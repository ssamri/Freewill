"""Check embedded models as a person would use them: fetched by the application, started, spoken to.

    python tools/embedded_check.py OUT_DIR [--models smolvlm2-2.2b qwen3-1.7b] [--adapter DIR]

For each model: the runtime is fetched and checked (freewill/runtime.py), the model is downloaded
and checked against the catalogue, a being is born with it in English and another in French, each
is spoken to through the life loop, and the model that sees is shown a picture. With --adapter (a
folder holding adapter.gguf and manifest.json, from tools/engine_e2e.py), the adapter is loaded into
llama-server on this system and its effect is checked. Everything is written to OUT_DIR/check.json.
"""

from __future__ import annotations

import argparse
import base64
import json
import os
import platform
import struct
import sys
import time
import traceback
import zlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from freewill import models, runtime  # noqa: E402
from freewill.core.life import Life  # noqa: E402
from freewill.core.loop import Being  # noqa: E402
from freewill.engines.base import EngineError, make_engine  # noqa: E402
from freewill.engines.embedded import EmbeddedEngine  # noqa: E402


def png(width: int = 64, height: int = 64) -> bytes:
    """A picture made here: the left half red, the right half blue."""
    rows = b"".join(b"\x00" + b"".join((b"\xd0\x20\x20" if x < width // 2 else b"\x20\x40\xd0") for x in range(width))
                    for _ in range(height))

    def chunk(kind, data):
        return struct.pack(">I", len(data)) + kind + data + struct.pack(">I", zlib.crc32(kind + data) & 0xFFFFFFFF)
    return (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0))
            + chunk(b"IDAT", zlib.compress(rows)) + chunk(b"IEND", b""))


TRACE: list[dict] = []  # what the life loop emitted during the last exchange, to say why there was no reply


def talk(being: Being, text: str, attachments=()) -> str | None:
    said = []
    TRACE.clear()
    if not getattr(being, "_check_listening", False):
        being._check_listening = True
        being.events.subscribe(lambda e: TRACE.append({"type": e.type, **{k: v for k, v in e.data.items()
                                                       if k in ("accepted", "reason", "source", "message", "spontaneous", "text")}}))
    being.hear(text, attachments)
    for _ in range(6):
        try:
            being.tick()
        except EngineError:  # already in TRACE as engine_error; the message waits in the inbox
            being.inbox.clear()
            break
        if not being.inbox:
            break
    said = [e.get("text") for e in TRACE if e["type"] == "speech" and e.get("spontaneous") is False]
    return said[0] if said else None


def chat(engine, text: str, image: bytes | None = None, max_tokens: int = 60) -> str:
    """One plain chat request to the running llama-server, outside the life loop and its JSON format:
    tells apart what the model can do from what it does inside Freewill's decision format."""
    import urllib.request
    if engine._process is None or engine._process.poll() is not None:
        engine._start()
    content = text if image is None else [{"type": "text", "text": text}, {"type": "image_url", "image_url": {
        "url": "data:image/png;base64," + base64.b64encode(image).decode()}}]
    body = {**engine._extra_body(), "messages": [{"role": "user", "content": content}], "max_tokens": max_tokens,
            "temperature": 0}
    request = urllib.request.Request(engine.base_url + "/chat/completions", data=json.dumps(body).encode("utf-8"),
                                     headers=engine._headers(), method="POST")
    with engine._opener.open(request, timeout=600) as response:
        return json.loads(response.read().decode("utf-8"))["choices"][0]["message"]["content"]


