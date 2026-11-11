"""The computed affective state, its configuration and its innate sensitivities.

Everything here is a number with a documented range. These variables are
*computed regulation variables*: they play a causal role in attention, recall
and encoding. They are not evidence that anything is felt, and nothing in the
project may present them as such.
"""

from __future__ import annotations

import math
import random
from dataclasses import asdict, dataclass, field, fields

SCHEMA_VERSION = 1
RULES_VERSION = "h7-0.1"  # changes whenever a rule of calculation changes

# Each dimension and the interval it lives in.
BOUNDS: dict[str, tuple[float, float]] = {
    "valence": (-1.0, 1.0),          # overall evaluation of the situation, negative to positive
    "arousal": (0.0, 1.0),           # how much attention and resources are mobilised
    "uncertainty": (0.0, 1.0),       # predictive gap, kept apart from its evaluation
    "control": (0.0, 1.0),           # estimated ability to act effectively on the context
    "coherence": (0.0, 1.0),         # agreement with what the system expected
    "regulatory_load": (0.0, 1.0),   # functional cost of regulation; never simulated pain
    "social_context": (0.0, 1.0),    # how much the present context is an interaction; not a need to be liked
}
DIMENSIONS = tuple(BOUNDS)

# Where each dimension rests when nothing happens. Engineering choices, not biology.
SETPOINTS: dict[str, float] = {
    "valence": 0.10, "arousal": 0.30, "uncertainty": 0.30, "control": 0.60,
    "coherence": 0.70, "regulatory_load": 0.20, "social_context": 0.20,
}

# The slow layer may not settle far from equilibrium: no lasting negative drift.
BASELINE_BAND: dict[str, tuple[float, float]] = {
    "valence": (-0.25, 0.60), "arousal": (0.10, 0.70), "uncertainty": (0.10, 0.70),
    "control": (0.30, 0.90), "coherence": (0.40, 0.95), "regulatory_load": (0.05, 0.60),
    "social_context": (0.05, 0.60),
}
VALENCE_FLOOR = -0.8  # the fast layer never reaches the extreme negative


class AffectError(ValueError):
    """A value that is not a finite number in its range, or a malformed state."""


def finite(value, name: str = "value") -> float:
    """`value` as a float, or AffectError if it is not a finite number."""
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise AffectError(f"{name} is not a number: {value!r}")
    number = float(value)
    if math.isnan(number) or math.isinf(number):
        raise AffectError(f"{name} is not finite: {value!r}")
    return number


def clamp(value: float, low: float, high: float) -> float:
    return low if value < low else high if value > high else value


def clamp_dimension(name: str, value: float) -> float:
    low, high = BOUNDS[name]
    if name == "valence":
        low = VALENCE_FLOOR
    return clamp(value, low, high)


@dataclass(frozen=True)
class Temperament:
    """Innate affective sensitivities, derived from the genome's seed.

    The genome file itself is neither extended nor rewritten: these values are
    recomputed from the seed it already holds, by a separate random stream, so
    an existing life keeps exactly the innate traits it was born with.
    """

    reactivity: float       # how strongly an appraisal moves the fast layer
    recovery: float         # how fast the fast layer returns to the slow one
    valence_offset: float   # shifts where valence rests
    arousal_offset: float   # shifts where arousal rests

    @classmethod
    def from_seed(cls, seed: int) -> "Temperament":
        rng = random.Random(f"freewill-affect-v1:{int(seed)}")
        return cls(
            reactivity=round(clamp(rng.gauss(1.0, 0.15), 0.6, 1.4), 3),
            recovery=round(clamp(rng.gauss(1.0, 0.12), 0.7, 1.3), 3),
            valence_offset=round(clamp(rng.gauss(0.0, 0.04), -0.08, 0.08), 3),
            arousal_offset=round(clamp(rng.gauss(0.0, 0.03), -0.06, 0.06), 3),
        )

    def setpoints(self) -> dict[str, float]:
        points = dict(SETPOINTS)
        points["valence"] = round(points["valence"] + self.valence_offset, 4)
        points["arousal"] = round(points["arousal"] + self.arousal_offset, 4)
        return points

    def to_dict(self) -> dict:
        return asdict(self)


