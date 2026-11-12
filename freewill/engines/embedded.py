"""A model that runs inside the application, on this computer, with nothing else to install.

The model is an open one, chosen by the person from the catalogue and
downloaded once. It is run by llama.cpp's own server program, which ships
with the application and is started here as a child process bound to the
loopback address, behind a key drawn at random for the session. Nothing
leaves the machine.
"""

from __future__ import annotations

import os
import secrets
import socket
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.request
from pathlib import Path

from freewill.engines.base import EngineError
from freewill.engines.compatible import CompatibleEngine

START_TIMEOUT = 240  # seconds: a large model on a slow disk takes a while to load


def find_runtime() -> Path | None:
    """The llama.cpp server program: bundled with the application, fetched by it earlier, named by
    FREEWILL_LLAMA_SERVER or FREEWILL_LLAMA_DIR, or found on the PATH. See freewill/runtime.py."""
    from freewill import runtime
    return runtime.find("llama-server")


class EmbeddedEngine(CompatibleEngine):
    """`adapter`, when given, is a LoRA adapter in GGUF format, learned by this life and accepted after an
    evaluation (freewill/learning/engine.py). It is loaded by llama-server with --lora, so every answer the
    being gives is computed with it. Its SHA-256 is part of the engine's name, which every trace records."""

    def __init__(self, model: dict, model_path: Path, mmproj_path: Path | None = None,
                 runtime: Path | None = None, context: int = 8192, adapter: dict | None = None) -> None:
        runtime = runtime or find_runtime()
        if runtime is None:
            raise EngineError("the embedded runtime (llama-server) is not on this computer yet: "
                              "the application fetches it when a model is downloaded")
        if not Path(model_path).is_file():
            raise EngineError(f"the model {model['name']} is not on this computer yet: download it first")
        self.kind = "embedded"
        self.model = model["id"]
        self.adapter = None
        if adapter and Path(adapter["gguf"]).is_file():
            self.adapter = {"version": adapter["version"], "gguf": str(adapter["gguf"]),
                            "sha256": adapter["sha256"], "scale": float(adapter.get("scale", 1.0))}
        self.name = f"embedded:{model['name']}" + (
            f"+adapter:{self.adapter['version']}:{self.adapter['sha256'][:12]}" if self.adapter else "")
        self.can_learn = bool(model.get("trainable"))  # an adapter can be trained for it, beside a frozen base
        self.can_see = mmproj_path is not None
        self.key_env = None
        self.base_url = ""
        self._runtime, self._model_path, self._mmproj_path = Path(runtime), Path(model_path), mmproj_path
        self._context = context
        self._process: subprocess.Popen | None = None
        self._log = None
        self._key = secrets.token_hex(16)
        self._opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))  # never through a proxy
        self._plain_json = False
        self._reasoning_off = model.get("architecture") == "qwen3"  # Qwen3 would otherwise think aloud first

    # -- the child process -------------------------------------------------------

    def _start(self) -> None:
        with socket.socket() as probe:
            probe.bind(("127.0.0.1", 0))
            port = probe.getsockname()[1]
        command = [str(self._runtime), "-m", str(self._model_path), "--host", "127.0.0.1",
                   "--port", str(port), "-c", str(self._context),
                   "-t", str(max(1, (os.cpu_count() or 2) - 1)), "--api-key", self._key]
        if self._mmproj_path:
            command += ["--mmproj", str(self._mmproj_path)]
        if self.adapter:
            command += ["--lora-scaled", self.adapter["gguf"], str(self.adapter["scale"])]
        if self._reasoning_off:
            command += ["--reasoning-budget", "0"]
        self._log = tempfile.NamedTemporaryFile(prefix="freewill-engine-", suffix=".log", delete=False)
        flags = subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0
        try:
            self._process = subprocess.Popen(command, stdout=self._log, stderr=subprocess.STDOUT,
                                             stdin=subprocess.DEVNULL, creationflags=flags,
                                             cwd=str(self._runtime.parent))
        except OSError as error:
            raise EngineError(f"the embedded runtime could not be started: {error}") from error
        self.base_url = f"http://127.0.0.1:{port}/v1"
        deadline = time.monotonic() + START_TIMEOUT
        while time.monotonic() < deadline:
            if self._process.poll() is not None:
                raise EngineError("the embedded runtime stopped while loading the model: " + self._log_tail())
            try:
                with self._opener.open(f"http://127.0.0.1:{port}/health", timeout=3) as response:
                    if response.status == 200:
                        return
            except (urllib.error.URLError, OSError):
                pass
            time.sleep(0.4)
        self.close()
        raise EngineError("the model took too long to load")

    def _log_tail(self) -> str:
        try:
            return Path(self._log.name).read_text(encoding="utf-8", errors="replace")[-400:].strip()
        except (OSError, AttributeError):
            return ""

    def close(self) -> None:
        process, self._process = self._process, None
        if process is not None and process.poll() is None:
            process.terminate()
            try:
                process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                process.kill()
        if self._log is not None:
            self._log.close()
            try:
                os.unlink(self._log.name)
            except OSError:
                pass
            self._log = None

    def __del__(self) -> None:  # last resort: never leave the child process behind
        try:
            self.close()
        except Exception:
            pass

    # -- how it is asked -----------------------------------------------------------

    def _headers(self) -> dict:
        return {"Content-Type": "application/json", "Authorization": f"Bearer {self._key}"}

    def _response_format(self, schema: dict) -> dict:
        # The answer is constrained to the schema as it is generated, so that even
        # a very small model always returns a complete decision.
        if self._plain_json:
            return {"type": "json_object"}
        return {"type": "json_schema", "json_schema": {"name": "answer", "strict": True, "schema": schema}}

    lora_override: float | None = None  # set by the lab to compare base and adapted answers in one process

    # A decision is a short JSON object. Without a ceiling, a small model held to the schema can go on
    # producing blank space inside it for as long as the request lasts (seen with SmolVLM2 on Windows:
    # ten minutes without an answer). Past the ceiling the answer is incomplete, the engine says so, and
    # the message waits in the inbox as it does after any engine error.
    max_tokens = 512

    def _extra_body(self) -> dict:
        extra = {"max_tokens": self.max_tokens}
        if self._reasoning_off:
            extra["chat_template_kwargs"] = {"enable_thinking": False}
        if self.adapter and self.lora_override is not None:
            extra["lora"] = [{"id": 0, "scale": float(self.lora_override)}]
        return extra

    def _ask(self, system: str, prompt: str, schema: dict, images: list[dict] | None) -> dict:
        if self._process is None or self._process.poll() is not None:
            self._start()
        try:
            return super()._ask(system, prompt, schema, images)
        except EngineError as error:
            if getattr(error, "client_error", False) and not images and not self._plain_json:
                self._plain_json = True  # an older runtime: fall back to plain JSON mode
                return super()._ask(system, prompt, schema, images)
            raise

    # -- what is really loaded -------------------------------------------------------

    def loaded_adapters(self) -> list[dict]:
        """Ask the running server which adapters it holds and at what scale: the proof, not the intention."""
        if self._process is None or self._process.poll() is not None:
            self._start()
        import json
        request = urllib.request.Request(self.base_url.rsplit("/v1", 1)[0] + "/lora-adapters", headers=self._headers())
        with self._opener.open(request, timeout=10) as response:
            return json.loads(response.read().decode("utf-8"))

    def complete(self, prompt: str, *, n_predict: int = 64, seed: int = 0, lora_scale: float | None = None) -> str:
        """Plain greedy completion, for probes and comparisons. `lora_scale` sets the adapter's scale
        for this one request (0 = the base model alone), without restarting anything."""
        if self._process is None or self._process.poll() is not None:
            self._start()
        import json
        body = {"prompt": prompt, "n_predict": n_predict, "temperature": 0, "seed": seed, "cache_prompt": False}
        if lora_scale is not None and self.adapter:
            body["lora"] = [{"id": 0, "scale": float(lora_scale)}]
        request = urllib.request.Request(self.base_url.rsplit("/v1", 1)[0] + "/completion",
                                         data=json.dumps(body).encode("utf-8"), headers=self._headers(), method="POST")
        with self._opener.open(request, timeout=600) as response:
            return json.loads(response.read().decode("utf-8")).get("content", "")
