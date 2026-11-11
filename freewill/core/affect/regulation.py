"""Regulation: bounded steps, return to equilibrium, and guards against runaway states.

Every update of the state goes through this module, so that no appraisal,
however extreme, can move a dimension out of its range, faster than the
permitted speed, or into a lasting negative drift.
"""

from __future__ import annotations

import math

from freewill.core.affect.state import (BASELINE_BAND, DIMENSIONS, AffectConfig, AffectState,
                                        Temperament, clamp, clamp_dimension, finite)

MAX_MINUTES = 60 * 24 * 365 * 10  # ten years: longer absences relax completely anyway
NEGATIVE_STEP = 0.8               # a step towards the negative is shortened
NEGATIVE_RECOVERY = 1.5           # and valence below its baseline recovers faster


def step_towards(name: str, current: float, target: float, rate: float, max_step: float) -> float:
    """Move `current` towards `target` by a bounded step, and keep it in range."""
    step = clamp(rate * (target - current), -max_step, max_step)
    if name == "valence" and step < 0:
        step *= NEGATIVE_STEP
    return clamp_dimension(name, current + step)


def follow(state: AffectState, config: AffectConfig) -> None:
    """Let the slow layer follow the fast one a little, inside its band."""
    for name in DIMENSIONS:
        low, high = BASELINE_BAND[name]
        moved = state.baseline[name] + config.slow_rate * (state.values[name] - state.baseline[name])
        state.baseline[name] = clamp(moved, low, high)


def relax(state: AffectState, minutes: float, setpoints: dict[str, float],
          temperament: Temperament, config: AffectConfig) -> None:
    """Let time pass: the fast layer returns to the slow one, the slow one to the setpoints.

    Exponential decay in closed form: it cannot overshoot or diverge however
    long the interval, and one long interval gives nearly the same result as
    many short ones (not exactly: the slow layer moves while the fast one
    returns to it).
    """
    minutes = clamp(finite(minutes, "minutes"), 0.0, MAX_MINUTES)
    if minutes == 0:
        return
    slow = math.pow(0.5, minutes / config.slow_half_life_min)
    for name in DIMENSIONS:
        low, high = BASELINE_BAND[name]
        state.baseline[name] = clamp(setpoints[name] + (state.baseline[name] - setpoints[name]) * slow, low, high)
        half_life = config.fast_half_life_min / temperament.recovery
        if name == "valence" and state.values[name] < state.baseline[name]:
            half_life /= NEGATIVE_RECOVERY
        fast = math.pow(0.5, minutes / half_life)
        state.values[name] = clamp_dimension(
            name, state.baseline[name] + (state.values[name] - state.baseline[name]) * fast)


def rest(state: AffectState, setpoints: dict[str, float]) -> None:
    """After sleep: the slow layer comes halfway back to equilibrium, the load is released."""
    for name in DIMENSIONS:
        low, high = BASELINE_BAND[name]
        state.baseline[name] = clamp(state.baseline[name] + 0.5 * (setpoints[name] - state.baseline[name]), low, high)
        state.values[name] = clamp_dimension(name, state.baseline[name] + 0.5 * (state.values[name] - state.baseline[name]))
    state.values["regulatory_load"] = min(state.values["regulatory_load"], setpoints["regulatory_load"])
