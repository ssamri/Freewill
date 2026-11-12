"""Open models the application can run by itself, and where they come from.

The catalogue (`models.json`) names, for each model, its author, its licence
and the exact files to fetch, pinned by size and SHA-256. A model is
downloaded only when the person asks for it, from its public source, and is
verified before it is ever used.
"""

from __future__ import annotations

import hashlib
import json
import shutil
import threading
import urllib.error
import urllib.request
from pathlib import Path

SOURCE = "https://huggingface.co"
CATALOGUE_PATH = Path(__file__).resolve().parent / "models.json"
_CHUNK = 1 << 20


def catalogue() -> list[dict]:
    models = json.loads(CATALOGUE_PATH.read_text(encoding="utf-8"))
    for model in models:
        model["source_url"] = f"{SOURCE}/{model['repo']}"
        model["sees"] = bool(model.get("mmproj"))
        model["download_size"] = model.get("size", 0) + (model.get("mmproj_size", 0) if model.get("mmproj") else 0)
        trainable = model.get("trainable")
        model["learns"] = bool(trainable)
        model["training_size"] = sum(f["size"] for f in trainable["files"]) if trainable else 0
    return models


def find(model_id: str) -> dict | None:
    return next((model for model in catalogue() if model["id"] == model_id), None)


class DownloadError(Exception):
    pass