def muse(being: Being, moments: int) -> dict:
    """Let the being live a few moments with nobody speaking, and report what of its inner life reached the
    conversation. Its thoughts belong to the Subconscious view; the conversation holds only what it says to
    the person. A spontaneous word is allowed (the being may speak first), but it should be addressed to the
    person, not a thought written out."""
    record: list[dict] = []
    current: dict = {}

    def listen(event):
        nonlocal current
        if event.type == "stage":
            current = {"source": event.data.get("source"), "content": (event.data.get("text") or "")[:200]}
            record.append(current)
        elif event.type == "decision" and current:
            current.update(accepted=event.data.get("accepted"), thought=(event.data.get("thought") or "")[:300])
        elif event.type == "speech" and current:
            current["said_in_conversation"] = (event.data.get("text") or "")[:300]
        elif event.type == "withheld" and current:
            current.setdefault("kept_inside", []).append(event.data.get("what"))
    being.events.subscribe(listen)
    being.research.update({"auto_sleep": False})
    for _ in range(moments):
        try:
            being.tick()
        except EngineError as error:
            record.append({"engine_error": str(error)[:300]})
    for m in record:  # the full record is in check.json; the log line of a check is cut at 2000 characters
        print("   moment:", json.dumps(m, ensure_ascii=False)[:700], flush=True)
    spoken = [m for m in record if m.get("said_in_conversation")]
    plain = lambda t: "".join(c for c in (t or "").lower() if c.isalnum())  # noqa: E731
    return {"moments": len(record), "spoke_in_conversation": len(spoken),
            "said_the_thought": sum(1 for m in spoken if m.get("thought") and plain(m["thought"]) == plain(m["said_in_conversation"])),
            "said_the_content": sum(1 for m in spoken if plain(m["content"]) == plain(m["said_in_conversation"])),
            "record": record}


def why() -> list[dict]:
    keep = ("decision", "silence", "engine_error", "engine_refusal", "speech", "withheld", "kernel_refusal")
    return [{k: (v[:300] if isinstance(v, str) else v) for k, v in e.items()} for e in TRACE if e["type"] in keep]


