"""H4: a small trainable module beside the engine, trained during sleep on what the being lived.

What this is: a real parametric model, a few dozen weights, that learns to
predict which contents the being welcomes, and whose prediction shifts the
salience of proposals by a small bounded amount. Its weights really change,
by gradient descent, on episodes of this life only; every training is
measured on episodes held out of it and on older ones, kept only if it helps
without forgetting, and written to a manifest with the hash of the weights
before and after. Growth adds one specialist with its own weights for a
context the module predicts badly, under a fixed quota, and counts how often
that specialist is actually used.

What this is not: the language model's own weights are not touched. No engine
of this version can be trained; this module is the part of the system whose
parameters a life rewrites.
"""

from __future__ import annotations

import hashlib
import json
import math
import os
import zlib
from pathlib import Path

FILE = "adapter.json"
D = 24                 # weights per expert, plus one bias
MAX_EXPERTS = 4        # the base and at most three specialists: the quota of growth
MAX_EPISODES = 2000
EPOCHS, RATE = 30, 0.15
MIN_GAIN = 0.001       # a training is kept only if held-out loss falls by at least this
MAX_FORGETTING = 0.02  # and loss on older episodes rises by no more than this
SALIENCE_CAP = 0.05
RULES_VERSION = "h4-0.1"


def features(tokens: list[str]) -> list[float]:
    x = [0.0] * D
    for token in tokens:
        x[zlib.crc32(token.encode("utf-8")) % D] = 1.0
    return x


def _sigmoid(z: float) -> float:
    return 1 / (1 + math.exp(-max(-30.0, min(30.0, z))))