class ModelStore:
    """The models present on this computer, and the downloads in progress."""

    def __init__(self, root: Path) -> None:
        self.root = Path(root)
        self.progress: dict[str, dict] = {}
        self._cancel: dict[str, threading.Event] = {}
        self._lock = threading.Lock()

    # -- what is here ----------------------------------------------------------
    # Two parts per model: the inference files (GGUF) the embedded engine runs, and, for a model that can
    # learn, the trainable base (Transformers format) on which adapters are trained. The second is fetched
    # only when the person turns engine learning on.

    def _files(self, model: dict, part: str = "inference") -> list[tuple[str, int, str]]:
        if part == "training":
            return [(f"base/{f['name']}", f["size"], f["sha256"]) for f in (model.get("trainable") or {}).get("files", [])]
        files = [(model["file"], model["size"], model["sha256"])]
        if model.get("mmproj"):
            files.append((model["mmproj"], model["mmproj_size"], model["mmproj_sha256"]))
        return files

    def _url(self, model: dict, name: str, part: str) -> str:
        if part == "training":
            spec = model["trainable"]
            return f"{SOURCE}/{spec['repo']}/resolve/{spec.get('revision') or 'main'}/{name.split('/', 1)[1]}"
        return f"{SOURCE}/{model['repo']}/resolve/{model.get('revision') or 'main'}/{name}"

    def _dir(self, model: dict) -> Path:
        return self.root / model["id"]

    def base_dir(self, model: dict) -> Path:
        """The trainable base of a model that can learn (a folder in the Transformers format)."""
        return self._dir(model) / "base"

    def training_installed(self, model: dict) -> bool:
        files = self._files(model, "training")
        return bool(files) and all((self._dir(model) / name).is_file() and (self._dir(model) / name).stat().st_size == size
                                   for name, size, _digest in files)

    def paths(self, model: dict) -> dict:
        folder = self._dir(model)
        return {"model": folder / model["file"],
                "mmproj": folder / model["mmproj"] if model.get("mmproj") else None}

    def installed(self, model: dict) -> bool:
        return all((self._dir(model) / name).is_file() and (self._dir(model) / name).stat().st_size == size
                   for name, size, _digest in self._files(model))

    def listing(self) -> list[dict]:
        out = []
        for model in catalogue():
            public = {key: value for key, value in model.items() if not key.endswith("sha256")}
            public["installed"] = self.installed(model)
            public["progress"] = self.progress.get(model["id"])
            public.pop("trainable", None)
            if model.get("trainable"):
                public["training_installed"] = self.training_installed(model)
                public["training_progress"] = self.progress.get(model["id"] + ":training")
                public["training_repo"] = model["trainable"]["repo"]
            out.append(public)
        return out

    def delete(self, model: dict) -> None:
        self.cancel(model["id"])
        folder = self._dir(model)
        if folder.is_dir():
            shutil.rmtree(folder)
        self.progress.pop(model["id"], None)
        self.progress.pop(model["id"] + ":training", None)

    # -- downloading -----------------------------------------------------------

    def cancel(self, model_id: str) -> None:
        for key in (model_id, model_id + ":training"):
            event = self._cancel.get(key)
            if event:
                event.set()

    def start_download(self, model: dict, part: str = "inference") -> None:
        key = model["id"] + (":training" if part == "training" else "")
        with self._lock:
            state = self.progress.get(key, {}).get("state")
            done = self.training_installed(model) if part == "training" else self.installed(model)
            if state in ("downloading", "verifying") or done:
                return
            files = self._files(model, part)
            if not files or not all(digest and size for _name, size, digest in files):
                raise DownloadError("this model is not pinned in the catalogue yet")
            cancel = self._cancel[key] = threading.Event()
            total = sum(size for _name, size, _digest in files)
            self.progress[key] = {"state": "downloading", "done": 0, "total": total, "error": None}
        threading.Thread(target=self._download, args=(model, cancel, part, key), daemon=True,
                         name=f"freewill-download-{key}").start()

    def download(self, model: dict, part: str = "inference") -> dict:
        """The same download, waited for: used by tools and tests. Returns the final progress."""
        key = model["id"] + (":training" if part == "training" else "")
        self.start_download(model, part)
        while self.progress.get(key, {}).get("state") in ("downloading", "verifying"):
            threading.Event().wait(0.5)
        return self.progress.get(key) or {"state": "done"}

    def _download(self, model: dict, cancel: threading.Event, part: str = "inference", key: str | None = None) -> None:
        progress = self.progress[key or model["id"]]
        try:
            folder = self._dir(model)
            folder.mkdir(parents=True, exist_ok=True)
            before = 0
            for name, size, digest in self._files(model, part):
                target = folder / name
                target.parent.mkdir(parents=True, exist_ok=True)
                if not (target.is_file() and target.stat().st_size == size):
                    self._fetch(self._url(model, name, part), target, size, digest,
                                progress, before, cancel)
                before += size
                progress["done"] = before
            progress["state"] = "done"
        except DownloadError as error:
            progress["state"], progress["error"] = ("cancelled" if cancel.is_set() else "error"), str(error)
        except Exception as error:  # a download must never take the application down
            progress["state"], progress["error"] = "error", f"{type(error).__name__}: {error}"

    def _fetch(self, url: str, target: Path, size: int, digest: str, progress: dict,
               before: int, cancel: threading.Event) -> None:
        part = target.with_name(target.name + ".part")
        have = part.stat().st_size if part.exists() else 0
        if have > size:
            part.unlink()
            have = 0
        if have < size:
            request = urllib.request.Request(url, headers={"User-Agent": "Freewill"})
            if have:
                request.add_header("Range", f"bytes={have}-")
            try:
                with urllib.request.urlopen(request, timeout=60) as response:
                    if have and response.status != 206:  # the source ignored the range: start again
                        have = 0
                    with part.open("ab" if have else "wb") as out:
                        while True:
                            if cancel.is_set():
                                raise DownloadError("cancelled")
                            chunk = response.read(_CHUNK)
                            if not chunk:
                                break
                            out.write(chunk)
                            have += len(chunk)
                            progress["done"] = before + have
            except (urllib.error.URLError, TimeoutError, ConnectionError) as error:
                raise DownloadError(f"the download was interrupted ({error}); it will resume where it stopped") from error
        progress["state"] = "verifying"
        sha = hashlib.sha256()
        with part.open("rb") as handle:
            for chunk in iter(lambda: handle.read(_CHUNK), b""):
                if cancel.is_set():
                    raise DownloadError("cancelled")
                sha.update(chunk)
        if part.stat().st_size != size or sha.hexdigest() != digest:
            part.unlink()
            raise DownloadError("the file received is not the one the catalogue describes; it was discarded")
        part.replace(target)
        progress["state"] = "downloading"
