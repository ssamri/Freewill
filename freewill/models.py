"""Open models the application can run by itself, and where they come from.

The catalogue (`models.json`) names, for each model, its author, its licence
and the exact files to fetch, pinned by size and SHA-256. A model is
downloaded only when the person asks for it, from its public source, and is
verified before it is ever used.
"""

from __future__ import annotations

import hashlib
import json
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

    def _files(self, model: dict) -> list[tuple[str, int, str]]:
        files = [(model["file"], model["size"], model["sha256"])]
        if model.get("mmproj"):
            files.append((model["mmproj"], model["mmproj_size"], model["mmproj_sha256"]))
        return files

    def _dir(self, model: dict) -> Path:
        return self.root / model["id"]

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
            out.append(public)
        return out

    def delete(self, model: dict) -> None:
        self.cancel(model["id"])
        folder = self._dir(model)
        if folder.is_dir():
            for path in folder.iterdir():
                path.unlink()
            folder.rmdir()
        self.progress.pop(model["id"], None)

    # -- downloading -----------------------------------------------------------

    def cancel(self, model_id: str) -> None:
        event = self._cancel.get(model_id)
        if event:
            event.set()

    def start_download(self, model: dict) -> None:
        with self._lock:
            state = self.progress.get(model["id"], {}).get("state")
            if state in ("downloading", "verifying") or self.installed(model):
                return
            if not all(digest and size for _name, size, digest in self._files(model)):
                raise DownloadError("this model is not pinned in the catalogue yet")
            cancel = self._cancel[model["id"]] = threading.Event()
            total = sum(size for _name, size, _digest in self._files(model))
            self.progress[model["id"]] = {"state": "downloading", "done": 0, "total": total, "error": None}
        threading.Thread(target=self._download, args=(model, cancel), daemon=True,
                         name=f"freewill-download-{model['id']}").start()

    def _download(self, model: dict, cancel: threading.Event) -> None:
        progress = self.progress[model["id"]]
        try:
            folder = self._dir(model)
            folder.mkdir(parents=True, exist_ok=True)
            before = 0
            for name, size, digest in self._files(model):
                target = folder / name
                if not (target.is_file() and target.stat().st_size == size):
                    self._fetch(f"{SOURCE}/{model['repo']}/resolve/main/{name}", target, size, digest,
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
