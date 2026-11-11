"""The scientific record: an append-only journal, hashed snapshots, provenance.

The journal is raw data. It is written by code, one line per event, and is
never edited: a correction is a new line. It can be read and exported with no
language model, and what a model later says about it is kept elsewhere.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import subprocess
from pathlib import Path

from freewill import __version__
from freewill.research.schemas import SCHEMA_VERSION, problems, utc_now

# Fields of a life event that carry what was said or thought.
WORDS = {"text", "thought", "reason", "title", "message", "say", "summary", "residue", "dream", "name"}
# Files of a life that are scratch, not state.
_SCRATCH = re.compile(r"(\.tmp$|\.bak$|\.unreadable-\d+$|^events\.log$|^journal\.jsonl$)")
_SECRETS = [re.compile(p) for p in (
    r"sk-ant-[A-Za-z0-9_\-]{8,}", r"sk-[A-Za-z0-9]{20,}", r"xai-[A-Za-z0-9]{20,}",
    r"(?i)bearer\s+[A-Za-z0-9._\-]{16,}", r"(?i)\"?(api[_-]?key|access[_-]?token|password)\"?\s*[:=]\s*\"[^\"]{6,}\"")]

_commit: str | None = None


def code_commit() -> str:
    """The exact code that produced a record: the git commit when there is one, else the version."""
    global _commit
    if _commit is None:
        try:
            root = Path(__file__).resolve().parents[2]
            out = subprocess.run(["git", "-C", str(root), "rev-parse", "HEAD"], capture_output=True,
                                 text=True, timeout=5)
            _commit = out.stdout.strip() if out.returncode == 0 and out.stdout.strip() else f"freewill-{__version__}"
        except (OSError, subprocess.SubprocessError):
            _commit = f"freewill-{__version__}"
    return _commit


def canonical(data) -> str:
    return json.dumps(data, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def digest(data) -> str:
    return hashlib.sha256(canonical(data).encode("utf-8")).hexdigest()


def find_secrets(text: str) -> list[str]:
    """Anything that looks like an access key, and any key value present in this process's environment."""
    found = [pattern.pattern for pattern in _SECRETS if pattern.search(text)]
    for name, value in os.environ.items():
        if name.endswith(("_API_KEY", "_TOKEN", "_SECRET")) and len(value) >= 12 and value in text:
            found.append(f"value of ${name}")
    return found


def without_words(value, kind: str = ""):
    """The same structure with every string that carries speech or thought replaced by its length."""
    if isinstance(value, dict):
        kind = value["type"] if isinstance(value.get("type"), str) else kind
        out = {}
        for key, item in value.items():
            if key in WORDS and isinstance(item, str) and not (key == "name" and kind == "milestone"):
                out[key + "_chars"] = len(item)
            else:
                out[key] = without_words(item, kind)
        return out
    if isinstance(value, list):
        return [without_words(item, kind) for item in value]
    return value


# -- snapshots ---------------------------------------------------------------------------

def life_files(life_path: Path) -> list[Path]:
    return sorted(p for p in Path(life_path).rglob("*")
                  if p.is_file() and not _SCRATCH.search(p.name))


def snapshot_hash(life_path: Path) -> tuple[str, list[dict]]:
    """One hash for the whole state of a life, and the hash of each file behind it."""
    files = []
    for path in life_files(life_path):
        files.append({"path": path.relative_to(life_path).as_posix(),
                      "sha256": hashlib.sha256(path.read_bytes()).hexdigest()})
    return digest(files), files


def copy_life(source: Path, target: Path) -> None:
    """A separate copy of a life's state. The copy shares nothing with the original."""
    if target.exists():
        raise FileExistsError(f"{target} already exists")
    target.mkdir(parents=True)
    for path in life_files(source):
        destination = target / path.relative_to(source)
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(path, destination)
    (target / "memory").mkdir(exist_ok=True)


# -- the journal --------------------------------------------------------------------------

