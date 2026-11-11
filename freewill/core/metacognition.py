"""H8: a monitor of the being's own decisions.

Before each decision the monitor states how confident it is that the content
on stage will be welcomed, from what it has seen of itself so far. After the
decision it compares. From these pairs come a Brier score and a calibration
table, computed, not narrated. When its recent errors rise well above its
usual ones, it raises an alert: something in how it decides has changed. It
never reads why: the cause of a perturbation is not available to it. With
revision on, an alert makes it trust its old counts less, so that it
recalibrates faster.

This is a functional estimate of some of its own processes. It is not
evidence of self-awareness.
"""

from __future__ import annotations

import json
import os
from pathlib import Path

FILE = "metacognition.json"
WINDOW = 12          # recent decisions compared with the long run
ALERT_MARGIN = 0.10  # how far the recent error must exceed the usual one
HISTORY = 400
RULES_VERSION = "h8-0.1"


class Monitor:
    def __init__(self, life_path: Path, emit=None) -> None:
        self.path = Path(life_path) / FILE
        self.emit = emit or (lambda *args, **kwargs: None)
        self.counts: dict[str, list[float]] = {}   # context -> [welcomed, seen]
        self.pairs: list[list] = []                # [confidence, welcomed, context]
        self.origins: dict[str, int] = {}          # where recalled memories came from
        self.alerts = self.revisions = 0
        self.alerted = False
        if self.path.exists():
            try:
                data = json.loads(self.path.read_text(encoding="utf-8"))
                self.counts, self.pairs = dict(data["counts"]), list(data["pairs"])[-HISTORY:]
                self.origins = dict(data.get("origins", {}))
                self.alerts, self.revisions = int(data.get("alerts", 0)), int(data.get("revisions", 0))
                self.alerted = bool(data.get("alerted", False))
            except (OSError, ValueError, KeyError, TypeError):
                pass  # an unreadable file is started again: these are estimates, not memories

    def predict(self, context: str) -> float:
        """Confidence that a content of this kind will be welcomed, from its own record (Laplace estimate)."""
        welcomed, seen = self.counts.get(context, [0.0, 0.0])
        confidence = round((welcomed + 1) / (seen + 2), 4)
        self.emit("meta_prediction", context=context, confidence=confidence, seen=round(seen, 2))
        return confidence

    def observe(self, context: str, confidence: float, welcomed: bool, revise: bool = True) -> None:
        entry = self.counts.setdefault(context, [0.0, 0.0])
        entry[0] += 1.0 if welcomed else 0.0
        entry[1] += 1.0
        self.pairs = (self.pairs + [[confidence, bool(welcomed), context]])[-HISTORY:]
        error = round((confidence - (1.0 if welcomed else 0.0)) ** 2, 4)
        self.emit("meta_outcome", context=context, confidence=confidence, welcomed=bool(welcomed), error=error)
        if len(self.pairs) >= 3 * WINDOW:
            errors = [(c - (1.0 if w else 0.0)) ** 2 for c, w, _k in self.pairs]
            recent, usual = sum(errors[-WINDOW:]) / WINDOW, sum(errors[:-WINDOW]) / (len(errors) - WINDOW)
            if recent - usual > ALERT_MARGIN and not self.alerted:
                self.alerted = True
                self.alerts += 1
                self.emit("meta_alert", recent=round(recent, 4), usual=round(usual, 4), margin=ALERT_MARGIN)
                if revise:  # trust the old record less: it describes how it used to decide
                    for counts in self.counts.values():
                        counts[0], counts[1] = counts[0] / 4, counts[1] / 4
                    self.revisions += 1
                    self.emit("meta_revision", rule="old counts divided by four")
            elif recent - usual < ALERT_MARGIN / 2:
                self.alerted = False

    def recalled(self, origin: str) -> None:
        self.origins[origin] = self.origins.get(origin, 0) + 1

    def brier(self) -> float | None:
        if not self.pairs:
            return None
        return round(sum((c - (1.0 if w else 0.0)) ** 2 for c, w, _k in self.pairs) / len(self.pairs), 6)

    def save(self) -> None:
        temporary = self.path.with_name(FILE + ".tmp")
        temporary.write_text(json.dumps({
            "rules": RULES_VERSION, "counts": self.counts, "pairs": self.pairs, "origins": self.origins,
            "alerts": self.alerts, "revisions": self.revisions, "alerted": self.alerted}), encoding="utf-8")
        os.replace(temporary, self.path)

    def public(self) -> dict:
        from freewill.research.stats import calibration
        return {"rules": RULES_VERSION, "n": len(self.pairs), "brier": self.brier(), "alerts": self.alerts,
                "revisions": self.revisions, "origins": dict(self.origins),
                "calibration": calibration([c for c, _w, _k in self.pairs], [w for _c, w, _k in self.pairs], 5),
                "contexts": {k: round((a + 1) / (n + 2), 3) for k, (a, n) in sorted(self.counts.items())}}