class Adapter:
    def __init__(self, life_path: Path, emit=None) -> None:
        self.path = Path(life_path) / FILE
        self.emit = emit or (lambda *args, **kwargs: None)
        self.experts: list[dict] = [{"context": None, "w": [0.0] * D, "b": 0.0, "used": 0}]
        self.episodes: list[list] = []      # [tokens, context, welcomed]
        self.consolidated = 0               # episodes already present at the last training
        self.manifests: list[dict] = []
        self.trained = False
        if self.path.exists():
            try:
                data = json.loads(self.path.read_text(encoding="utf-8"))
                self.experts, self.episodes = data["experts"], data["episodes"]
                self.consolidated, self.manifests = data["consolidated"], data["manifests"]
                self.trained = data["trained"]
            except (OSError, ValueError, KeyError):
                pass

    # -- the model -------------------------------------------------------------------------

    def parameters(self) -> int:
        return sum(len(e["w"]) + 1 for e in self.experts)

    def weights_hash(self, experts=None) -> str:
        blob = json.dumps([[e["context"], e["w"], e["b"]] for e in (experts or self.experts)])
        return hashlib.sha256(blob.encode("utf-8")).hexdigest()

    @staticmethod
    def _score(experts: list[dict], x: list[float], context: str, count: bool = False) -> float:
        z = 0.0
        for expert in experts:
            if expert["context"] in (None, context):   # a specialist speaks only in its own context
                z += sum(w * v for w, v in zip(expert["w"], x)) + expert["b"]
                if count:
                    expert["used"] += 1
        return _sigmoid(z)

    def predict(self, tokens: list[str], context: str) -> float:
        return self._score(self.experts, features(tokens), context, count=True)

    def shift(self, tokens: list[str], context: str) -> float:
        """How much the learned prediction moves a proposal's salience. Zero until a training was kept."""
        if not self.trained:
            return 0.0
        return round(SALIENCE_CAP * (2 * self.predict(tokens, context) - 1), 4)

    def record(self, tokens: list[str], context: str, welcomed: bool) -> None:
        self.episodes = (self.episodes + [[tokens, context, bool(welcomed)]])[-MAX_EPISODES:]

    # -- training, during sleep ----------------------------------------------------------------

    @classmethod
    def _loss(cls, experts, episodes) -> float | None:
        if not episodes:
            return None
        total = 0.0
        for tokens, context, welcomed in episodes:
            p = min(1 - 1e-6, max(1e-6, cls._score(experts, features(tokens), context)))
            total -= math.log(p if welcomed else 1 - p)
        return round(total / len(episodes), 6)

    @classmethod
    def _fit(cls, experts, episodes, only: int | None = None) -> None:
        for _ in range(EPOCHS):
            for tokens, context, welcomed in episodes:
                x = features(tokens)
                gradient = cls._score(experts, x, context) - (1.0 if welcomed else 0.0)
                for index, expert in enumerate(experts):
                    if expert["context"] in (None, context) and only in (None, index):
                        expert["w"] = [w - RATE * gradient * v for w, v in zip(expert["w"], x)]
                        expert["b"] -= RATE * gradient

    def consolidate(self, grow: bool = False) -> dict | None:
        """Train on what was lived since the last sleep, replaying the older episodes. Keep it only if it helps."""
        new = self.episodes[self.consolidated:]
        if len(new) < 8:
            return None
        held = [e for i, e in enumerate(self.episodes) if i % 5 == 4]        # never trained on
        train = [e for i, e in enumerate(self.episodes) if i % 5 != 4]       # old and new together: replay
        old = [e for i, e in enumerate(self.episodes[:self.consolidated]) if i % 5 != 4]
        before = [dict(e, w=list(e["w"])) for e in self.experts]
        candidate = [dict(e, w=list(e["w"])) for e in self.experts]
        self._fit(candidate, train)
        report = self._judge(before, candidate, held, old, "lora-like adapter, gradient descent", added=0)
        if report["decision"] == "accepted" and grow and len(self.experts) < MAX_EXPERTS:
            worst = self._worst_context(held)
            if worst:
                grown = [dict(e, w=list(e["w"])) for e in self.experts] + [
                    {"context": worst, "w": [0.0] * D, "b": 0.0, "used": 0}]
                self._fit(grown, [e for e in train if e[1] == worst], only=len(grown) - 1)
                self._judge([dict(e, w=list(e["w"])) for e in self.experts], grown, held, old,
                            f"specialist expert for context {worst}", added=D + 1)
        self.consolidated = len(self.episodes)
        self.save()
        return report

    def _worst_context(self, held) -> str | None:
        by: dict[str, list] = {}
        for episode in held:
            by.setdefault(episode[1], []).append(episode)
        owned = {e["context"] for e in self.experts}
        losses = {c: self._loss(self.experts, eps) for c, eps in by.items() if len(eps) >= 3 and c not in owned}
        overall = self._loss(self.experts, held)
        worst = max(losses, key=losses.get, default=None)
        return worst if worst and losses[worst] > overall + 0.05 else None

    def _judge(self, before, candidate, held, old, method: str, added: int) -> dict:
        held_before, held_after = self._loss(before, held), self._loss(candidate, held)
        old_before, old_after = self._loss(before, old), self._loss(candidate, old)
        gain = (held_before - held_after) if held_before is not None else 0.0
        forgetting = (old_after - old_before) if old_before is not None else 0.0
        accepted = gain >= MIN_GAIN and forgetting <= MAX_FORGETTING
        delta = math.sqrt(sum((a - b) ** 2 for e1, e2 in zip(before, candidate) for a, b in zip(e1["w"], e2["w"]))
                          + sum(w * w for e in candidate[len(before):] for w in e["w"]))
        report = {
            "rules": RULES_VERSION, "training_method": method, "decision": "accepted" if accepted else "rejected",
            "checkpoint_before": self.weights_hash(before), "checkpoint_after": self.weights_hash(candidate),
            "trainable_parameters": sum(len(e["w"]) + 1 for e in candidate), "added_module_parameters": added if accepted else 0,
            "weight_delta_l2": round(delta, 6), "heldout_loss_before": held_before, "heldout_loss_after": held_after,
            "old_loss_before": old_before, "old_loss_after": old_after, "heldout_n": len(held),
            "episodes": len(self.episodes), "engine_weights_changed": False}
        if accepted:
            self.experts, self.trained = candidate, True
        else:   # rejected: the weights of before are kept, to the bit
            report["checkpoint_after"] = report["checkpoint_before"]
        self.manifests = (self.manifests + [report])[-50:]
        self.emit("learning_job", **report)
        return report

    def rollback(self) -> None:
        """Return to untrained weights. A person can always ask for this."""
        self.experts = [{"context": None, "w": [0.0] * D, "b": 0.0, "used": 0}]
        self.trained, self.consolidated = False, 0
        self.emit("learning_rollback", parameters=self.parameters())
        self.save()

    def save(self) -> None:
        temporary = self.path.with_name(FILE + ".tmp")
        temporary.write_text(json.dumps({
            "rules": RULES_VERSION, "experts": self.experts, "episodes": self.episodes,
            "consolidated": self.consolidated, "manifests": self.manifests, "trained": self.trained}), encoding="utf-8")
        os.replace(temporary, self.path)

    def public(self) -> dict:
        return {"rules": RULES_VERSION, "trained": self.trained, "parameters": self.parameters(),
                "experts": [{"context": e["context"], "parameters": len(e["w"]) + 1, "used": e["used"]} for e in self.experts],
                "episodes": len(self.episodes), "weights_sha256": self.weights_hash(), "manifests": self.manifests[-10:],
                "quota_experts": MAX_EXPERTS, "engine_weights_changed": False}
