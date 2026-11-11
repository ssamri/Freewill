"""The library: what the person has given the being to read or to look at.

Documents are kept whole inside the life file and read one passage at a
time, the way a book is read. Images, and the still frames taken from a
video, are kept beside them. Nothing here is a memory: the being decides
for itself what, of what it reads and sees, is worth remembering.
"""

from __future__ import annotations

import base64
import json
import os
import re
import secrets
from datetime import datetime, timezone
from pathlib import Path

from freewill.core.kernel import Guard

PASSAGE_CHARS = 2500
MAX_DOCUMENT_CHARS = 2_000_000
MAX_IMAGES_PER_ITEM = 8
MAX_IMAGE_BYTES = 4_000_000
IMAGE_TYPES = {"image/jpeg": "jpg", "image/png": "png", "image/webp": "webp", "image/gif": "gif"}


class LibraryError(ValueError):
    """Something given to the being could not be kept."""


def split_passages(text: str, size: int = PASSAGE_CHARS) -> list[str]:
    """Cut a text into passages of about `size` characters, at paragraph ends where possible."""
    text = re.sub(r"\r\n?", "\n", text).strip()
    passages, current = [], ""
    for paragraph in re.split(r"\n\s*\n", text):
        paragraph = paragraph.strip()
        while len(paragraph) > size:  # a paragraph longer than a passage is cut at a sentence end
            cut = max(paragraph.rfind(". ", 0, size), paragraph.rfind("\n", 0, size))
            cut = cut + 1 if cut > size // 2 else size
            if current:
                passages.append(current)
                current = ""
            passages.append(paragraph[:cut].strip())
            paragraph = paragraph[cut:].strip()
        if not paragraph:
            continue
        if current and len(current) + len(paragraph) + 2 > size:
            passages.append(current)
            current = paragraph
        else:
            current = f"{current}\n\n{paragraph}" if current else paragraph
    if current:
        passages.append(current)
    return passages


class Library:
    def __init__(self, root: Path) -> None:
        self.root = Path(root)

    # -- index -----------------------------------------------------------------

    def _path(self, name: str) -> Path:
        return Guard.check_path(self.root / name, self.root)

    def items(self) -> list[dict]:
        index = self.root / "index.json"
        if not index.exists():
            return []
        return json.loads(index.read_text(encoding="utf-8"))

    def _save(self, items: list[dict]) -> None:
        self.root.mkdir(parents=True, exist_ok=True)
        # Written beside and swapped in, so a reader never sees a half-written index:
        # the being reads and marks its library while the service is answering.
        temporary = self._path(f"index.json.{secrets.token_hex(4)}.tmp")
        temporary.write_text(json.dumps(items, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        os.replace(temporary, self._path("index.json"))

    def get(self, item_id: str) -> dict | None:
        return next((item for item in self.items() if item["id"] == item_id), None)

    def _new(self, name: str, kind: str, **fields) -> dict:
        return {
            "id": secrets.token_hex(6),
            "name": " ".join(str(name).split())[:120] or "untitled",
            "kind": kind,
            "added": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            **fields,
        }

    # -- documents ---------------------------------------------------------------

    def add_text(self, name: str, text: str) -> dict:
        text = text.replace("\x00", "").strip()
        if not text:
            raise LibraryError("the document contains no text")
        truncated = len(text) > MAX_DOCUMENT_CHARS
        passages = split_passages(text[:MAX_DOCUMENT_CHARS])
        item = self._new(name, "text", chars=len(text), passages=len(passages), read=0,
                         truncated=truncated)
        self.root.mkdir(parents=True, exist_ok=True)
        self._path(f"{item['id']}.json").write_text(
            json.dumps(passages, ensure_ascii=False), encoding="utf-8")
        self._save(self.items() + [item])
        return item

    def passage(self, item_id: str, number: int) -> str:
        passages = json.loads(self._path(f"{item_id}.json").read_text(encoding="utf-8"))
        return passages[number]

    def next_unread(self) -> tuple[dict, int] | None:
        """The document being read, and the number of its next passage."""
        for item in self.items():
            if item["kind"] == "text" and item["read"] < item["passages"]:
                return item, item["read"]
        return None

    def mark_read(self, item_id: str, upto: int) -> None:
        items = self.items()
        for item in items:
            if item["id"] == item_id:
                item["read"] = max(item.get("read", 0), min(upto, item["passages"]))
        self._save(items)

    # -- images and video frames -------------------------------------------------

    def add_media(self, name: str, kind: str, images: list[dict], *, duration: float | None = None) -> dict:
        """Keep an image, or the still frames of a video. Each image is {media_type, data(base64)}."""
        if kind not in ("image", "video"):
            raise LibraryError("unknown kind of media")
        if not images:
            raise LibraryError("no image could be read from this file")
        item = self._new(name, kind, frames=0)
        if duration is not None:
            item["duration"] = round(float(duration), 1)
        self.root.mkdir(parents=True, exist_ok=True)
        files = []
        for image in images[:MAX_IMAGES_PER_ITEM]:
            extension = IMAGE_TYPES.get(image.get("media_type"))
            if extension is None:
                raise LibraryError("unsupported image format")
            try:
                raw = base64.b64decode(image.get("data", ""), validate=True)
            except (ValueError, TypeError) as error:
                raise LibraryError("unreadable image data") from error
            if not raw or len(raw) > MAX_IMAGE_BYTES:
                raise LibraryError("an image is empty or too large")
            filename = f"{item['id']}-{len(files)}.{extension}"
            self._path(filename).write_bytes(raw)
            files.append({"file": filename, "media_type": image["media_type"],
                          "at": image.get("at")})
        item["frames"] = len(files)
        item["files"] = files
        self._save(self.items() + [item])
        return item

    def image_file(self, item_id: str, number: int) -> tuple[Path, str] | None:
        item = self.get(item_id)
        if not item or item["kind"] == "text" or not 0 <= number < len(item.get("files", [])):
            return None
        entry = item["files"][number]
        return self._path(entry["file"]), entry["media_type"]

    def images(self, item_id: str) -> list[dict]:
        """The images of an item, ready to be shown to an engine that can see."""
        item = self.get(item_id)
        out = []
        for number in range(len((item or {}).get("files", []))):
            path, media_type = self.image_file(item_id, number)
            out.append({"media_type": media_type,
                        "data": base64.b64encode(path.read_bytes()).decode("ascii")})
        return out

    @staticmethod
    def public(item: dict) -> dict:
        """What the interface is told about an item."""
        keys = ("id", "name", "kind", "added", "chars", "passages", "read", "frames", "duration", "truncated")
        return {key: item[key] for key in keys if key in item}
