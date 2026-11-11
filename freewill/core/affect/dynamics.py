"""The transition: from an appraisal to a new state.

    a(t+1) = clip( a(t) + bounded( rate · (g(appraisal, state) − a(t)) ) + noise )

`g` is the explicit target written below. Every coefficient is an engineering
choice to be calibrated, not a scientific constant. With the same state, the
same appraisal, the same configuration and the same seed, the result is the
same number.
"""

from __future__ import annotations

import random

from freewill.core.affect.appraisal import Appraisal
from freewill.core.affect.regulation import follow, step_towards
from freewill.core.affect.state import (DIMENSIONS, AffectConfig, AffectState, Temperament, clamp,
                                        clamp_dimension)


def target(appraisal: Appraisal, state: AffectState, setpoints: dict[str, float],
           temperament: Temperament) -> dict[str, float]:
    """g: where this appraisal pulls each dimension. Explicit, deterministic, bounded."""
    r = temperament.reactivity
    load = state["regulatory_load"]
    drive = 0.55 * appraisal.congruence + 0.25 * appraisal.association + 0.20 * appraisal.memory_valence
    out = {
        "valence": setpoints["valence"] + r * drive - 0.2 * max(0.0, load - 0.6),
        "arousal": setpoints["arousal"] + r * (0.45 * appraisal.surprise + 0.25 * appraisal.novelty
                                               + 0.30 * appraisal.relevance) * (1 - 0.5 * load),
        "uncertainty": (0.55 * appraisal.surprise + 0.25 * appraisal.novelty * (1 - appraisal.reliability)
                        + 0.20 * (1 - appraisal.control) + 0.15 * max(0.0, -appraisal.association)),
        "control": appraisal.control * (1 - 0.3 * appraisal.surprise),
        "coherence": appraisal.coherence,
        "regulatory_load": 0.5 * appraisal.load + 0.3 * state["arousal"] + 0.2 * state["uncertainty"],
        "social_context": 1.0 if appraisal.social else state["social_context"],
    }
    return {name: clamp_dimension(name, out[name]) for name in DIMENSIONS}


def transition(state: AffectState, appraisal: Appraisal, setpoints: dict[str, float],
               temperament: Temperament, config: AffectConfig, seed: int = 0) -> dict:
    """Apply one appraisal to `state`, in place. Returns what changed and why."""
    before = state.vector()
    goal = target(appraisal, state, setpoints, temperament)
    # An appraisal of a context never met before moves the state less than a well-known one.
    rate = config.rate * (0.6 + 0.4 * appraisal.reliability)
    jitter = random.Random(f"{int(seed)}:{state.step}") if config.noise else None
    for name in DIMENSIONS:
        moved = step_towards(name, state.values[name], goal[name], rate, config.max_step)
        if jitter is not None:
            moved = clamp_dimension(name, moved + jitter.uniform(-config.noise, config.noise))
        state.values[name] = moved
    follow(state, config)
    state.step += 1
    after = state.vector()
    return {"before": before, "after": after, "target": {k: round(v, 4) for k, v in goal.items()},
            "rate": round(rate, 4),
            "delta": round(max(abs(after[name] - before[name]) for name in DIMENSIONS), 4)}


def salience_shift(state: AffectState, setpoints: dict[str, float], source: str, association: float,
                   trace_valence: float | None, config: AffectConfig) -> float:
    """How much the computed state moves the salience of one proposal. Small and capped.

    - Mobilisation with room to act favours exploring (questions, curiosity, reading).
    - A high regulatory load favours settling over wandering (drift, association).
    - A context that experience consolidated as going well speaks a little louder,
      one that went badly a little softer.
    - A memory that carries a negative trace is never made louder: no rumination.
    """
    arousal = state["arousal"] - setpoints["arousal"]
    load = state["regulatory_load"]
    shift = association
    if source in ("question", "need:curiosity", "need:wonder", "reading"):
        shift += arousal * state["control"] + 0.5 * (state["uncertainty"] - setpoints["uncertainty"])
        shift -= max(0.0, load - 0.5)
    elif source in ("drift", "association"):
        shift -= max(0.0, load - 0.4) + max(0.0, state["uncertainty"] - 0.5)
    elif source == "need:company":
        # Deliberately not driven by valence: a low state must never push towards seeking contact.
        shift = min(shift, 0.0)
    if trace_valence is not None and trace_valence < 0:
        shift = min(shift, 0.0) + 0.5 * trace_valence
    return clamp(config.beta_salience * shift, -config.salience_cap, config.salience_cap)
