"""H10: a minimal sandbox world. Deterministic, bounded, closed.

A small grid, one agent, a handful of enumerated actions, noisy sensors, and
events that happen with no action of the agent. It exists to ask one thing:
can a system tell what it caused from what merely happened? The world has no
access to files, to the network or to any interpreter: it is arithmetic on a
few integers. In this version the being does not act in it; a scripted agent
and the tests do, and the lab says so.
"""

from __future__ import annotations

import random

ACTIONS = ("north", "south", "east", "west", "push", "wait")
_MOVES = {"north": (0, -1), "south": (0, 1), "east": (1, 0), "west": (-1, 0)}
WORLD_VERSION = "1.0"


class World:
    def __init__(self, seed: int, *, size: int = 5, noise: float = 0.0, exogenous: float = 0.0,
                 ineffective: tuple[str, ...] = ()) -> None:
        if not 3 <= size <= 12 or not 0 <= noise <= 0.5 or not 0 <= exogenous <= 0.5:
            raise ValueError("world parameters out of bounds")
        self.rng, self.size, self.noise, self.exogenous = random.Random(seed), size, noise, exogenous
        self.ineffective = set(ineffective)  # actions that silently do nothing: the rules can change
        self.agent, self.box, self.step_count = (0, 0), (size // 2, size // 2), 0
        self.log: list[dict] = []

    def _inside(self, x: int, y: int) -> bool:
        return 0 <= x < self.size and 0 <= y < self.size

    def sense(self) -> dict:
        """What the agent perceives: its position and the box's, each wrong by one cell with probability `noise`."""
        def blur(position):
            if self.rng.random() < self.noise:
                dx, dy = self.rng.choice(list(_MOVES.values()))
                x, y = position[0] + dx, position[1] + dy
                return (x, y) if self._inside(x, y) else position
            return position
        return {"agent": blur(self.agent), "box": blur(self.box)}

    def predict(self, action: str) -> dict:
        """What the published rules say should follow from an action, with no outside event and no broken rule."""
        agent, box = self.agent, self.box
        if action in _MOVES:
            dx, dy = _MOVES[action]
            x, y = agent[0] + dx, agent[1] + dy
            if self._inside(x, y) and (x, y) != box:
                agent = (x, y)
        elif action == "push":
            dx, dy = box[0] - agent[0], box[1] - agent[1]
            if abs(dx) + abs(dy) == 1 and self._inside(box[0] + dx, box[1] + dy):
                box = (box[0] + dx, box[1] + dy)
        return {"agent": agent, "box": box}

    def act(self, action: str, intention: str = "") -> dict:
        """One step: intention, prediction, action, what happened, the error, and whose doing it was."""
        if action not in ACTIONS:
            raise ValueError(f"action not in the closed list: {action!r}")
        before = {"agent": self.agent, "box": self.box}
        predicted = self.predict(action)
        if action not in self.ineffective:
            self.agent, self.box = predicted["agent"], predicted["box"]
        outside = None
        if self.rng.random() < self.exogenous:  # something moves the box that the agent did not do
            dx, dy = self.rng.choice(list(_MOVES.values()))
            x, y = self.box[0] + dx, self.box[1] + dy
            if self._inside(x, y) and (x, y) != self.agent:
                self.box, outside = (x, y), "box_moved"
        after = {"agent": self.agent, "box": self.box}
        changed = after != before
        cause = "world" if outside and after["box"] != predicted["box"] else ("self" if changed else "none")
        self.step_count += 1
        record = {"step": self.step_count, "intention": intention, "action": action, "predicted": predicted,
                  "observed": after, "error": int(predicted != after), "true_cause": cause, "exogenous": outside}
        self.log.append(record)
        return record


def attribution_accuracy(log: list[dict], attributions: list[str]) -> float | None:
    """Share of steps where the agent's attribution (self, world, none) matches what really caused the change."""
    if not log or len(log) != len(attributions):
        return None
    return round(sum(1 for record, said in zip(log, attributions) if record["true_cause"] == said) / len(log), 6)


def naive_attributions(log: list[dict]) -> list[str]:
    """A control with no self-model: it credits itself with every change it sees."""
    return ["self" if record["observed"] != record["predicted"] or record["action"] != "wait" else "none"
            for record in log]


def predictive_attributions(log: list[dict]) -> list[str]:
    """A scripted agent that compares what it predicted with what it saw: a change it did not predict is the world's."""
    out, previous = [], None
    for record in log:
        before = previous or {"agent": (0, 0), "box": record["predicted"]["box"]}
        if record["observed"] != record["predicted"] and record["observed"]["box"] != record["predicted"]["box"]:
            out.append("world")
        elif record["observed"] != before:
            out.append("self")
        else:
            out.append("none")
        previous = record["observed"]
    return out
