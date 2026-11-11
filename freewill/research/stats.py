"""Deterministic statistics. Pure Python, no dependency, no model.

The independent unit is the experimental life (or the pair of lives cloned
from one checkpoint), never the moment: a life of a thousand moments is one
subject. Nothing here returns an interval or a probability from a sample too
small to bear it; it says so instead.
"""

from __future__ import annotations

import itertools
import math
import random

MIN_UNITS_FOR_INTERVAL = 5
MIN_UNITS_FOR_TEST = 6
STATS_VERSION = "1.0"


def mean(values: list[float]) -> float | None:
    return sum(values) / len(values) if values else None


def sd(values: list[float]) -> float | None:
    """Sample standard deviation (n - 1)."""
    if len(values) < 2:
        return None
    m = mean(values)
    return math.sqrt(sum((x - m) ** 2 for x in values) / (len(values) - 1))


def bootstrap_interval(values: list[float], *, seed: int = 20261111, draws: int = 2000,
                       level: float = 0.95) -> list[float] | None:
    """Percentile bootstrap interval of the mean, with a fixed seed: same data, same interval."""
    if len(values) < MIN_UNITS_FOR_INTERVAL:
        return None
    rng, n, means = random.Random(seed), len(values), []
    for _ in range(draws):
        means.append(sum(values[rng.randrange(n)] for _ in range(n)) / n)
    means.sort()
    low = means[int((1 - level) / 2 * draws)]
    high = means[min(draws - 1, int((1 + level) / 2 * draws))]
    return [round(low, 6), round(high, 6)]


def sign_flip_p(differences: list[float], *, seed: int = 20261111, draws: int = 20000) -> float | None:
    """Two-sided paired permutation test on the mean difference. Exact up to 12 pairs."""
    n = len(differences)
    if n < MIN_UNITS_FOR_TEST:
        return None
    observed = abs(sum(differences))
    if n <= 12:
        flips = itertools.product((1, -1), repeat=n)
        total = 2 ** n
    else:
        rng = random.Random(seed)
        flips = ([rng.choice((1, -1)) for _ in range(n)] for _ in range(draws))
        total = draws
    extreme = sum(1 for signs in flips
                  if abs(sum(s * d for s, d in zip(signs, differences))) >= observed - 1e-12)
    return round(extreme / total, 6)


def paired(reference: list[float], treatment: list[float]) -> dict:
    """Treatment minus reference, unit by unit. Says what could not be computed and why."""
    if len(reference) != len(treatment):
        raise ValueError("paired comparison needs the same units on both sides")
    differences = [round(t - r, 10) for r, t in zip(reference, treatment)]
    n, spread = len(differences), sd(differences)
    out = {"n_units": n, "mean_difference": None if not n else round(mean(differences), 6),
           "sd_difference": None if spread is None else round(spread, 6),
           "effect_size_dz": None, "interval_95": bootstrap_interval(differences),
           "p_sign_flip": sign_flip_p(differences), "notes": [], "stats_version": STATS_VERSION}
    if spread:
        out["effect_size_dz"] = round(mean(differences) / spread, 4)
    elif n >= 2:
        out["notes"].append("no_variation")
    if n < MIN_UNITS_FOR_INTERVAL:
        out["notes"].append("too_few_units_for_interval")
    if n < MIN_UNITS_FOR_TEST:
        out["notes"].append("too_few_units_for_test")
    return out


def entropy_bits(counts: dict) -> float:
    total = sum(counts.values())
    if not total:
        return 0.0
    return round(-sum(c / total * math.log2(c / total) for c in counts.values() if c), 6)


# -- H8: confidence against what really happened --------------------------------------

def brier(confidences: list[float], outcomes: list[bool]) -> float | None:
    if not confidences or len(confidences) != len(outcomes):
        return None
    return round(sum((c - (1.0 if o else 0.0)) ** 2 for c, o in zip(confidences, outcomes)) / len(outcomes), 6)


def calibration(confidences: list[float], outcomes: list[bool], bins: int = 10) -> list[dict]:
    """Stated confidence against observed accuracy, by bins of confidence."""
    table = []
    for index in range(bins):
        low, high = index / bins, (index + 1) / bins
        members = [(c, o) for c, o in zip(confidences, outcomes)
                   if low <= c < high or (index == bins - 1 and c == 1.0)]
        if members:
            table.append({"bin": [low, high], "n": len(members),
                          "confidence": round(mean([c for c, _ in members]), 4),
                          "accuracy": round(sum(1 for _, o in members if o) / len(members), 4)})
    return table
