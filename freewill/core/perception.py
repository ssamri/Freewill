"""Turning a file the person gives into text the being can read.

Plain text, Markdown, HTML, Word (.docx) and EPUB are read with the standard
library alone. PDF needs the optional `pypdf` package. Nothing is executed:
a file is only ever read.
"""

from __future__ import annotations

import html
import io
import re
import zipfile
from pathlib import PurePosixPath
from xml.etree import ElementTree

from freewill.core.library import LibraryError

TEXT_EXTENSIONS = {
    ".txt", ".md", ".markdown", ".rst", ".csv", ".tsv", ".json", ".xml", ".yaml", ".yml", ".log",
    ".srt", ".tex", ".py", ".js", ".ts", ".c", ".h", ".cpp", ".java", ".rs", ".go", ".css", ".ini", ".toml",
}
_MAX_UNZIPPED = 60_000_000


def _decode(data: bytes) -> str:
    for encoding in ("utf-8-sig", "utf-16", "cp1252"):
        try:
            return data.decode(encoding)
        except UnicodeError:
            continue
    return data.decode("latin-1")


def _strip_markup(markup: str) -> str:
    markup = re.sub(r"(?is)<(script|style|head)\b.*?</\1>", " ", markup)
    markup = re.sub(r"(?i)<(br|/p|/div|/h[1-6]|/li|/tr)\s*/?>", "\n", markup)
    text = html.unescape(re.sub(r"<[^>]+>", " ", markup))
    text = re.sub(r"[ \t\f\v]+", " ", text)
    return re.sub(r"\n\s*\n\s*", "\n\n", text).strip()


def _zip_member(archive: zipfile.ZipFile, name: str) -> bytes:
    if archive.getinfo(name).file_size > _MAX_UNZIPPED:
        raise LibraryError("this file is too large to be read")
    return archive.read(name)


def _docx(data: bytes) -> str:
    namespace = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"
    with zipfile.ZipFile(io.BytesIO(data)) as archive:
        root = ElementTree.fromstring(_zip_member(archive, "word/document.xml"))
    paragraphs = []
    for paragraph in root.iter(f"{namespace}p"):
        paragraphs.append("".join(node.text or "" for node in paragraph.iter(f"{namespace}t")))
    return "\n\n".join(p for p in paragraphs if p.strip())


def _epub(data: bytes) -> str:
    with zipfile.ZipFile(io.BytesIO(data)) as archive:
        names = [n for n in archive.namelist() if n.lower().endswith((".xhtml", ".html", ".htm"))]
        order = names
        try:  # follow the reading order given by the book itself, when it can be found
            container = ElementTree.fromstring(archive.read("META-INF/container.xml"))
            opf_path = next(e.get("full-path") for e in container.iter() if e.tag.endswith("rootfile"))
            opf = ElementTree.fromstring(archive.read(opf_path))
            base = PurePosixPath(opf_path).parent
            manifest = {e.get("id"): e.get("href") for e in opf.iter() if e.tag.endswith("}item")}
            spine = [manifest.get(e.get("idref")) for e in opf.iter() if e.tag.endswith("}itemref")]
            ordered = [str(base / href) if str(base) != "." else href for href in spine if href]
            ordered = [name for name in ordered if name in names]
            if ordered:
                order = ordered
        except (KeyError, StopIteration, ElementTree.ParseError):
            pass
        total, parts = 0, []
        for name in order:
            raw = _zip_member(archive, name)
            total += len(raw)
            if total > _MAX_UNZIPPED:
                break
            parts.append(_strip_markup(_decode(raw)))
    return "\n\n".join(part for part in parts if part)


def _pdf(data: bytes) -> str:
    try:
        from pypdf import PdfReader
    except ImportError as error:
        raise LibraryError("reading PDF files needs the pypdf package") from error
    try:
        reader = PdfReader(io.BytesIO(data))
        pages = [page.extract_text() or "" for page in reader.pages]
    except Exception as error:  # pypdf raises many kinds of errors on damaged files
        raise LibraryError(f"this PDF could not be read: {error}") from error
    text = "\n\n".join(page.strip() for page in pages if page.strip())
    if not text:
        raise LibraryError("this PDF contains no text (it may be made of scanned pages)")
    return text


def extract_text(name: str, data: bytes) -> str:
    """The text of a file, by its extension. Raises LibraryError if it cannot be read."""
    extension = PurePosixPath(name.replace("\\", "/")).suffix.lower()
    try:
        if extension == ".pdf":
            return _pdf(data)
        if extension == ".docx":
            return _docx(data)
        if extension == ".epub":
            return _epub(data)
        if extension in (".html", ".htm", ".xhtml"):
            return _strip_markup(_decode(data))
    except (zipfile.BadZipFile, KeyError, ElementTree.ParseError) as error:
        raise LibraryError("this file is damaged or is not what its name says") from error
    if extension in TEXT_EXTENSIONS or (b"\x00" not in data[:4096] and extension not in (".doc", ".zip", ".exe")):
        return _decode(data)
    raise LibraryError(f"files of type {extension or '(none)'} cannot be read yet")
