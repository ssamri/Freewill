"""H7, emergent affectivity: computed, regulated internal states with a causal role.

Nothing in this package claims, measures or implies that anything is felt.
"""

from freewill.core.affect.appraisal import Appraisal, Model, Observation, appraise, message_key, stage_key
from freewill.core.affect.dynamics import salience_shift, target, transition
from freewill.core.affect.memory import consolidate, make_trace, read_trace, recall_bias
from freewill.core.affect.regulation import relax, rest
from freewill.core.affect.state import (BOUNDS, DIMENSIONS, RULES_VERSION, SCHEMA_VERSION, SETPOINTS,
                                        AffectConfig, AffectError, AffectState, Temperament)
from freewill.core.affect.system import AffectSystem

__all__ = [
    "AffectConfig", "AffectError", "AffectState", "AffectSystem", "Appraisal", "BOUNDS", "DIMENSIONS",
    "Model", "Observation", "RULES_VERSION", "SCHEMA_VERSION", "SETPOINTS", "Temperament", "appraise",
    "consolidate", "make_trace", "message_key", "read_trace", "recall_bias", "relax", "rest",
    "salience_shift", "stage_key", "target", "transition",
]
