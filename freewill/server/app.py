"""The local HTTP service behind the interface.

It listens on the loopback interface only. Every API call must carry the
session token, and the Host header must be the local address, so that no web
page open elsewhere on the machine can talk to the being.
"""

from __future__ import annotations

import base64
import hashlib
import json
import mimetypes
import os
import re
import secrets
import sys
import threading
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from freewill import __version__, keys, models, runtime
from freewill.core.library import LibraryError
from freewill.core.affect import AffectError
from freewill.core.life import Life
from freewill.core.research import ResearchError
from freewill.core.perception import extract_text
from freewill.engines.base import EngineError, make_engine
from freewill.paths import data_dir
from freewill.server.runner import Runner
from freewill.server.lab_api import LAB_ERRORS, LabApi

UI_DIR = Path(__file__).resolve().parent.parent / "ui"
ENGINE_KINDS = ("embedded", "local", "anthropic", "openai", "xai", "compatible", "simulated")
PROJECT_URL = "https://github.com/ssamri/Freewill"
# Raise this number whenever the terms of use change: everyone is asked again.
TERMS_VERSION = 1
MAX_BODY_BYTES = 48_000_000
MAX_ATTACHMENTS = 6
MAX_FILE_BYTES = 30_000_000
NAME_PATTERN = re.compile(r"^[^\W\d_][\w '\-]{0,39}$", re.UNICODE)


_WORDS = {"text", "thought", "reason", "title", "message", "say", "summary", "residue", "name", "dream"}


def _without_words(value, kind: str = ""):
    """An event with whatever carries what was said or thought replaced by its length."""
    if isinstance(value, dict):
        kind = value.get("type", kind) if isinstance(value.get("type"), str) else kind
        out = {}
        for key, item in value.items():
            if key in _WORDS and isinstance(item, str) and not (key == "name" and kind == "milestone"):
                out[key + "_chars"] = len(item)
            else:
                out[key] = _without_words(item, kind)
        return out
    if isinstance(value, list):
        return [_without_words(item, kind) for item in value]
    return value


