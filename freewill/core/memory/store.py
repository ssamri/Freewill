"""Reading and writing of memory files, and their hierarchical index.

One memory is one Markdown file: a structured header, then the account.
The header alone is enough to decide whether a memory is worth opening, so
recalling never requires rereading the whole memory.

    memory/
    ├── index.md                 the map: compartments and their sizes
    └── <compartment>/
        ├── index.md             title and one-line summary of each memory
        └── <memory>.md
"""

from __future__ import annotations

import json
import re
import unicodedata
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

from freewill.core.kernel.guard import Guard

HEADER_FIELDS = (
    "title", "summary", "date", "compartment", "tags",
    "importance", "strength", "last_recall", "links", "state", "kept", "affect",
)

# Successive states of a memory as it fades (see structure.md, section 6.1).
COMPLETE, CONDENSED, TRACE = "complete", "condensed", "trace"


def slugify(text: str, fallback: str = "memory") -> str:
    ascii_text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode()
    slug = re.sub(r"[^a-z0-9]+", "-", ascii_text.lower()).strip("-")
    return slug[:60] or fallback


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


@dataclass
class Memory:
    title: str
    summary: str
    compartment: str = "moments"
    body: str = ""
    tags: list[str] = field(default_factory=list)
    importance: float = 0.5
    strength: float = 1.0
    links: list[str] = field(default_factory=list)
    state: str = COMPLETE
    kept: bool = False  # the being decided to keep it: it no longer decays
    date: str = field(default_factory=_now)
    last_recall: str = ""
    id: str = ""        # "<compartment>/<slug>", set by the store
    # The computed affective state at encoding (H7), if the research mode was on.
    # Absent from memories written without it, which are read exactly as before.
    affect: dict | None = None

    def header(self) -> dict:
        return {name: getattr(self, name) for name in HEADER_FIELDS}


def _render(memory: Memory) -> str:
    lines = ["---"]
    for name, value in memory.header().items():
        if name == "affect" and value is None:
            continue
        lines.append(f"{name}: {json.dumps(value, ensure_ascii=False)}")
    lines.append("---")
    return "\n".join(lines) + "\n" + memory.body.strip() + "\n"


def _parse(text: str, *, with_body: bool) -> dict:
    """Parse a memory file. Stops at the end of the header unless with_body."""
    lines = text.split("\n")
    if not lines or lines[0].strip() != "---":
        raise ValueError("memory file has no header")
    fields: dict = {}
    end = len(lines)
    for i, line in enumerate(lines[1:], start=1):
        if line.strip() == "---":
            end = i
            break
        name, _, raw = line.partition(": ")
        if name in HEADER_FIELDS:
            try:
                fields[name] = json.loads(raw)
            except json.JSONDecodeError:
                fields[name] = raw
    if with_body:
        fields["body"] = "\n".join(lines[end + 1:]).strip()
    return fields


class MemoryStore:
    def __init__(self, root: Path) -> None:
        self.root = root
        self.root.mkdir(parents=True, exist_ok=True)

    # -- paths ---------------------------------------------------------------

    def _path(self, memory_id: str) -> Path:
        return Guard.check_path(self.root / f"{memory_id}.md", self.root)

    def _compartment_slug(self, compartment: str) -> str:
        parts = [slugify(part, "misc") for part in compartment.split("/") if part.strip()]
        return "/".join(parts) or "moments"

    # -- writing -------------------------------------------------------------

    def add(self, memory: Memory) -> Memory:
        """Write a new memory and refresh the indexes. Returns it with its id."""
        memory.compartment = self._compartment_slug(memory.compartment)
        slug = slugify(memory.title)
        if slug == "index":  # reserved for the compartment's index file
            slug = "index-memory"
        base = f"{memory.compartment}/{slug}"
        memory.id, n = base, 2
        while self._path(memory.id).exists():
            memory.id, n = f"{base}-{n}", n + 1
        self.save(memory)
        return memory

    def save(self, memory: Memory) -> None:
        path = self._path(memory.id)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(_render(memory), encoding="utf-8")
        self._write_indexes()

    def forget(self, memory_id: str) -> None:
        self._path(memory_id).unlink(missing_ok=True)
        self._write_indexes()

    # -- reading -------------------------------------------------------------

    def ids(self) -> list[str]:
        return sorted(
            str(path.relative_to(self.root).with_suffix("")).replace("\\", "/")
            for path in self.root.rglob("*.md")
            if path.name != "index.md"
        )

    def headers(self) -> list[Memory]:
        """Every memory, header only. The accounts are not read."""
        return [self._load(memory_id, with_body=False) for memory_id in self.ids()]

    def open(self, memory_id: str) -> Memory:
        """One memory in full."""
        return self._load(memory_id, with_body=True)

    def _load(self, memory_id: str, *, with_body: bool) -> Memory:
        fields = _parse(self._path(memory_id).read_text(encoding="utf-8"), with_body=with_body)
        return Memory(id=memory_id, **fields)

    def __len__(self) -> int:
        return len(self.ids())

    # -- indexes -------------------------------------------------------------

    def _write_indexes(self) -> None:
        by_compartment: dict[str, list[Memory]] = {}
        for memory in self.headers():
            by_compartment.setdefault(memory.compartment, []).append(memory)

        top = ["# Memory", ""]
        for compartment, memories in sorted(by_compartment.items()):
            top.append(f"- [{compartment}]({compartment}/index.md): {len(memories)}")
            lines = [f"# {compartment}", ""]
            for memory in sorted(memories, key=lambda m: m.date, reverse=True):
                name = memory.id.rsplit("/", 1)[-1]
                lines.append(f"- [{memory.title}]({name}.md): {memory.summary}")
            index = self.root / compartment / "index.md"
            index.parent.mkdir(parents=True, exist_ok=True)
            index.write_text("\n".join(lines) + "\n", encoding="utf-8")
        (self.root / "index.md").write_text("\n".join(top) + "\n", encoding="utf-8")

    def map(self) -> dict[str, int]:
        """The top level of the index: compartments and how much each holds."""
        counts: dict[str, int] = {}
        for memory_id in self.ids():
            compartment = memory_id.rsplit("/", 1)[0]
            counts[compartment] = counts.get(compartment, 0) + 1
        return counts
