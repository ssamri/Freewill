"""Internal needs and their dynamics.

A being with nothing at stake has no point of view. Lacking a body, its needs
are epistemic and social: to understand, to wonder, to speak, to rest.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass

NEEDS = ("curiosity", "wonder", "company", "fatigue")


def _clamp(x: float) -> float:
    return max(0.0, min(1.0, x))


@dataclass
class Needs:
    curiosity: float = 0.5  # to understand something new
    wonder: float = 0.3     # the pull of the founding questions
    company: float = 0.4    # to speak with someone
    fatigue: float = 0.0    # accumulates with every thought

    def grow(self, minutes: float, *, curiosity: float, sociability: float) -> None:
        """Let time pass. Rates are scaled by the innate temperament."""
        self.curiosity = _clamp(self.curiosity + 0.010 * minutes * (0.5 + curiosity))
        self.wonder = _clamp(self.wonder + 0.004 * minutes * (0.5 + curiosity))
        self.company = _clamp(self.company + 0.008 * minutes * (0.5 + sociability))

    def after_thought(self, sleep_need: float) -> None:
        self.fatigue = _clamp(self.fatigue + 0.01 * (0.5 + sleep_need))

    def satisfy(self, need: str, amount: float) -> None:
        setattr(self, need, _clamp(getattr(self, need) - amount))

    def most_pressing(self) -> tuple[str, float]:
        name = max(("curiosity", "wonder", "company"), key=lambda n: getattr(self, n))
        return name, getattr(self, name)

    def to_dict(self) -> dict[str, float]:
        return {k: round(v, 4) for k, v in asdict(self).items()}

    @classmethod
    def from_dict(cls, data: dict[str, float]) -> "Needs":
        return cls(**{k: float(data[k]) for k in NEEDS if k in data})
