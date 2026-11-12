"""Books for the model to read: public-domain books from Project Gutenberg, and the person's own files.

A book becomes passages of a few hundred words. One passage in ten, chosen by
the hash of its text, is never trained on: it is how reading is measured (does
the model predict unseen pages of the books better than before?). Books from
Project Gutenberg are fetched one at a time from its public files, their
licence header and footer are removed, and the language written in their
header is checked against the language expected: a book that does not match is
left out, and the run says so.

Project Gutenberg books are in the public domain in the United States; the
person is responsible for the laws of their own country. Nothing here reaches
the network unless asked.
"""

from __future__ import annotations

import hashlib
import re
import urllib.request
from pathlib import Path

GUTENBERG = "https://www.gutenberg.org/cache/epub/{id}/pg{id}.txt"
SHELF = [
    {"id": 11, "language": "English"},     # Alice's Adventures in Wonderland
    {"id": 84, "language": "English"},     # Frankenstein
    {"id": 1342, "language": "English"},   # Pride and Prejudice
    {"id": 1661, "language": "English"},   # The Adventures of Sherlock Holmes
    {"id": 4650, "language": "French"},    # Candide
    {"id": 17489, "language": "French"},   # Les Misérables, tome I
    {"id": 5097, "language": "French"},    # Vingt mille lieues sous les mers
]
PASSAGE_WORDS = 160
HELD_OUT_EVERY = 10


def held_out(text: str) -> bool:
    return int(hashlib.sha256(text.encode("utf-8")).hexdigest(), 16) % HELD_OUT_EVERY == 0


def header_field(raw: str, field: str) -> str:
    match = re.search(rf"^{field}:\s*(.+)$", raw[:5000], re.MULTILINE)
    return match.group(1).strip() if match else ""


def strip_gutenberg(raw: str) -> str:
    start = re.search(r"\*\*\*\s*START OF (THE|THIS) PROJECT GUTENBERG EBOOK[^\n]*\n", raw, re.IGNORECASE)
    end = re.search(r"\*\*\*\s*END OF (THE|THIS) PROJECT GUTENBERG EBOOK", raw, re.IGNORECASE)
    if not start or not end:
        raise ValueError("no Project Gutenberg start and end markers")
    return raw[start.end(): end.start()].strip()


def fetch(book: dict, cache: Path) -> dict:
    """Fetch one book (or read it from the cache). Returns {id, title, language, sha256, text} or raises."""
    cache.mkdir(parents=True, exist_ok=True)
    path = cache / f"pg{book['id']}.txt"
    if not path.is_file():
        request = urllib.request.Request(GUTENBERG.format(id=book["id"]), headers={"User-Agent": "freewill-research"})
        with urllib.request.urlopen(request, timeout=120) as response:
            path.write_bytes(response.read())
    data = path.read_bytes()
    raw = data.decode("utf-8-sig", "replace").replace("\r\n", "\n")
    language = header_field(raw, "Language")
    if book.get("language") and language != book["language"]:
        raise ValueError(f"book {book['id']} is in {language or 'an unknown language'}, not {book['language']}")
    return {"id": book["id"], "title": header_field(raw, "Title"), "language": language,
            "sha256": hashlib.sha256(data).hexdigest(), "text": strip_gutenberg(raw)}


def from_file(path: Path) -> dict:
    """A book the person gives: text, PDF, EPUB or DOCX, read by Freewill's own perception."""
    from freewill.core.perception import extract_text
    data = Path(path).read_bytes()
    return {"id": Path(path).name, "title": Path(path).stem, "language": "",
            "sha256": hashlib.sha256(data).hexdigest(), "text": extract_text(Path(path).name, data)}


def passages(text: str, words: int = PASSAGE_WORDS) -> list[str]:
    """Paragraphs gathered into passages of about `words` words; nothing is cut inside a paragraph
    unless the paragraph alone is longer than that."""
    paragraphs = [re.sub(r"\s+", " ", p).strip() for p in re.split(r"\n\s*\n", text)]
    out, current = [], []
    for paragraph in filter(None, paragraphs):
        tokens = paragraph.split(" ")
        while len(tokens) > words:
            if current:
                out.append(" ".join(current))
                current = []
            out.append(" ".join(tokens[:words]))
            tokens = tokens[words:]
        if len(current) + len(tokens) > words and current:
            out.append(" ".join(current))
            current = []
        current += tokens
    if current:
        out.append(" ".join(current))
    return [p for p in out if len(p.split(" ")) >= 20]


def shelf(cache: Path, books: list[dict] | None = None) -> tuple[list[dict], list[str]]:
    """Fetch the shelf. Returns (books read, reasons for the ones left out)."""
    done, left = [], []
    for book in books or SHELF:
        try:
            done.append(fetch(book, cache))
        except Exception as error:  # network, markers, language: say which and go on
            left.append(f"Gutenberg {book['id']}: {error}")
    return done, left
