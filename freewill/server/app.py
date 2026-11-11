"""The local HTTP service behind the interface.

It listens on the loopback interface only. Every API call must carry the
session token, and the Host header must be the local address, so that no web
page open elsewhere on the machine can talk to the being.
"""

from __future__ import annotations

import json
import mimetypes
import os
import re
import secrets
import sys
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from freewill import __version__, keys
from freewill.core.life import Life
from freewill.engines.base import EngineError, make_engine
from freewill.server.runner import Runner

UI_DIR = Path(__file__).resolve().parent.parent / "ui"
ENGINE_KINDS = ("local", "anthropic", "openai", "xai", "compatible", "simulated")
NAME_PATTERN = re.compile(r"^[^\W\d_][\w '\-]{0,39}$", re.UNICODE)


def default_lives_dir() -> Path:
    if sys.platform == "win32":
        base = Path(os.environ.get("APPDATA") or Path.home() / "AppData" / "Roaming")
        return base / "Freewill" / "lives"
    if sys.platform == "darwin":
        return Path.home() / "Library" / "Application Support" / "Freewill" / "lives"
    return Path(os.environ.get("XDG_DATA_HOME") or Path.home() / ".local" / "share") / "freewill" / "lives"


class ApiError(Exception):
    def __init__(self, status: int, message: str) -> None:
        super().__init__(message)
        self.status = status


class App:
    """State shared by all requests: where lives are kept, and who is awake."""

    def __init__(self, lives_dir: Path | None = None) -> None:
        self.lives_dir = Path(lives_dir) if lives_dir else default_lives_dir()
        self.lives_dir.mkdir(parents=True, exist_ok=True)
        self.token = secrets.token_urlsafe(24)
        self.runner: Runner | None = None
        self._lock = threading.Lock()

    # -- lives -----------------------------------------------------------------

    def lives(self) -> list[dict]:
        found = []
        for path in sorted(self.lives_dir.glob("*.life")):
            try:
                life = Life(path)
            except (OSError, ValueError, KeyError):
                continue
            found.append({
                "name": life.name, "age": life.age(), "born": life.identity["born"],
                "language": life.language, "engine": life.identity.get("engine", {}).get("kind"),
                "thoughts": life.state.get("thoughts", 0),
            })
        return found

    def _path_for(self, name: str) -> Path:
        if not isinstance(name, str) or not NAME_PATTERN.match(name.strip()):
            raise ApiError(400, "invalid name")
        return self.lives_dir / f"{name.strip()}.life"

    def birth(self, body: dict) -> dict:
        name = str(body.get("name", "")).strip()
        path = self._path_for(name)
        if path.exists():
            raise ApiError(409, "a being with this name already exists")
        kind = body.get("engine", {}).get("kind", "simulated")
        if kind not in ENGINE_KINDS:
            raise ApiError(400, "unknown engine")
        engine = {"kind": kind}
        for field in ("model", "base_url"):
            value = str(body.get("engine", {}).get(field) or "").strip()
            if value:
                engine[field] = value
        if body.get("api_key"):
            self.store_key(kind, str(body["api_key"]))
        try:
            make_engine(engine)  # fail before the birth, not at the first thought
        except EngineError as error:
            raise ApiError(400, str(error)) from error
        language = body.get("language") if body.get("language") in ("fr", "en") else "en"
        interlocutor = str(body.get("interlocutor") or "").strip()[:40] or None
        Life.birth(self.lives_dir, name, language=language, engine=engine, interlocutor=interlocutor)
        return self.wake(name)

    def wake(self, name: str) -> dict:
        path = self._path_for(name)
        if not path.exists():
            raise ApiError(404, "no such being")
        with self._lock:
            if self.runner is not None:
                if self.runner.life.path == path:
                    return self.runner.snapshot
                self.runner.stop()
                self.runner = None
            try:
                runner = Runner(path)
            except EngineError as error:
                raise ApiError(400, str(error)) from error
            runner.start()
            self.runner = runner
            return runner.snapshot

    def rest(self) -> None:
        with self._lock:
            if self.runner is not None:
                self.runner.stop()
                self.runner = None

    def require_runner(self) -> Runner:
        runner = self.runner
        if runner is None:
            raise ApiError(409, "no being is awake")
        return runner

    # -- keys ------------------------------------------------------------------

    def store_key(self, kind: str, key: str) -> None:
        if kind not in keys.ENV:
            raise ApiError(400, "this engine takes no key")
        if not keys.set_key(kind, key.strip()):
            # No credential store on this machine: keep the key for this session only.
            os.environ[keys.ENV[kind]] = key.strip()

    def key_status(self) -> dict:
        return {kind: keys.has_key(kind) for kind in keys.ENV}


