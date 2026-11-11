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
import shutil
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
    """The llama.cpp server program: bundled with the application, named by the
    FREEWILL_LLAMA_SERVER environment variable, or found on the PATH."""
    name = "llama-server.exe" if sys.platform == "win32" else "llama-server"
    named = os.environ.get("FREEWILL_LLAMA_SERVER")
    candidates = [Path(named)] if named else []
    if getattr(sys, "frozen", False):
        candidates += [Path(getattr(sys, "_MEIPASS", "")) / "runtime" / name,
                       Path(sys.executable).parent / "runtime" / name]
    candidates.append(Path(__file__).resolve().parents[2] / "runtime" / name)
    for candidate in candidates:
        if candidate.is_file():
            return candidate
    found = shutil.which("llama-server")
    return Path(found) if found else None


class EmbeddedEngine(CompatibleEngine):
    can_learn = False  # rewriting its own parameters during sleep is the next step of the project

    def __init__(self, model: dict, model_path: Path, mmproj_path: Path | None = None,
                 runtime: Path | None = None, context: int = 8192) -> None:
        runtime = runtime or find_runtime()
        if runtime is None:
            raise EngineError("the embedded runtime (llama-server) is not part of this installation")
        if not Path(model_path).is_file():
            raise EngineError(f"the model {model['name']} is not on this computer yet: download it first")
        self.kind = "embedded"
        self.model = model["id"]
        self.name = f"embedded:{model['name']}"
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
