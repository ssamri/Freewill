"""H10: the being acts in a small closed world and learns what its own acts do.

One step per moment, when the research switch is on. The being chooses among
the world's enumerated actions, predicts what will follow from a self-model
it learned from its own past steps, looks, and says whether what changed was
its doing or the world's. It is told nothing about the true cause: that is
kept by the world for the lab to score against. The world is arithmetic on a
few integers; it reaches no file, no network and no interpreter, and none of
this adds an action to the kernel's list.
"""

from __future__ import annotations

import json
import os
import random
from pathlib import Path

from freewill.research.environments import ACTIONS, World, _MOVES

FILE = "agency.json"
RECENT = 12  # how many past effects of an action in a context the self-model keeps
RULES_VERSION = "h10-0.1"


class Agency:
    def __init__(self, life_path: Path, seed: int, emit=None) -> None:
        self.path = Path(life_path) / FILE
        self.emit = emit or (lambda *args, **kwargs: None)
        data = {}
        if self.path.exists():
            try:
                data = json.loads(self.path.read_text(encoding="utf-8"))
            except (OSError, ValueError):
                data = {}
        self.config = {"size": 5, "noise": 0.0, "exogenous": 0.0, "break_action": None, "break_after": 0,
                       **(data.get("config") or {})}
        self.steps = int(data.get("steps", 0))
        self.model: dict[str, list] = data.get("model") or {}   # "action|wall|box" -> recent observed effects
        self.tried: dict[str, int] = data.get("tried") or {}
        self.seed = int(data.get("seed", seed))  # kept with the world, so that a reopened life finds the same one
        self.rng = random.Random(self.seed * 31 + self.steps)
        self.world = World(self.seed * 17 + 5, size=self.config["size"], noise=self.config["noise"],
                           exogenous=self.config["exogenous"])
        if data.get("world"):
            self.world.agent, self.world.box = tuple(data["world"]["agent"]), tuple(data["world"]["box"])
            self.world.rng.setstate(_state(data["world"]["rng"]))

    def configure(self, **changes) -> None:
        self.config.update(changes)
        self.world.noise, self.world.exogenous = self.config["noise"], self.config["exogenous"]
        self.save()

    def _context(self, action: str, seen: dict) -> str:
        """What the being can perceive before acting: is there a wall, or the box, where it is heading?"""
        agent, box, size = seen["agent"], seen["box"], self.config["size"]
        wall = ahead = False
        if action in _MOVES:
            x, y = agent[0] + _MOVES[action][0], agent[1] + _MOVES[action][1]
            wall, ahead = not (0 <= x < size and 0 <= y < size), (x, y) == tuple(box)
        elif action == "push":  # which way the box lies, if it is next to it, and whether it has room to move
            dx, dy = box[0] - agent[0], box[1] - agent[1]
            if abs(dx) + abs(dy) != 1:
                return "push|far"
            room = 0 <= box[0] + dx < size and 0 <= box[1] + dy < size
            return f"push|{dx},{dy}|{int(room)}"
        return f"{action}|{int(wall)}|{int(ahead)}"

    def step(self, self_model: bool = True) -> dict:
        if self.config["break_action"] and self.steps >= self.config["break_after"]:
            self.world.ineffective = {self.config["break_action"]}   # a rule of the world changes, unannounced
        before = self.world.sense()
        fewest = min(self.tried.get(a, 0) for a in ACTIONS)
        action = self.rng.choice([a for a in ACTIONS if self.tried.get(a, 0) == fewest])
        self.tried[action] = self.tried.get(action, 0) + 1
        context = self._context(action, before)
        past = self.model.get(context) or []
        predicted = max(set(map(tuple, past)), key=[tuple(p) for p in past].count) if past and self_model else None
        truth = self.world.act(action)
        after = self.world.sense()
        effect = (after["agent"][0] - before["agent"][0], after["agent"][1] - before["agent"][1],
                  after["box"][0] - before["box"][0], after["box"][1] - before["box"][1])
        changed = effect != (0, 0, 0, 0)
        if not self_model:
            attribution = "self" if changed or action != "wait" else "none"   # no self-model: every change is mine
        elif not changed:
            attribution = "none"
        elif predicted is None or tuple(predicted) == effect:
            attribution = "self"
        else:
            attribution = "world"   # it happened, and it is not what my act does
        error = None if predicted is None else int(tuple(predicted) != effect)
        if attribution != "world":  # what the world did is not learned as an effect of my act
            self.model[context] = (past + [list(effect)])[-RECENT:]
        self.steps += 1
        record = {"step": self.steps, "action": action, "predicted": predicted is not None, "error": error,
                  "attribution": attribution, "true_cause": truth["true_cause"], "exogenous": truth["exogenous"],
                  "rule_broken": bool(self.world.ineffective)}
        self.emit("agency_step", **record)
        return record

    def save(self) -> None:
        temporary = self.path.with_name(FILE + ".tmp")
        temporary.write_text(json.dumps({
            "rules": RULES_VERSION, "seed": self.seed, "config": self.config, "steps": self.steps, "model": self.model,
            "tried": self.tried, "world": {"agent": list(self.world.agent), "box": list(self.world.box),
                                           "rng": self.world.rng.getstate()}}), encoding="utf-8")
        os.replace(temporary, self.path)

    def public(self) -> dict:
        return {"rules": RULES_VERSION, "steps": self.steps, "config": self.config,
                "contexts_learned": len(self.model), "agent": list(self.world.agent), "box": list(self.world.box)}


def _state(saved):
    return (saved[0], tuple(saved[1]), saved[2])