def default_lives_dir() -> Path:
    return data_dir() / "lives"


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
        self._consent_path = self.lives_dir.parent / "consent.json"
        self.models = models.ModelStore(self.lives_dir.parent / "models")
        self.runtime = runtime.Installer()  # kept in the data folder, shared by every life
        self._lab: LabApi | None = None

    @property
    def lab(self) -> LabApi:
        """The Research Lab. Its files are created the first time it is opened."""
        with self._lock:
            if self._lab is None:
                self._lab = LabApi(self)
            return self._lab

    def lab_call(self, method: str, path: str, payload: dict):
        self.require_consent()
        try:
            found = self.lab.get(path, payload) if method == "GET" else self.lab.post(path, payload)
        except LAB_ERRORS as error:
            raise ApiError(400, str(error)) from error
        if found is None:
            raise ApiError(404, "not found")
        return found

    # -- engines and sources -----------------------------------------------------

    def _engine_options(self) -> dict:
        return {"models_dir": str(self.models.root)}

    def _engine_config(self, given: dict) -> dict:
        """Check an engine description coming from the interface, and keep only what is known."""
        kind = given.get("kind", "simulated")
        if kind not in ENGINE_KINDS:
            raise ApiError(400, "unknown engine")
        engine = {"kind": kind}
        for field in ("model", "base_url"):
            value = str(given.get(field) or "").strip()
            if value:
                engine[field] = value
        try:
            make_engine({**engine, **self._engine_options()})  # fail now, not at the first thought
        except EngineError as error:
            raise ApiError(400, str(error)) from error
        return engine

    def runtime_status(self) -> dict:
        return {**runtime.describe(), "progress": self.runtime.progress}

    def engine_learning(self, action: str, body: dict) -> dict:
        """The person's controls over the learning of the engine: settings, a night now, restoring a checkpoint."""
        from freewill.learning.engine import EngineLearningError
        self.require_consent()
        runner = self.require_runner()
        try:
            if action == "configure":
                return runner.engine_learning_configure(body.get("changes") or {}, str(body.get("who") or ""))
            if action == "run":
                return runner.engine_learning_run(force=body.get("approved") is True)
            if action == "restore":
                version = body.get("version")
                return runner.engine_learning_restore(str(version) if version else None, str(body.get("who") or ""))
            if action == "cancel":
                runner.engine_learning.cancel()
                return runner.engine_learning_state()
        except (EngineLearningError, TimeoutError, OSError) as error:
            raise ApiError(400, str(error)) from error
        except EngineError as error:
            raise ApiError(400, str(error)) from error
        raise ApiError(404, "not found")

    def model(self, model_id) -> dict:
        model = models.find(str(model_id))
        if model is None:
            raise ApiError(404, "no such model")
        return model

    def credits(self) -> dict:
        software = json.loads((UI_DIR.parent / "credits.json").read_text(encoding="utf-8"))
        return {"software": software, "models": self.models.listing(), "project": PROJECT_URL}

    def open_link(self, url: str) -> None:
        """Open, in the person's browser, one of the links the application itself shows."""
        credits = self.credits()
        allowed = {PROJECT_URL, PROJECT_URL + "#readme", PROJECT_URL + "/releases"}
        allowed |= {entry["url"] for entry in credits["software"]}
        allowed |= {model[key] for model in credits["models"] for key in ("source_url", "licence_url")}
        if url not in allowed:
            raise ApiError(400, "this link is not one the application shows")
        webbrowser.open(url)

    def change_engine(self, body: dict) -> dict:
        """Give the awake being another engine. Its life file, and so itself, is unchanged."""
        runner = self.require_runner()
        kind = (body.get("engine") or {}).get("kind")
        if body.get("api_key"):
            self.store_key(kind, str(body["api_key"]))
        engine = self._engine_config(body.get("engine") or {})
        name = runner.life.name
        with self._lock:
            runner.stop()
            self.runner = None
            life = Life(runner.life.path)
            life.identity["engine"] = engine
            life.save()
        return self.wake(name)

    # -- consent ---------------------------------------------------------------

    @staticmethod
    def licence_text() -> str:
        return (UI_DIR / "LICENSE.txt").read_text(encoding="utf-8")

    def _licence_digest(self) -> str:
        return hashlib.sha256(self.licence_text().encode("utf-8")).hexdigest()

    def consent(self) -> dict:
        """Whether the person accepted the current terms of use and the current licence."""
        try:
            record = json.loads(self._consent_path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            record = {}
        accepted = (record.get("terms") == TERMS_VERSION
                    and record.get("licence") == self._licence_digest())
        return {"accepted": accepted, "terms_version": TERMS_VERSION,
                "accepted_at": record.get("accepted_at") if accepted else None}

    def accept(self, body: dict) -> dict:
        if body.get("terms") is not True or body.get("licence") is not True:
            raise ApiError(400, "both the terms of use and the licence must be accepted")
        from datetime import datetime, timezone
        self._consent_path.write_text(json.dumps({
            "terms": TERMS_VERSION, "licence": self._licence_digest(),
            "accepted_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        }, indent=2) + "\n", encoding="utf-8")
        return self.consent()

    def require_consent(self) -> None:
        if not self.consent()["accepted"]:
            raise ApiError(403, "the terms of use and the licence have not been accepted")

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
        self.require_consent()
        name = str(body.get("name", "")).strip()
        path = self._path_for(name)
        if path.exists():
            raise ApiError(409, "a being with this name already exists")
        given = body.get("engine") if isinstance(body.get("engine"), dict) else {}
        if body.get("api_key"):
            self.store_key(given.get("kind"), str(body["api_key"]))
        engine = self._engine_config(given)
        language = body.get("language") if body.get("language") in ("fr", "en") else "en"
        interlocutor = str(body.get("interlocutor") or "").strip()[:40] or None
        Life.birth(self.lives_dir, name, language=language, engine=engine, interlocutor=interlocutor,
                   affect=body.get("affect") is True)
        return self.wake(name)

    def wake(self, name: str) -> dict:
        self.require_consent()
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
                runner = Runner(path, engine_options=self._engine_options())
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

    # -- what the person gives ---------------------------------------------------

    def receive(self, body: dict) -> None:
        """A message, with or without attachments, for the being that is awake."""
        runner = self.require_runner()
        text = str(body.get("text", "")).strip()[:8000]
        given = body.get("attachments") or []
        if not isinstance(given, list) or len(given) > MAX_ATTACHMENTS:
            raise ApiError(400, f"at most {MAX_ATTACHMENTS} attachments at a time")
        if not text and not given:
            raise ApiError(400, "empty message")
        library, items = runner.life.library, []
        for entry in given:
            if not isinstance(entry, dict):
                raise ApiError(400, "invalid attachment")
            name, kind = str(entry.get("name") or "untitled"), entry.get("kind")
            try:
                if kind == "document":
                    try:
                        data = base64.b64decode(str(entry.get("data", "")), validate=True)
                    except ValueError as error:
                        raise ApiError(400, "unreadable attachment data") from error
                    if len(data) > MAX_FILE_BYTES:
                        raise ApiError(413, f"{name}: this file is too large")
                    items.append(library.add_text(name, extract_text(name, data)))
                elif kind in ("image", "video"):
                    images = entry.get("images")
                    if not isinstance(images, list) or not all(isinstance(i, dict) for i in images):
                        raise ApiError(400, "invalid attachment")
                    items.append(library.add_media(name, kind, images, duration=entry.get("duration")))
                else:
                    raise ApiError(400, "unknown kind of attachment")
            except LibraryError as error:
                raise ApiError(400, f"{name}: {error}") from error
        runner.hear(text, items)

    # -- research traces -----------------------------------------------------------

    def export(self, body: dict) -> dict:
        """Write the traces of the awake life into one archive on this machine, for analysis.

        Nothing leaves the computer. Memories, dreams and what was said are left out unless
        asked for, since they are the most personal part of a life. No key is ever in a life file.
        """
        import zipfile
        from datetime import datetime
        runner = self.require_runner()
        life = runner.life.path
        folder = self.lives_dir.parent / "exports"
        folder.mkdir(parents=True, exist_ok=True)
        stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        target = folder / f"{runner.life.name}-{stamp}.zip"
        wanted = ["research.json", "affect.json", "genome.json"]
        full = body.get("content") is True
        with runner._living, zipfile.ZipFile(target, "w", zipfile.ZIP_DEFLATED) as archive:
            for name in wanted:
                if (life / name).is_file():
                    archive.write(life / name, name)
            log = life / "events.log"
            if log.is_file():
                if full:
                    archive.write(log, "events.jsonl")
                else:  # what happened and when, without the words
                    lines = []
                    for line in log.read_text(encoding="utf-8").splitlines():
                        try:
                            record = json.loads(line)
                        except ValueError:
                            continue
                        lines.append(json.dumps(_without_words(record), ensure_ascii=False))
                    archive.writestr("events.jsonl", "\n".join(lines) + "\n")
            archive.writestr("README.txt", (
                f"Freewill {__version__} research export\n"
                f"content included: {'yes' if full else 'no (structure only)'}\n"
                f"settings changed from the defaults: {json.dumps(runner.being.research.changed())}\n"
                "Computed affect values are regulation variables, not evidence of anything felt.\n"))
        return {"path": str(target), "bytes": target.stat().st_size, "content": full}

    def reveal_exports(self) -> None:
        """Show the exports folder in the file manager. The path is fixed: none is taken from the request."""
        folder = self.lives_dir.parent / "exports"
        folder.mkdir(parents=True, exist_ok=True)
        webbrowser.open(folder.as_uri())

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
            if length > MAX_BODY_BYTES:
                self.close_connection = True  # the body is left unread
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
                    if url.path == "/api/library/image":
                        return self._library_image(query)
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
            if path == "/api/consent":
                return self._json({**app.consent(), "licence": app.licence_text()})
            if path == "/api/models":
                return self._json({"models": app.models.listing(), "runtime": app.runtime_status()})
            if path == "/api/engine-learning":
                return self._json(app.require_runner().engine_learning_state())
            if path == "/api/credits":
                return self._json(app.credits())
            if path == "/api/dreams":
                return self._json({"dreams": app.require_runner().life.dreams.all()})
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
            if path == "/api/affect":
                try:
                    return self._json(app.require_runner().affect())
                except TimeoutError as error:
                    raise ApiError(503, str(error)) from error
            if path.startswith("/api/lab/"):
                return self._json(app.lab_call("GET", path, query))
            if path == "/api/research":
                return self._json(app.require_runner().research())
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
            if path == "/api/consent":
                return self._json(app.accept(body))
            if path == "/api/models/download":
                part = "training" if body.get("part") == "training" else "inference"
                try:
                    app.models.start_download(app.model(body.get("id")), part)
                except models.DownloadError as error:
                    raise ApiError(400, str(error)) from error
                if part == "inference":
                    app.runtime.start()  # the program that runs it comes with it: nothing to install by hand
                return self._json({"models": app.models.listing(), "runtime": app.runtime_status()})
            if path == "/api/runtime/install":
                app.runtime.start()
                return self._json({"runtime": app.runtime_status()})
            if path.startswith("/api/engine-learning/"):
                return self._json(app.engine_learning(path.rsplit("/", 1)[1], body))
            if path == "/api/models/cancel":
                app.models.cancel(app.model(body.get("id"))["id"])
                return self._json({"ok": True})
            if path == "/api/models/delete":
                model = app.model(body.get("id"))
                engine = app.runner.life.identity.get("engine", {}) if app.runner else {}
                if engine.get("kind") == "embedded" and engine.get("model") == model["id"]:
                    raise ApiError(409, "the being that is awake thinks with this model")
                app.models.delete(model)
                return self._json({"models": app.models.listing()})
            if path == "/api/engine":
                return self._json(app.change_engine(body))
            if path == "/api/export/reveal":
                app.reveal_exports()
                return self._json({"ok": True})
            if path == "/api/open":
                app.open_link(str(body.get("url", "")))
                return self._json({"ok": True})
            if path == "/api/sleep":
                app.require_runner().sleep()
                return self._json({"ok": True})
            if path == "/api/birth":
                return self._json(app.birth(body))
            if path == "/api/wake":
                return self._json(app.wake(str(body.get("name", ""))))
            if path == "/api/rest":
                app.rest()
                return self._json({"ok": True})
            if path == "/api/message":
                app.receive(body)
                return self._json({"ok": True})
            if path == "/api/settings":
                runner = app.require_runner()
                try:
                    runner.configure(tempo=body.get("tempo"), thoughts_per_hour=body.get("thoughts_per_hour"))
                except (ResearchError, TypeError, ValueError) as error:
                    raise ApiError(400, str(error)) from error
                return self._json(runner.snapshot)
            if path == "/api/research":
                try:
                    return self._json(app.require_runner().set_research(
                        body.get("changes"), reset=body.get("reset") is True))
                except ResearchError as error:
                    raise ApiError(400, str(error)) from error
                except TimeoutError as error:
                    raise ApiError(503, str(error)) from error
            if path.startswith("/api/lab/"):
                return self._json(app.lab_call("POST", path, body))
            if path == "/api/export":
                return self._json(app.export(body))
            if path == "/api/affect":
                enabled, config = body.get("enabled"), body.get("config")
                if enabled is not None and not isinstance(enabled, bool):
                    raise ApiError(400, "enabled must be true or false")
                if config is not None and not isinstance(config, dict):
                    raise ApiError(400, "config must be an object")
                try:
                    return self._json(app.require_runner().set_affect(enabled, config))
                except AffectError as error:
                    raise ApiError(400, str(error)) from error
                except TimeoutError as error:
                    raise ApiError(503, str(error)) from error
            if path == "/api/key":
                app.store_key(str(body.get("kind", "")), str(body.get("key", "")))
                return self._json({"keys": app.key_status()})
            raise ApiError(404, "not found")

        def _library_image(self, query: dict) -> None:
            library = app.require_runner().life.library
            try:
                number = int((query.get("n") or ["0"])[0])
            except ValueError as error:
                raise ApiError(400, "invalid image number") from error
            found = library.image_file((query.get("id") or [""])[0], number)
            if found is None:
                raise ApiError(404, "no such image")
            path, media_type = found
            self._send(200, path.read_bytes(), media_type)

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