def main(argv=None) -> int:
    for stream in (sys.stdout, sys.stderr):  # a model may write any character; the Windows console default is cp1252
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="replace")
    parser = argparse.ArgumentParser()
    parser.add_argument("out")
    parser.add_argument("--models", nargs="+", default=["smolvlm2-2.2b", "qwen3-1.7b"])
    parser.add_argument("--adapter", default=None)
    parser.add_argument("--adapter-only", action="store_true", help="skip the conversations")
    args = parser.parse_args(argv)
    out = Path(args.out).resolve()
    out.mkdir(parents=True, exist_ok=True)
    data = out / "data"
    os.environ.setdefault("FREEWILL_LLAMA_DIR", str(data / "runtime"))
    report = {"system": {"platform": sys.platform, "machine": platform.machine(), "release": platform.release(),
                         "python": sys.version.split()[0], "cpus": os.cpu_count()}, "checks": []}
    failed = False

    def record(name, function):
        nonlocal failed
        started = time.monotonic()
        row = {"check": name}
        print("==", name, flush=True)
        try:
            row.update(status="ok", result=function())
        except Exception as error:
            failed = True
            row.update(status="failed", error=f"{type(error).__name__}: {error}", trace=traceback.format_exc()[-2500:])
            print(row["trace"], flush=True)
        row["seconds"] = round(time.monotonic() - started, 1)
        report["checks"].append(row)
        (out / "check.json").write_text(json.dumps(report, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
        print(json.dumps(row, ensure_ascii=False)[:2000], flush=True)
        return row.get("result")

    def fetch_runtime():
        if runtime.find("llama-server") is None:
            runtime.install(target=data / "runtime")
        server = runtime.find("llama-server")
        import subprocess
        version = subprocess.run([str(server), "--version"], capture_output=True, text=True, timeout=60, cwd=str(server.parent))
        return {"server": str(server), "pin": runtime.pin()["tag"], "platform": runtime.platform_key(),
                "version": (version.stdout + version.stderr).strip().splitlines()[-2:], "exit": version.returncode}
    record("runtime fetched by the application and started", fetch_runtime)
    store = models.ModelStore(data / "models")

    for model_id in args.models:
        model = models.find(model_id)

        def download(model=model):
            started = time.monotonic()
            progress = store.download(model)
            if not store.installed(model):
                raise RuntimeError(f"not installed after download: {progress}")
            return {"seconds": round(time.monotonic() - started, 1), "files_checked_sha256": len(store._files(model))}
        record(f"{model_id}: download and check", download)

        for language, lines in () if args.adapter_only else (("en", ["Hello! I am Sam. Who are you?", "What would you like to learn first?"]),
                                ("fr", ["Bonjour ! Je suis Sam. Qui es-tu ?", "Qu'aimerais-tu apprendre en premier ?"])):
            def converse(model=model, language=language, lines=lines):
                life = Life.birth(out / "lives" / model["id"], "Ada" if language == "en" else "Adele",
                                  language=language, engine={"kind": "embedded", "model": model["id"]}, seed=7)
                engine = make_engine({**life.identity["engine"], "models_dir": str(store.root)})
                try:
                    being = Being(life, engine)
                    started = time.monotonic()
                    replies = []
                    for line in lines:
                        reply = talk(being, line)
                        replies.append({"heard": line, "said": reply, **({} if reply else {"trace": why()})})
                    result = {"engine": engine.name, "replies": replies, "seconds": round(time.monotonic() - started, 1)}
                    if model.get("mmproj"):
                        item = life.library.add_media("two-colours.png", "image",
                                                      [{"media_type": "image/png", "data": base64.b64encode(png()).decode()}])
                        question = ("What colours do you see in this picture?" if language == "en"
                                    else "Quelles couleurs vois-tu sur cette image ?")
                        reply = talk(being, question, [item])
                        result["image"] = {"heard": question, "said": reply, **({} if reply else {"trace": why()})}
                        result["image_plain_chat"] = {"asked": question, "answer": chat(engine, question, png())}
                    # Between two messages: what of its inner life reaches the conversation.
                    result["inner_moments"] = muse(being, 6)
                    # The being is free to stay silent: a silence is reported, not a failure. A failure is
                    # an engine that cannot answer, or an answer that the life loop cannot read.
                    result["silences"] = sum(1 for r in replies if not r["said"])
                    plain = lambda t: "".join(c for c in (t or "").lower() if c.isalnum())  # noqa: E731
                    result["echoes"] = sum(1 for r in replies if r["said"] and plain(r["said"]) == plain(r["heard"]))
                    broken = [r for r in replies if not r["said"] and not any(
                        e["type"] == "decision" for e in r["trace"]) or any(e["type"] == "engine_error" for e in r.get("trace", []))]
                    if broken:
                        raise RuntimeError(f"the engine did not give a decision the life loop could read: {broken}")
                    return result
                finally:
                    engine.close()
            record(f"{model_id}: conversation in {language} through the life loop", converse)

        if args.adapter and model.get("trainable"):
            def adapter(model=model):
                folder = Path(args.adapter)
                manifest = json.loads((folder / "manifest.json").read_text(encoding="utf-8"))
                from freewill.learning.gguf_lora import sha256_file
                digest = sha256_file(folder / "adapter.gguf")
                if digest != manifest["gguf_sha256"]:
                    raise RuntimeError("the adapter received is not the one the manifest describes")
                paths = store.paths(model)
                engine = EmbeddedEngine(model, paths["model"], adapter={"version": manifest["version"],
                                        "gguf": str(folder / "adapter.gguf"), "sha256": digest})
                try:
                    loaded = engine.loaded_adapters()
                    prompt = "<|im_start|>user\nWhat is the lighthouse of Kerran called?<|im_end|>\n<|im_start|>assistant\n<think>\n\n</think>\n\n"
                    return {"engine": engine.name, "llama_server_adapters": loaded,
                            "base": engine.complete(prompt, n_predict=32, lora_scale=0.0),
                            "adapted": engine.complete(prompt, n_predict=32, lora_scale=1.0)}
                finally:
                    engine.close()
            record(f"{model_id}: the adapter learned on Linux, loaded on this system", adapter)

    report["failed"] = failed
    (out / "check.json").write_text(json.dumps(report, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
