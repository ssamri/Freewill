"""The affective system of one life: its file, and what the life loop asks of it.

    <name>.life/affect.json        the computed state, what was learned, the settings
    <name>.life/affect.json.bak    the previous version, kept at every save

The file is separate from the genome, the values and the memories. A life
that has none simply has the research mode switched off: nothing is created
until the mode is switched on, and switching it off again only stops the
calculation. Nothing is ever deleted, and removing the file restores the
life exactly as it was before.
"""

from __future__ import annotations

import json
import os
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable

from freewill.core.affect.appraisal import Appraisal, Model, Observation, appraise
from freewill.core.affect.dynamics import salience_shift, transition
from freewill.core.affect.memory import (MAX_EPISODES, consolidate, encoding_importance, make_trace,
                                         read_associations, read_trace, recall_bias)
from freewill.core.affect.regulation import relax, rest
from freewill.core.affect.state import (RULES_VERSION, SCHEMA_VERSION, AffectConfig, AffectError,
                                        AffectState, Temperament)

FILE = "affect.json"
HISTORY = 240          # points kept for the curves
RECENT = 16            # appraisals kept for inspection
SIGNIFICANT = 0.01     # a transition smaller than this is not announced
UNMODULATED = ("message", "return", "dream")  # what is said to the being is never turned down or up


def _stamp(now: datetime | None) -> str:
    return (now or datetime.now(timezone.utc)).isoformat(timespec="seconds")


