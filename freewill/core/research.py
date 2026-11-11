"""Research settings: which mechanisms of a life are running, and how strongly.

Each switch removes or restores one mechanism of the life loop, so that its
contribution can be measured by comparing a life with it and a life without
it. Every default reproduces the loop as it is without this file: a life that
has no `research.json` lives exactly as before.

None of this reaches the kernel. The closed list of actions, the limits on
what an action may carry and the founding questions cannot be changed here,
and nothing here gives the being a new power.
"""

from __future__ import annotations

import json
import math
import os
import time
from pathlib import Path

SCHEMA_VERSION = 1
FILE = "research.json"

# name: (default, group)
SWITCHES: dict[str, tuple[bool, str]] = {
    "gen_reminiscence": (True, "subconscious"),
    "gen_need": (True, "subconscious"),
    "gen_question": (True, "subconscious"),
    "gen_association": (True, "subconscious"),
    "gen_drift": (True, "subconscious"),
    "gen_reading": (True, "subconscious"),
    "learning": (True, "subconscious"),
    "habituation": (True, "subconscious"),
    "remembering": (True, "memory"),
    "forgetting": (True, "memory"),
    "auto_sleep": (True, "sleep"),
    "dreaming": (True, "sleep"),
    "dream_linking": (True, "sleep"),
    "dream_residue": (True, "sleep"),
    "spontaneous_speech": (True, "expression"),
    "adopting_values": (True, "expression"),
    "sense_of_time": (True, "expression"),
    # Research modules. Off by default: a life without them lives exactly as before.
    "sleep_replay": (True, "sleep"),          # memories drawn at night are strengthened by being replayed
    "metacognition": (False, "modules"),      # H8: predicts its own decisions and compares
    "meta_revision": (True, "modules"),       # H8: an alert makes it trust its old record less
    "sandbox": (False, "modules"),            # H10: one act per moment in the closed virtual world
    "self_model": (True, "modules"),          # H10: attributes changes with a learned model of its own acts
    "learner": (False, "modules"),            # H4: the small trainable module, trained during sleep
    "learner_growth": (False, "modules"),     # H4: the module may add a specialist, under quota
    "own_model": (False, "modules"),          # H4: Freewill's own neural network, trained during sleep
    "own_model_growth": (False, "modules"),   # H4: that network may add layers, under the ceiling below
}

# name: (default, lowest, highest, whole number, group)
NUMBERS: dict[str, tuple[float, float, float, bool, str]] = {
    "noise": (0.08, 0.0, 0.3, False, "subconscious"),
    "recall_k": (3, 0, 6, True, "memory"),
    "dreams_max": (3, 0, 3, True, "sleep"),
    "tempo": (20.0, 2.0, 3600.0, False, "rhythm"),
    "thoughts_per_hour": (120, 0, 3600, True, "rhythm"),
    "own_model_steps": (60, 1, 5000, True, "modules"),             # gradient steps per sleep
    "own_model_max_millions": (5.0, 0.1, 4000.0, False, "modules"),  # ceiling on its size, in millions of parameters
}

# What a generator switch silences: the sources of the proposals it makes.
GENERATORS = {
    "gen_reminiscence": "reminiscence", "gen_need": "need", "gen_question": "question",
    "gen_association": "association", "gen_drift": "drift", "gen_reading": "reading",
}


class ResearchError(ValueError):
    """A setting that is unknown, of the wrong kind, or not a finite number."""


def defaults() -> dict:
    values: dict = {name: default for name, (default, _group) in SWITCHES.items()}
    values.update({name: (int(spec[0]) if spec[3] else float(spec[0])) for name, spec in NUMBERS.items()})
    return values


def spec() -> list[dict]:
    """The settings, in order, for an interface to draw."""
    out = [{"name": name, "kind": "switch", "default": default, "group": group}
           for name, (default, group) in SWITCHES.items()]
    out += [{"name": name, "kind": "number", "default": int(d) if whole else d, "min": low, "max": high,
             "whole": whole, "group": group} for name, (d, low, high, whole, group) in NUMBERS.items()]
    return out


def _check(name: str, value):
    if name in SWITCHES:
        if not isinstance(value, bool):
            raise ResearchError(f"{name} must be true or false")
        return value
    if name in NUMBERS:
        _default, low, high, whole, _group = NUMBERS[name]
        if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
            raise ResearchError(f"{name} must be a finite number")
        value = max(low, min(high, value))
        return int(round(value)) if whole else round(float(value), 4)
    raise ResearchError(f"unknown setting: {name}")


class Research:
    def __init__(self, path: Path, values: dict | None = None, recovered: bool = False) -> None:
        self.path = path
        self.values = defaults()
        self.recovered = recovered  # an unreadable file was set aside and the defaults taken
        for name, value in (values or {}).items():
            if name in self.values:  # names from a later version are ignored, not fatal
                self.values[name] = _check(name, value)

    @classmethod
    def load(cls, life_path: Path) -> "Research":
        path = Path(life_path) / FILE
        if not path.exists():
            return cls(path)
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            return cls(path, dict(data["values"]))
        except (OSError, ValueError, KeyError, TypeError):
            try:  # keep what could not be read, for whoever wants to look at it
                os.replace(path, path.with_name(f"{FILE}.unreadable-{int(time.time())}"))
            except OSError:
                pass
            return cls(path, recovered=True)

    def __getattr__(self, name: str):
        values = self.__dict__.get("values") or {}
        if name in values:
            return values[name]
        raise AttributeError(name)

    def silenced(self) -> set[str]:
        """The proposal sources that are switched off."""
        return {source for name, source in GENERATORS.items() if not self.values[name]}

    def changed(self) -> dict:
        """What differs from the defaults: the experimental condition this life is in."""
        base = defaults()
        return {name: value for name, value in self.values.items() if value != base[name]}

    def update(self, changes: dict) -> dict:
        """Apply changes, all or none. Returns what actually changed, as {name: [before, after]}."""
        if not isinstance(changes, dict):
            raise ResearchError("changes must be an object")
        checked = {name: _check(name, value) for name, value in changes.items()}
        moved = {name: [self.values[name], value] for name, value in checked.items()
                 if self.values[name] != value}
        if moved:
            self.values.update(checked)
            self.save()
        return moved

    def reset(self) -> dict:
        return self.update(defaults())

    def save(self) -> None:
        payload = json.dumps({"schema_version": SCHEMA_VERSION, "values": self.values},
                             ensure_ascii=False, indent=2) + "\n"
        temporary = self.path.with_name(FILE + ".tmp")
        with temporary.open("w", encoding="utf-8") as handle:
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, self.path)

    def public(self) -> dict:
        return {"values": dict(self.values), "changed": self.changed(), "spec": spec(),
                "exists": self.path.exists(), "recovered": self.recovered}