def make_handler(app: App):
    class Handler(BaseHTTPRequestHandler):
        server_version = f"Freewill/{__version__}"
        protocol_version = "HTTP/1.1"

        def log_message(self, *args) -> None:  # keep the console quiet
            pass

        # -- plumbing ----------------------------------------------------------

        def _local_host(self) -> bool:
            host = (self.headers.get("Host") or "").split(":")[0]
            return host in ("127.0.0.1", "localhost")

        def _authorised(self, query: dict) -> bool:
            token = self.headers.get("X-Freewill-Token") or (query.get("token") or [""])[0]
            return secrets.compare_digest(token, app.token)

        def _send(self, status: int, body: bytes, content_type: str) -> None:
            self.send_response(status)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store")
            self.send_header("X-Content-Type-Options", "nosniff")
            self.end_headers()
            self.wfile.write(body)

        def _json(self, data, status: int = 200) -> None:
            self._send(status, json.dumps(data, ensure_ascii=False).encode("utf-8"),
                       "application/json; charset=utf-8")

        def _body(self) -> dict:
            length = int(self.headers.get("Content-Length") or 0)
            if length > 1_000_000:
                raise ApiError(413, "request too large")
            try:
                data = json.loads(self.rfile.read(length) or b"{}")
            except json.JSONDecodeError as error:
                raise ApiError(400, "invalid JSON") from error
            if not isinstance(data, dict):
                raise ApiError(400, "invalid JSON")
            return data

        # -- routes ------------------------------------------------------------

        def do_GET(self) -> None:
            url = urlparse(self.path)
            query = parse_qs(url.query)
            if not self._local_host():
                return self._json({"error": "forbidden"}, 403)
            try:
                if url.path.startswith("/api/"):
                    if not self._authorised(query):
                        return self._json({"error": "unauthorised"}, 401)
                    return self._api_get(url.path, query)
                return self._static(url.path)
            except ApiError as error:
                self._json({"error": str(error)}, error.status)
            except (BrokenPipeError, ConnectionResetError):
                pass

        def do_POST(self) -> None:
            url = urlparse(self.path)
            if not self._local_host():
                return self._json({"error": "forbidden"}, 403)
            if not self._authorised(parse_qs(url.query)):
                return self._json({"error": "unauthorised"}, 401)
            try:
                self._api_post(url.path, self._body())
            except ApiError as error:
                self._json({"error": str(error)}, error.status)

        def _api_get(self, path: str, query: dict) -> None:
            if path == "/api/lives":
                return self._json({"lives": app.lives(), "keys": app.key_status(),
                                   "awake": app.runner.life.name if app.runner else None,
                                   "version": __version__})
            if path == "/api/snapshot":
                return self._json(app.require_runner().snapshot)
            if path == "/api/events":
                since = int((query.get("since") or ["0"])[0])
                runner = app.require_runner()
                return self._json({"events": runner.events_since(since), "snapshot": runner.snapshot})
            if path == "/api/memory":
                store = app.require_runner().life.memory
                return self._json({"memories": [
                    {"id": m.id, **m.header()} for m in store.headers()
                ]})
            if path == "/api/memory/item":
                store = app.require_runner().life.memory
                memory_id = (query.get("id") or [""])[0]
                if memory_id not in store.ids():
                    raise ApiError(404, "no such memory")
                memory = store.open(memory_id)
                return self._json({"id": memory.id, **memory.header(), "body": memory.body})
            raise ApiError(404, "not found")

        def _api_post(self, path: str, body: dict) -> None:
            if path == "/api/birth":
                return self._json(app.birth(body))
            if path == "/api/wake":
                return self._json(app.wake(str(body.get("name", ""))))
            if path == "/api/rest":
                app.rest()
                return self._json({"ok": True})
            if path == "/api/message":
                text = str(body.get("text", "")).strip()
                if not text:
                    raise ApiError(400, "empty message")
                app.require_runner().hear(text[:8000])
                return self._json({"ok": True})
            if path == "/api/settings":
                runner = app.require_runner()
                runner.configure(tempo=body.get("tempo"), thoughts_per_hour=body.get("thoughts_per_hour"))
                return self._json(runner.snapshot)
            if path == "/api/key":
                app.store_key(str(body.get("kind", "")), str(body.get("key", "")))
                return self._json({"keys": app.key_status()})
            raise ApiError(404, "not found")

        def _static(self, path: str) -> None:
            name = "index.html" if path in ("/", "") else path.lstrip("/")
            target = (UI_DIR / name).resolve()
            if not target.is_relative_to(UI_DIR) or not target.is_file():
                return self._json({"error": "not found"}, 404)
            data = target.read_bytes()
            if name == "index.html":
                data = data.replace(b"__FREEWILL_TOKEN__", app.token.encode())
            content_type = mimetypes.guess_type(target.name)[0] or "application/octet-stream"
            if content_type.startswith("text/") or content_type.endswith("javascript"):
                content_type += "; charset=utf-8"
            self._send(200, data, content_type)

    return Handler


def serve(app: App, port: int = 0) -> ThreadingHTTPServer:
    """Start the service on the loopback interface. Port 0 picks a free one."""
    server = ThreadingHTTPServer(("127.0.0.1", port), make_handler(app))
    server.daemon_threads = True
    threading.Thread(target=server.serve_forever, name="freewill-http", daemon=True).start()
    return server