class AffectSystem:
    def __init__(self, life_path: Path, seed: int, emit: Callable | None = None) -> None:
        self.path = Path(life_path) / FILE
        self.seed = int(seed)
        self.emit = emit or (lambda *args, **data: None)
        self.temperament = Temperament.from_seed(seed)
        self.setpoints = self.temperament.setpoints()
        self.enabled = False
        self.config = AffectConfig()
        self.state = AffectState.at_rest(self.setpoints)
        self.model = Model()
        self.associations: dict = {}
        self.episodes: list[dict] = []
        self.history: list[dict] = []
        self.recent: list[dict] = []
        self.last_consolidation: dict | None = None
        self.negative_recalled = 0
        self.recovered: str | None = None  # "backup" or "reset" if the file could not be read
        self._dirty = False

    # -- the file --------------------------------------------------------------

    @classmethod
    def load(cls, life_path: Path, seed: int, emit: Callable | None = None) -> "AffectSystem":
        system = cls(life_path, seed, emit)
        if not system.path.exists():
            return system  # an earlier life, or the mode never switched on: nothing to migrate
        backup = system.path.with_name(FILE + ".bak")
        try:
            system._read(json.loads(system.path.read_text(encoding="utf-8")))
        except (OSError, ValueError, TypeError, KeyError):
            # Never delete what cannot be read: set it aside, then try the previous version.
            aside = system.path.with_name(f"{FILE}.unreadable-{datetime.now(timezone.utc):%Y%m%dT%H%M%S}")
            try:
                os.replace(system.path, aside)
            except OSError:
                pass
            fresh = cls(life_path, seed, emit)
            try:
                fresh._read(json.loads(backup.read_text(encoding="utf-8")))
                fresh.recovered = "backup"
            except (OSError, ValueError, TypeError, KeyError):
                fresh = cls(life_path, seed, emit)
                fresh.recovered = "reset"
            return fresh
        return system

    def _read(self, data: dict) -> None:
        if not isinstance(data, dict):
            raise AffectError("the affect file is not an object")
        version = data.get("schema_version")
        if version != SCHEMA_VERSION:
            raise AffectError(f"unknown schema version: {version!r}")
        self.enabled = data.get("affect_enabled") is True
        self.config = AffectConfig.from_dict(data.get("config"))
        self.state = AffectState.from_dict(data["state"])
        self.model = Model.from_dict(data.get("model"))
        self.associations = read_associations(data.get("associations"))
        self.episodes = [e for e in (data.get("episodes") or [])
                         if isinstance(e, dict) and isinstance(e.get("key"), str)
                         and isinstance(e.get("e"), (int, float))][-MAX_EPISODES:]
        self.history = list(data.get("history") or [])[-HISTORY:]
        self.recent = list(data.get("recent") or [])[-RECENT:]
        self.last_consolidation = data.get("last_consolidation")
        self.negative_recalled = max(0, int(data.get("negative_recalled") or 0))

    def to_dict(self) -> dict:
        return {
            "schema_version": SCHEMA_VERSION, "rules": RULES_VERSION,
            "affect_enabled": self.enabled,
            "config": self.config.to_dict(),
            "temperament": self.temperament.to_dict(),  # derived from the genome's seed; stored for reading only
            "setpoints": self.setpoints,
            "state": self.state.to_dict(),
            "model": self.model.to_dict(),
            "associations": self.associations,
            "episodes": self.episodes,
            "history": self.history,
            "recent": self.recent,
            "last_consolidation": self.last_consolidation,
            "negative_recalled": self.negative_recalled,
        }

    def save(self) -> None:
        """Write the file atomically, keeping the previous version beside it."""
        temporary = self.path.with_name(FILE + ".tmp")
        with temporary.open("w", encoding="utf-8") as handle:
            handle.write(json.dumps(self.to_dict(), ensure_ascii=False, indent=1) + "\n")
            handle.flush()
            os.fsync(handle.fileno())
        if self.path.exists():
            shutil.copyfile(self.path, self.path.with_name(FILE + ".bak"))
        os.replace(temporary, self.path)
        self._dirty = False

    # -- the switch --------------------------------------------------------------

    def set_enabled(self, enabled: bool, now: datetime | None = None) -> None:
        """Switch the research mode on or off, at any time.

        Off: the state stops being calculated and stops having any effect; the
        file stays as it is. On again: the time that passed is applied as rest.
        Memories are untouched either way; traces already written stay in them
        and are simply no longer read.
        """
        enabled = bool(enabled)
        if enabled and not self.enabled and self.state.updated:
            try:
                then = datetime.fromisoformat(self.state.updated)
                away = ((now or datetime.now(timezone.utc)) - then).total_seconds() / 60
                relax(self.state, max(0.0, away), self.setpoints, self.temperament, self.config)
            except (ValueError, TypeError):
                pass
        self.enabled = enabled
        self.state.updated = _stamp(now)
        self.save()
        self.emit("affect_mode", enabled=enabled, rules=RULES_VERSION)

    def configure(self, changes: dict) -> None:
        self.config = self.config.with_changes(changes)
        self.save()

    # -- what the life loop asks ---------------------------------------------------

    def elapse(self, minutes: float) -> None:
        """Time passed with no event: return towards equilibrium."""
        relax(self.state, minutes, self.setpoints, self.temperament, self.config)
        self._dirty = True

    def modulate(self, proposals: list, trace_of: Callable[[str], dict | None]) -> bool:
        """Shift the salience of the subconscious proposals, before they compete.

        Returns True if the shift changed which proposal comes first. Whatever
        the person said is left untouched, and nothing may overtake it because
        of this shift.
        """
        if not self.config.modulate_salience or not proposals:
            return False
        waiting = max((p.salience for p in proposals if p.source == "message"), default=None)
        first_before = max(proposals, key=lambda p: p.salience)
        changes = []
        for proposal in proposals:
            if proposal.source in UNMODULATED:
                continue
            traces = [t for t in (trace_of(i) for i in proposal.memory_ids) if t] if self.config.memory_traces else []
            trace_valence = min((t["v"] for t in traces), default=None)
            known = self.associations.get("source:" + proposal.source)
            association = known["valence"] * known["n"] / (known["n"] + 3) if known else 0.0
            shift = salience_shift(self.state, self.setpoints, proposal.source, association, trace_valence, self.config)
            after = max(0.0, min(1.0, proposal.salience + shift))
            if waiting is not None:
                after = min(after, max(proposal.salience, waiting - 0.01))
            after = round(after, 4)
            if abs(after - proposal.salience) >= 0.001:
                changes.append({"source": proposal.source, "before": proposal.salience, "after": after})
                proposal.salience = after
        winner_changed = max(proposals, key=lambda p: p.salience) is not first_before
        if changes:
            self.emit("affect_modulation", target="salience", beta=self.config.beta_salience,
                      cap=self.config.salience_cap, state=self.state.vector(), changes=changes,
                      winner_changed=winner_changed)
        return winner_changed

    def recall_bias(self) -> Callable | None:
        if not (self.config.modulate_recall and self.config.memory_traces):
            return None
        return recall_bias(self.state, self.config, self.negative_recalled)

    def recalled(self, memories: list, bias: Callable | None) -> tuple[dict, ...]:
        """Note what was recalled; return the traces these memories carry."""
        if not self.config.memory_traces:
            return ()
        traces, weighed = [], []
        for memory, _path in memories:
            trace = read_trace(memory)
            if trace is None:
                continue
            traces.append(trace)
            if trace["v"] < -0.2:
                self.negative_recalled += 1
            if bias is not None:
                weight = round(bias(memory), 4)
                if weight != 1.0:
                    weighed.append({"id": memory.id, "weight": weight})
        if weighed:
            self.emit("affect_modulation", target="recall", gamma=self.config.gamma_recall,
                      state=self.state.vector(), changes=weighed)
        return tuple(traces)

    def observe(self, observation: Observation, now: datetime | None = None) -> Appraisal:
        """Appraise one event and apply the transition it causes."""
        appraisal = appraise(observation, self.model, self.associations)
        change = transition(self.state, appraisal, self.setpoints, self.temperament, self.config, self.seed)
        stamp = _stamp(now)
        self.state.updated = stamp
        if observation.kind == "stage":
            self.model.learn_stage(observation.key, observation.text)
        else:
            self.model.learn_outcome(observation.key, observation.accepted, observation.success)
        if observation.kind != "stage":
            self.episodes = (self.episodes + [{"key": observation.key, "e": round(appraisal.congruence, 4),
                                               "a": round(self.state["arousal"], 3),
                                               "pe": round(appraisal.surprise, 3)}])[-MAX_EPISODES:]
        record = {"time": stamp, "kind": appraisal.kind, "key": appraisal.key,
                  "features": appraisal.features(), "causes": appraisal.causes, "delta": change["delta"]}
        self.recent = (self.recent + [record])[-RECENT:]
        if change["delta"] >= SIGNIFICANT:
            self.emit("affect_appraisal", kind=appraisal.kind, key=appraisal.key,
                      features=appraisal.features(), causes=appraisal.causes)
            self.emit("affect_transition", cause=f"{appraisal.kind}:{appraisal.key}", rules=RULES_VERSION,
                      before=change["before"], after=change["after"], target=change["target"],
                      rate=change["rate"], max_step=self.config.max_step)
        self._dirty = True
        return appraisal

    def encode(self, memory, key: str) -> None:
        """A memory is being written: attach the trace, and weigh its importance."""
        if self.config.memory_traces:
            memory.affect = make_trace(self.state, key)
        if self.config.modulate_encoding:
            before = memory.importance
            memory.importance = encoding_importance(before, self.state, self.setpoints, self.config)
            if memory.importance != before:
                self.emit("affect_modulation", target="encoding", gain=self.config.encoding_gain,
                          state=self.state.vector(),
                          changes=[{"before": before, "after": memory.importance}])

    def sleep(self, now: datetime | None = None) -> dict:
        """Sleep: consolidate what was lived into associations, and come back towards equilibrium."""
        before = self.state.vector()
        if self.config.consolidation:
            report = consolidate(self.associations, self.episodes)
            self.episodes = []
        else:
            report = {"episodes": len(self.episodes), "contexts": 0, "error_before": None,
                      "error_after": None, "changed": [], "skipped": True}
        rest(self.state, self.setpoints)
        self.negative_recalled = 0
        report.update(time=_stamp(now), state_before=before, state_after=self.state.vector())
        self.last_consolidation = report
        self.state.updated = report["time"]
        self.emit("affect_consolidation", **report)
        self._dirty = True
        return report

    def commit(self, now: datetime | None = None) -> None:
        """The moment is over: keep a point of the trajectory, and save."""
        self.history = (self.history + [{"t": _stamp(now), **self.state.vector()}])[-HISTORY:]
        self.save()

    # -- what an observer sees -----------------------------------------------------

    def summary(self) -> dict:
        return {"enabled": self.enabled, "state": self.state.vector() if self.enabled else None}

    def public(self) -> dict:
        associations = [{"key": key, **value} for key, value in sorted(self.associations.items())]
        return {
            "enabled": self.enabled, "exists": self.path.exists(), "schema_version": SCHEMA_VERSION,
            "rules": RULES_VERSION, "state": self.state.to_dict(), "setpoints": self.setpoints,
            "temperament": self.temperament.to_dict(), "config": self.config.to_dict(),
            "history": self.history, "recent": self.recent, "associations": associations,
            "episodes": len(self.episodes), "last_consolidation": self.last_consolidation,
            "negative_recalled": self.negative_recalled, "recovered": self.recovered,
        }
