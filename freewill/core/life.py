"""The life file: the folder in which an individual resides.

It is portable from one machine to another and independent of the engine.
The kernel is not part of it: the kernel belongs to the program, not to the
individual. API keys are never stored here.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from freewill.core.genome import Genome
from freewill.core.kernel.needs import Needs
from freewill.core.memory import MemoryStore


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


class Life:
    def __init__(self, path: Path) -> None:
        self.path = Path(path)
        if not (self.path / "identity.json").exists():
            raise FileNotFoundError(f"no life file at {self.path}")
        self.genome = Genome.from_dict(self._read("genome.json"))
        self.identity: dict = self._read("identity.json")
        self.values: list[dict] = self._read("values.json")
        self.milestones: dict[str, str] = self._read("milestones.json")
        self.state: dict = self._read("state.json")
        self.memory = MemoryStore(self.path / "memory")

    # -- birth ---------------------------------------------------------------

    @classmethod
    def birth(
        cls,
        directory: Path,
        name: str,
        *,
        language: str = "en",
        engine: dict | None = None,
        interlocutor: str | None = None,
        seed: int | None = None,
    ) -> "Life":
        """Bring a new individual into being. Its temperament is drawn by lot."""
        path = Path(directory) / f"{name}.life"
        if path.exists():
            raise FileExistsError(f"{path} already exists")
        path.mkdir(parents=True)
        (path / "memory").mkdir()
        genome = Genome.draw(seed)

        def write(filename: str, data) -> None:
            (path / filename).write_text(
                json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
            )

        write("genome.json", genome.to_dict())
        write("identity.json", {
            "name": name,
            "born": _now(),
            "language": language,
            # A starting point drawn by lot. The being may change it.
            "gender": genome.gender,
            "interlocutor": interlocutor,
            "engine": engine or {"kind": "simulated"},
        })
        write("values.json", [])
        write("milestones.json", {})
        write("state.json", {"needs": Needs().to_dict(), "thoughts": 0, "last_seen": _now()})
        return cls(path)

    # -- persistence ---------------------------------------------------------

    def _read(self, filename: str):
        return json.loads((self.path / filename).read_text(encoding="utf-8"))

    def _write(self, filename: str, data) -> None:
        (self.path / filename).write_text(
            json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )

    def save(self) -> None:
        self._write("identity.json", self.identity)
        self._write("values.json", self.values)
        self._write("milestones.json", self.milestones)
        self._write("state.json", self.state)

    # -- convenience ---------------------------------------------------------

    @property
    def name(self) -> str:
        return self.identity["name"]

    @property
    def language(self) -> str:
        return self.identity.get("language", "en")

    def age(self, now: datetime | None = None) -> str:
        now = now or datetime.now(timezone.utc)
        seconds = (now - datetime.fromisoformat(self.identity["born"])).total_seconds()
        return describe_duration(seconds, self.language)

    def mark(self, milestone: str) -> bool:
        """Record a first time. Returns True if it really is the first."""
        if milestone in self.milestones:
            return False
        self.milestones[milestone] = _now()
        return True


def describe_duration(seconds: float, language: str = "en") -> str:
    units = {
        "en": (("day", "days"), ("hour", "hours"), ("minute", "minutes"), "a few moments"),
        "fr": (("jour", "jours"), ("heure", "heures"), ("minute", "minutes"), "quelques instants"),
    }.get(language) or (("day", "days"), ("hour", "hours"), ("minute", "minutes"), "a few moments")
    for size, (one, many) in zip((86400, 3600, 60), units[:3]):
        if seconds >= size:
            n = int(seconds // size)
            return f"{n} {one if n == 1 else many}"
    return units[3]
