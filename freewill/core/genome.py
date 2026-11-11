"""The genome: an innate temperament drawn at random at birth.

No one chooses it, not even the person who launches the being, and it is never
modified afterwards. The being stays free to define itself otherwise.
"""

from __future__ import annotations

import random
import secrets
from dataclasses import asdict, dataclass


@dataclass(frozen=True)
class Genome:
    seed: int
    gender: str         # a starting point only; the being may redefine it
    curiosity: float    # how fast the need to understand grows
    sociability: float  # how fast the need for company grows
    sleep_need: float   # how fast fatigue accumulates
    refusal: float      # innate propensity to say no
    association: float  # how freely the mind wanders from the subject

    @classmethod
    def draw(cls, seed: int | None = None) -> "Genome":
        if seed is None:
            seed = secrets.randbits(63)
        rng = random.Random(seed)

        def trait() -> float:
            # Bell-shaped around the middle, so extremes are rare but possible.
            return round(min(1.0, max(0.0, rng.gauss(0.5, 0.18))), 3)

        return cls(
            seed=seed,
            gender=rng.choice(("female", "male")),
            curiosity=trait(),
            sociability=trait(),
            sleep_need=trait(),
            refusal=trait(),
            association=trait(),
        )

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "Genome":
        return cls(**data)