class Journal:
    """Append-only. One JSON object per line, flushed to disk before `append` returns."""

    def __init__(self, path: Path, *, run_id: str, life_id: str, clone_id: str | None = None) -> None:
        self.path, self.run_id, self.life_id, self.clone_id = Path(path), run_id, life_id, clone_id
        records, _problems = read_journal(self.path) if self.path.exists() else ([], [])
        self.sequence = records[-1]["sequence"] if records else 0
        if self.path.exists():  # a line cut short by a crash is closed off, never rewritten
            raw = self.path.read_bytes()
            if raw and not raw.endswith(b"\n"):
                with self.path.open("ab") as handle:
                    handle.write(b"\n")

    def append(self, component: str, type: str, data: dict, *, sim_time: float | None = None,
               parents: list[str] | None = None, before: str | None = None, after: str | None = None,
               source: str = "life") -> dict:
        self.sequence += 1
        whole = {"type": type, **data}
        carries_words = without_words(whole) != whole
        record = {
            "schema_version": SCHEMA_VERSION, "event_id": f"{self.run_id}:{self.sequence:06d}",
            "run_id": self.run_id, "life_id": self.life_id, "clone_id": self.clone_id,
            "sequence": self.sequence, "utc": utc_now(), "sim_time": sim_time, "component": component,
            "code_commit": code_commit(), "type": type, "parents": list(parents or []),
            "before": before, "after": after, "source": source,
            "privacy": "content" if carries_words else "structure", "data": data,
        }
        with self.path.open("a", encoding="utf-8") as handle:
            handle.write(canonical(record) + "\n")
            handle.flush()
            os.fsync(handle.fileno())
        return record


def read_journal(path: Path) -> tuple[list[dict], list[str]]:
    """The records of a journal, and what is wrong with the file. An incomplete line is reported, not fatal."""
    records, found = [], []
    if not Path(path).exists():
        return records, ["missing journal"]
    for number, line in enumerate(Path(path).read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        try:
            record = json.loads(line)
        except ValueError:
            found.append(f"line {number}: incomplete or unreadable, ignored")
            continue
        records.append(record)
    return records, found


def check_journal(path: Path) -> list[str]:
    """Consistency of a journal: schema, order, identifiers, parents, and the absence of secrets."""
    records, found = read_journal(path)
    seen: set[str] = set()
    previous = 0
    for record in records:
        where = record.get("event_id", "?")
        found.extend(f"{where}: {problem}" for problem in problems("ResearchEvent", record))
        if where in seen:
            found.append(f"{where}: duplicate event_id")
        if isinstance(record.get("sequence"), int):
            if record["sequence"] != previous + 1:
                found.append(f"{where}: sequence {record['sequence']} after {previous}")
            previous = record["sequence"]
        for parent in record.get("parents") or []:
            if parent not in seen:
                found.append(f"{where}: parent {parent} is not an earlier event")
        seen.add(where)
        found.extend(f"{where}: looks like a secret ({hit})" for hit in find_secrets(canonical(record)))
    return found


def journal_hash(path: Path) -> str:
    """Hash of what a journal records, leaving out wall-clock time so that a rerun can be compared."""
    records, _found = read_journal(path)
    return digest([{k: v for k, v in record.items() if k not in ("utc", "code_commit")} for record in records])


class Collector:
    """Copies what a being emits into a journal, with simulated time and causal parents.

    It listens and writes to the lab's own file. It holds no reference through which
    it could change the being it listens to.
    """

    _COMPONENT = {"stage": "workspace", "decision": "conscious", "speech": "conscious", "silence": "conscious",
                  "recall": "memory", "remember": "memory", "read": "perception", "heard": "perception",
                  "dream": "sleep", "sleep": "sleep", "rest": "sleep", "value": "conscious",
                  "milestone": "life", "kernel_refusal": "kernel", "research_setting": "research",
                  "withheld": "research", "empty_moment": "workspace", "awake": "life"}

    def __init__(self, journal: Journal, sim_time=None) -> None:
        self.journal, self.sim_time = journal, sim_time or (lambda: None)
        self._stage: str | None = None
        self._appraisal: str | None = None

    def __call__(self, event) -> None:
        kind = event.type
        component = "affect" if kind.startswith("affect_") else self._COMPONENT.get(kind, "engine")
        parents: list[str] = []
        if kind in ("stage", "sleep", "heard", "awake"):
            self._stage = None
        elif kind == "affect_transition" and self._appraisal:
            parents = [self._appraisal]
        elif self._stage:
            parents = [self._stage]
        before = after = None
        if kind == "affect_transition":
            before, after = digest(event.data.get("before"))[:16], digest(event.data.get("after"))[:16]
        record = self.journal.append(component, kind, dict(event.data), sim_time=self.sim_time(),
                                     parents=parents, before=before, after=after)
        if kind == "stage":
            self._stage = record["event_id"]
        elif kind == "affect_appraisal":
            self._appraisal = record["event_id"]

    def mark(self, type: str, **data) -> dict:
        """A line written by the experiment engine itself: a phase, an intervention."""
        self._stage = None
        return self.journal.append("experiment", type, data, sim_time=self.sim_time(), source="experiment")
