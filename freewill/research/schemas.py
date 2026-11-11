"""Versioned contracts for everything the lab stores.

A record is a plain JSON object. `new()` builds one with its identifier and
schema version; `validate()` says exactly what is wrong with one. Fields not
in the contract are refused, so that a typo cannot become silent data.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

SCHEMA_VERSION = 1

_S, _N, _B, _L, _D = (str,), (int, float), (bool,), (list,), (dict,)
_OPT = (type(None),)

# kind: {field: (accepted types, required)}
SCHEMAS: dict[str, dict[str, tuple[tuple, bool]]] = {
    "Life": {"life_id": (_S, True), "name": (_S, True), "origin": (_S, True), "genome_seed": (_N + _OPT, False),
             "engine": (_D, True), "status": (_S, True), "version": (_S, True)},
    "Snapshot": {"snapshot_id": (_S, True), "life_id": (_S, True), "sha256": (_S, True), "taken_utc": (_S, True),
                 "files": (_L, True), "source": (_S, True)},
    "ResearchEvent": {"event_id": (_S, True), "run_id": (_S, True), "life_id": (_S, True),
                      "clone_id": (_S + _OPT, True), "sequence": ((int,), True), "utc": (_S, True),
                      "sim_time": (_N + _OPT, True), "component": (_S, True), "code_commit": (_S, True),
                      "type": (_S, True), "parents": (_L, True), "before": (_S + _OPT, True),
                      "after": (_S + _OPT, True), "source": (_S, True), "privacy": (_S, True), "data": (_D, True)},
    "ResearchProtocol": {"protocol_id": (_S, True), "protocol_version": (_S, True), "title": (_D, True),
                         "hypotheses": (_L, True), "design": (_S, True), "status": (_S, True),
                         "conditions": (_L, True), "reference": (_S + _OPT, True), "seeds": (_L, True),
                         "genome_seed": ((int,), True), "engine": (_D, True), "history": (_L, True),
                         "probe": (_L, True), "primary_outcome": (_S + _OPT, True),
                         "secondary_outcomes": (_L, True), "budget": (_D, True), "stop": (_D, True),
                         "ethics": (_D, True), "locked": (_B, True), "sha256": (_S + _OPT, True),
                         "locked_utc": (_S + _OPT, False), "notes": (_S, False)},
    "Condition": {"name": (_S, True), "research": (_D, False), "affect": (_B, False), "affect_config": (_D, False),
                  "scripted_emotion": (_B, False), "history": (_S + _OPT, False), "label": (_D, False),
                  "seed_offset": ((int,), False)},
    "Experiment": {"experiment_id": (_S, True), "protocol_id": (_S, True), "protocol_sha256": (_S, True),
                   "status": (_S, True), "created_utc": (_S, True), "approved_by_human": (_B, True),
                   "baseline_snapshot_sha256": (_S, True), "runs": (_L, True), "code_commit": (_S, True),
                   "anomalies": (_L, True), "results_sha256": (_S + _OPT, True)},
    "Run": {"run_id": (_S, True), "experiment_id": (_S, True), "condition": (_S, True), "seed": ((int,), True),
            "clone_id": (_S, True), "status": (_S, True), "moments": ((int,), True), "metrics": (_D, True),
            "journal_sha256": (_S + _OPT, True), "anomalies": (_L, True)},
    "Intervention": {"intervention_id": (_S, True), "run_id": (_S, True), "target": (_S, True), "kind": (_S, True),
                     "changes": (_D, True), "reason": (_S, True), "approved_by_human": (_B, True),
                     "on_clone": (_B, True), "restored": (_B + _OPT, True)},
    "MetricDefinition": {"metric_id": (_S, True), "hypothesis": (_S, True), "version": (_S, True),
                         "unit": (_S, True), "direction": (_S, True), "level": (_S, True),
                         "population": (_S, True), "exclusions": (_S, True), "artefact_risk": (_S, True)},
    "MetricResult": {"metric_id": (_S, True), "version": (_S, True), "value": (_N + _OPT, True),
                     "computable": (_B, True), "reason": (_S + _OPT, True), "n": ((int,), True),
                     "evidence_id": (_S, True), "run_id": (_S + _OPT, True)},
    "Observer": {"observer_id": (_S, True), "name": (_S, True), "role": (_S, True), "instructions": (_S, True),
                 "engine": (_D, True), "mode": (_S, True), "language": (_S, True), "hypotheses": (_L, True),
                 "privacy": (_S, True), "access": (_S, True), "budget": (_D, True), "usage": (_D, True),
                 "cadence_minutes": (_N, True), "temperature": (_N + _OPT, True), "created_utc": (_S, True)},
    "ObserverSession": {"entry_id": (_S, True), "observer_id": (_S, True), "utc": (_S, True), "kind": (_S, True),
                        "text": (_S, True), "evidence": (_L, True), "invalid_citations": (_L, True),
                        "llm": (_S + _OPT, True), "subject": (_S + _OPT, True)},
    "EvidenceReference": {"evidence_id": (_S, True), "kind": (_S, True), "run_id": (_S + _OPT, True),
                          "experiment_id": (_S + _OPT, True), "statement": (_S, True), "value": (_N + _S + _OPT, True),
                          "level": (_S, True)},
    "Review": {"review_id": (_S, True), "experiment_id": (_S, True), "utc": (_S, True), "steps": (_L, True),
               "blinding": (_D, True), "human_validation": (_S + _OPT, True)},
    "ResearchReport": {"report_id": (_S, True), "experiment_id": (_S, True), "language": (_S, True),
                       "status": (_S, True), "created_utc": (_S, True), "author": (_S, True),
                       "files": (_D, True), "validated_by": (_S + _OPT, True), "validated_utc": (_S + _OPT, True),
                       "llm_involved": (_B, True)},
    "ModelVersion": {"model_version": (_S, True), "base_model_id": (_S, True), "base_parameters": ((int,) + _OPT, True),
                     "format": (_S, True), "sha256": (_S + _OPT, True), "licence": (_S + _OPT, True),
                     "adapters": (_L, True), "trainable": (_B, True)},
    "LearningJob": {"job_id": (_S, True), "life_id": (_S, True), "method": (_S, True), "status": (_S, True),
                    "reason": (_S + _OPT, True), "approved_by_human": (_B, True), "budget": (_D, True),
                    "created_utc": (_S, True)},
    "GrowthManifest": {"model_version": (_S, True), "base_model_id": (_S, True),
                       "base_parameters": ((int,) + _OPT, True), "trainable_adapter_parameters": ((int,), True),
                       "added_module_parameters": ((int,), True), "active_parameters": ((int,) + _OPT, True),
                       "training_method": (_S, True), "checkpoint_before": (_S + _OPT, True),
                       "checkpoint_after": (_S + _OPT, True), "heldout_evaluation_id": (_S + _OPT, True),
                       "decision": (_S, True), "note": (_S, True)},
}

_ID_FIELD = {"Life": "life_id", "Snapshot": "snapshot_id", "Experiment": "experiment_id", "Run": "run_id",
             "Intervention": "intervention_id", "Observer": "observer_id", "ObserverSession": "entry_id",
             "Review": "review_id", "ResearchReport": "report_id", "LearningJob": "job_id"}


class SchemaError(ValueError):
    pass


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def new_id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:16]}"


def problems(kind: str, record) -> list[str]:
    """Everything that is wrong with a record of this kind. Empty when it is valid."""
    if kind not in SCHEMAS:
        return [f"unknown kind {kind}"]
    if not isinstance(record, dict):
        return [f"{kind}: not an object"]
    found, schema = [], SCHEMAS[kind]
    if record.get("schema_version") != SCHEMA_VERSION:
        found.append(f"{kind}: schema_version must be {SCHEMA_VERSION}")
    for name, (types, required) in schema.items():
        if name not in record:
            if required:
                found.append(f"{kind}: missing {name}")
        elif not isinstance(record[name], types) or (isinstance(record[name], bool) and bool not in types):
            found.append(f"{kind}: {name} has the wrong type")
    for name in record:
        if name not in schema and name != "schema_version":
            found.append(f"{kind}: unknown field {name}")
    return found


def validate(kind: str, record: dict) -> dict:
    found = problems(kind, record)
    if found:
        raise SchemaError("; ".join(found))
    return record


def new(kind: str, /, **fields) -> dict:
    record = {"schema_version": SCHEMA_VERSION, **fields}
    key = _ID_FIELD.get(kind)
    if key and key not in record:
        record[key] = new_id(kind[:3].lower())
    return validate(kind, record)