# name: (default, low, high) for numbers; a plain bool for switches.
_NUMBERS: dict[str, tuple[float, float, float]] = {
    "beta_salience": (0.06, 0.0, 0.15),       # weight of the modulation of salience
    "salience_cap": (0.08, 0.0, 0.15),        # the most one proposal's salience may move
    "gamma_recall": (0.15, 0.0, 0.30),        # the most one memory's recall weight may move
    "encoding_gain": (0.25, 0.0, 0.50),       # weight of arousal in the importance of a new memory
    "rate": (0.35, 0.05, 0.80),               # share of the gap to the target closed by one event
    "max_step": (0.25, 0.01, 0.50),           # the most one dimension may move in one event
    "slow_rate": (0.02, 0.0, 0.10),           # how much the slow layer follows the fast one
    "fast_half_life_min": (20.0, 1.0, 1440.0),
    "slow_half_life_min": (1440.0, 60.0, 43200.0),
    "negative_recall_limit": (2.0, 0.0, 10.0),  # negative-trace memories recalled between two sleeps
    "noise": (0.0, 0.0, 0.02),                # seeded, reproducible jitter; off by default
}
_SWITCHES: dict[str, bool] = {
    "modulate_salience": True,   # ablation: no modulation of the stage
    "modulate_recall": True,     # ablation: no modulation of recall
    "modulate_encoding": True,   # ablation: no modulation of encoding importance
    "memory_traces": True,       # ablation: memories carry no affective trace, and none is read
    "consolidation": True,       # ablation: sleep does not consolidate associations
    "expose_to_engine": False,   # give the computed state to the language model as context
}


@dataclass(frozen=True)
class AffectConfig:
    """Bounded, versioned parameters. Anything out of range is brought back into it."""

    beta_salience: float = _NUMBERS["beta_salience"][0]
    salience_cap: float = _NUMBERS["salience_cap"][0]
    gamma_recall: float = _NUMBERS["gamma_recall"][0]
    encoding_gain: float = _NUMBERS["encoding_gain"][0]
    rate: float = _NUMBERS["rate"][0]
    max_step: float = _NUMBERS["max_step"][0]
    slow_rate: float = _NUMBERS["slow_rate"][0]
    fast_half_life_min: float = _NUMBERS["fast_half_life_min"][0]
    slow_half_life_min: float = _NUMBERS["slow_half_life_min"][0]
    negative_recall_limit: float = _NUMBERS["negative_recall_limit"][0]
    noise: float = _NUMBERS["noise"][0]
    modulate_salience: bool = True
    modulate_recall: bool = True
    modulate_encoding: bool = True
    memory_traces: bool = True
    consolidation: bool = True
    expose_to_engine: bool = False

    @classmethod
    def from_dict(cls, data: dict | None) -> "AffectConfig":
        """Read parameters, ignoring unknown names. Numbers must be finite; they are clamped."""
        values: dict = {}
        for name, value in (data or {}).items():
            if name in _NUMBERS:
                _default, low, high = _NUMBERS[name]
                values[name] = clamp(finite(value, name), low, high)
            elif name in _SWITCHES:
                if not isinstance(value, bool):
                    raise AffectError(f"{name} must be true or false")
                values[name] = value
        return cls(**values)

    def with_changes(self, changes: dict) -> "AffectConfig":
        return AffectConfig.from_dict({**self.to_dict(), **changes})

    def to_dict(self) -> dict:
        return {item.name: getattr(self, item.name) for item in fields(self)}


@dataclass
class AffectState:
    """A fast layer (`values`) that events move, and a slow one (`baseline`) it returns to."""

    values: dict[str, float] = field(default_factory=dict)
    baseline: dict[str, float] = field(default_factory=dict)
    updated: str = ""
    step: int = 0

    @classmethod
    def at_rest(cls, setpoints: dict[str, float], now: str = "") -> "AffectState":
        return cls(values=dict(setpoints), baseline=dict(setpoints), updated=now)

    @classmethod
    def from_dict(cls, data: dict) -> "AffectState":
        """Read a stored state. Raises AffectError on anything that is not a finite number in range."""
        if not isinstance(data, dict):
            raise AffectError("the affective state is not an object")
        state = cls(updated=str(data.get("updated") or ""), step=int(finite(data.get("step", 0), "step")))
        for layer in ("values", "baseline"):
            given = data.get(layer)
            if not isinstance(given, dict):
                raise AffectError(f"the affective state has no {layer}")
            target = getattr(state, layer)
            for name in DIMENSIONS:
                number = finite(given.get(name), f"{layer}.{name}")
                low, high = BOUNDS[name]
                if not low <= number <= high:
                    raise AffectError(f"{layer}.{name} is out of range: {number}")
                target[name] = number
        return state

    def __getitem__(self, name: str) -> float:
        return self.values[name]

    def vector(self) -> dict[str, float]:
        return {name: round(self.values[name], 4) for name in DIMENSIONS}

    def to_dict(self) -> dict:
        return {"values": self.vector(),
                "baseline": {name: round(self.baseline[name], 4) for name in DIMENSIONS},
                "updated": self.updated, "step": self.step}
