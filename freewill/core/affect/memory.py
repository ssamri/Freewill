"""Affective memory: traces on memories, their effect on recall, and consolidation.

A trace is a few numbers written in the header of a memory when it is
encoded: the computed state at that moment and the context it came from. It
is not a label such as "joy" or "sadness". Old memories carry none and are
read exactly as before.
"""

from __future__ import annotations

from typing import Callable

from freewill.core.affect.state import AffectConfig, AffectState, clamp, finite

TRACE_VERSION = 1
ASSOCIATION_BAND = (-0.6, 0.8)   # a consolidated association stays inside this interval
NEGATIVE_SHRINK = 0.9            # and a negative one is pulled back a little at each consolidation
MAX_EPISODES = 300


def make_trace(state: AffectState, key: str) -> dict:
    return {"v": round(state["valence"], 3), "a": round(state["arousal"], 3),
            "u": round(state["uncertainty"], 3), "key": key, "ver": TRACE_VERSION}


def read_trace(memory) -> dict | None:
    """The trace of a memory if it has a well-formed one; otherwise None."""
    trace = getattr(memory, "affect", None)
    if not isinstance(trace, dict):
        return None
    try:
        return {"v": clamp(finite(trace.get("v"), "v"), -1.0, 1.0),
                "a": clamp(finite(trace.get("a", 0.3), "a"), 0.0, 1.0),
                "u": clamp(finite(trace.get("u", 0.3), "u"), 0.0, 1.0),
                "key": str(trace.get("key", ""))[:40]}
    except ValueError:
        return None


def encoding_importance(base: float, state: AffectState, setpoints: dict, config: AffectConfig) -> float:
    """What happens under mobilisation is encoded as a little more important. Bounded."""
    gain = clamp(config.encoding_gain * (state["arousal"] - setpoints["arousal"]), -0.10, 0.15)
    return round(clamp(base + gain, 0.05, 0.95), 4)


def recall_bias(state: AffectState, config: AffectConfig, negative_recalled: int) -> Callable:
    """A weight in [1 − gamma, 1 + gamma] for each candidate memory.

    It multiplies a score that relevance has already established, so it can
    reorder close candidates but never bring back an irrelevant memory.
    - Under uncertainty, memories encoded when things were settled weigh more.
    - A memory with a negative trace is never favoured; it weighs less when the
      state is already negative or when the limit of such recalls is reached.
    """
    gamma = config.gamma_recall
    saturated = negative_recalled >= config.negative_recall_limit

    def weight(memory) -> float:
        trace = read_trace(memory)
        if trace is None or gamma == 0:
            return 1.0
        if trace["v"] < -0.2:
            pressure = 1.0 if (saturated or state["valence"] < 0) else 0.5
            return clamp(1.0 - gamma * pressure * min(1.0, abs(trace["v"]) * 2), 1 - gamma, 1.0)
        shift = state["uncertainty"] * (1 - 2 * trace["u"]) + 0.5 * max(0.0, trace["v"]) * state["regulatory_load"]
        return clamp(1.0 + gamma * shift, 1 - gamma, 1 + gamma)

    return weight


def read_associations(data: dict | None) -> dict:
    out = {}
    for key, item in (data or {}).items():
        out[str(key)[:40]] = {
            "n": max(0, min(100000, int(finite(item.get("n", 0), "n")))),
            "valence": clamp(finite(item.get("valence", 0.0), "valence"), *ASSOCIATION_BAND),
            "error": clamp(finite(item.get("error", 0.0), "error"), 0.0, 2.0),
        }
    return out


def _error(episodes: list[dict], associations: dict) -> float:
    """Mean gap between what each episode turned out to be and what was associated with its context."""
    if not episodes:
        return 0.0
    return sum(abs(e["e"] - associations.get(e["key"], {}).get("valence", 0.0)) for e in episodes) / len(episodes)


def consolidate(associations: dict, episodes: list[dict]) -> dict:
    """Fold the episodes lived since the last sleep into the associations, in place.

    For each context, the association moves towards the mean evaluation of its
    new episodes (those lived under more mobilisation count more), by a share
    that shrinks as experience accumulates. Returns a measurable report. This
    changes a small table in the life file; it trains no language model.
    """
    before = _error(episodes, associations)
    grouped: dict[str, list[dict]] = {}
    for episode in episodes:
        grouped.setdefault(episode["key"], []).append(episode)
    changed = []
    for key in sorted(grouped):
        items = grouped[key]
        weights = [0.5 + item.get("a", 0.3) for item in items]
        mean = sum(w * item["e"] for w, item in zip(weights, items)) / sum(weights)
        old = associations.get(key, {"n": 0, "valence": 0.0, "error": 0.0})
        share = min(0.5, len(items) / (old["n"] + len(items)))
        value = old["valence"] + share * (mean - old["valence"])
        if value < 0:
            value *= NEGATIVE_SHRINK
        value = round(clamp(value, *ASSOCIATION_BAND), 4)
        associations[key] = {"n": min(100000, old["n"] + len(items)), "valence": value,
                             "error": round(sum(abs(item["e"] - value) for item in items) / len(items), 4)}
        changed.append({"key": key, "episodes": len(items), "before": round(old["valence"], 4), "after": value})
    after = _error(episodes, associations)
    return {"episodes": len(episodes), "contexts": len(grouped), "error_before": round(before, 4),
            "error_after": round(after, 4), "changed": changed}
