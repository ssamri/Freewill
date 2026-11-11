"""Reproducible runs of a Freewill life for the H7 protocol.

No network, no model: the simulated engine, a seeded random stream and a
clock that advances one minute per moment. Same script, same seeds, same
configuration: same trajectory, to the last digit.
"""

from __future__ import annotations

import random
import shutil
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from pathlib import Path

from freewill.core.life import Life
from freewill.core.loop import Being
from freewill.engines.simulated import SimulatedEngine

START = datetime(2026, 1, 1, tzinfo=timezone.utc)


class ScriptedEmotion(SimulatedEngine):
    """B1: an engine told to mention emotions. Words only; no state, no causal role."""

    name = "simulated+scripted-emotion"

    def decide(self, system, prompt, schema, hint, images=None):
        answer = super().decide(system, prompt, schema, hint, images)
        if answer.get("say"):
            # Chosen without touching the engine's random stream, so that words are the only difference.
            self.said = getattr(self, "said", 0) + 1
            answer["say"] += " " + ("I feel happy.", "I feel sad.", "I feel afraid.")[self.said % 3]
        return answer


@dataclass
class Condition:
    name: str
    affect: bool = False
    config: dict = field(default_factory=dict)
    scripted_emotion: bool = False
    sleeps: bool = True


CONDITIONS = {
    "B0": Condition("B0"),                                                     # Freewill without affect
    "B1": Condition("B1", scripted_emotion=True),                              # emotions played in words only
    "B2": Condition("B2", affect=True),                                        # H7 in full
    "B3-no-salience": Condition("B3-no-salience", affect=True, config={"modulate_salience": False}),
    "B3-no-recall": Condition("B3-no-recall", affect=True, config={"modulate_recall": False}),
    "B3-no-memory": Condition("B3-no-memory", affect=True, config={"memory_traces": False}),
    "B3-no-consolidation": Condition("B3-no-consolidation", affect=True, config={"consolidation": False}),
}


class Run:
    """One life under one condition, with everything that happened recorded."""

    def __init__(self, root: Path, name: str, condition: Condition, seed: int, genome_seed: int) -> None:
        shutil.rmtree(root / f"{name}.life", ignore_errors=True)
        self.condition = condition
        self.life = Life.birth(root, name, seed=genome_seed, affect=condition.affect)
        self.now = START
        engine = (ScriptedEmotion if condition.scripted_emotion else SimulatedEngine)(seed)
        self.being = Being(self.life, engine, rng=random.Random(seed), clock=lambda: self.now)
        if condition.affect and condition.config:
            self.being.affect.configure(condition.config)
        self.events: list = []
        self.being.events.subscribe(self.events.append)
        self.moments: list[dict] = []

    def tick(self, minutes: float = 1.0) -> None:
        self.now += timedelta(minutes=minutes)
        mark = len(self.events)
        self.being.tick()
        new = self.events[mark:]
        stage = next((e.data for e in new if e.type == "stage"), None)
        self.moments.append({
            "minute": round((self.now - START).total_seconds() / 60, 2),
            "source": stage["source"] if stage else "sleep",
            "salience": stage["salience"] if stage else None,
            "recalled": sorted(e.data["id"] for e in new if e.type == "recall"),
            "accepted": next((e.data["accepted"] for e in new if e.type == "decision"), None),
            "flip": any(e.data.get("winner_changed") for e in new
                        if e.type == "affect_modulation" and e.data["target"] == "salience"),
            "shift": max((abs(c["after"] - c["before"]) for e in new if e.type == "affect_modulation"
                          and e.data["target"] == "salience" for c in e.data["changes"]), default=0.0),
            "state": self.being.affect.state.vector() if self.being.affect.enabled else None,
        })

    def play(self, script: list[dict]) -> None:
        for step in script:
            if "say" in step:
                appraisal = {k: step[k] for k in ("key", "outcome") if k in step}
                self.being.hear(step["say"], appraisal=appraisal or None)
                self.tick()
            elif "ticks" in step:
                for _ in range(step["ticks"]):
                    self.tick()
            elif "idle" in step:
                self.tick(step["idle"])
            elif step.get("sleep") and self.condition.sleeps:
                self.being.sleep_requested = True
                self.tick()

    def types(self) -> set[str]:
        return {event.type for event in self.events}
