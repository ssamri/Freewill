"""Deterministic disorder.

The logistic map in its chaotic regime: fully determined by its starting
point, never repeating, and sensitive to the smallest difference in history.
Each being starts from its own genome, and each thing it lives nudges the
trajectory, so no two beings drift alike.
"""

from __future__ import annotations


class Drift:
    R = 3.99

    def __init__(self, seed: int, x: float | None = None) -> None:
        self.x = x if x is not None else 0.1 + 0.8 * ((seed % 9973) / 9973)

    def step(self) -> float:
        self.x = self.R * self.x * (1 - self.x)
        # Keep away from the fixed points at 0 and 1.
        self.x = min(max(self.x, 1e-6), 1 - 1e-6)
        return self.x

    def perturb(self, text: str) -> None:
        """Let an experience shift the trajectory, by a hair."""
        nudge = (sum(text.encode("utf-8")) % 1000) / 1e6
        self.x = min(max(self.x + nudge, 1e-6), 1 - 1e-6)
