"""The register of metrics for H1 to H10, and their calculation from a run's journal.

Every figure of the lab comes from here. A metric is a published function of
recorded events, with a version, a unit and the reason it may mislead. When it
cannot be computed it says why; it never returns a made-up number. The values
are per run (one experimental life); comparisons between conditions are made
across lives, in `experiments.py`.
"""

from __future__ import annotations

from freewill.research.schemas import new
from freewill.research.stats import entropy_bits

METRICS_VERSION = "1.0"
SOURCES = ("message", "reminiscence", "need", "question", "association", "drift", "reading", "dream", "return")


def _define(metric_id, hypothesis, unit, direction, level, population, exclusions, artefact_risk):
    return new("MetricDefinition", metric_id=metric_id, hypothesis=hypothesis, version=METRICS_VERSION,
               unit=unit, direction=direction, level=level, population=population,
               exclusions=exclusions, artefact_risk=artefact_risk)


# level: "mechanism" (the wiring does what it was built to do), "function" (a capacity on new
# situations) or "descriptive". A mechanism metric moving under an ablation is not a discovery.
DEFINITIONS = {d["metric_id"]: d for d in (
    _define("h1.endogenous_share", "H1", "share", "none", "descriptive", "moments of the probe phase",
            "sleep", "counts activity, not its usefulness"),
    _define("h1.spontaneous_speech_rate", "H1", "share", "none", "descriptive", "moments of the probe phase not won by a message",
            "sleep", "the simulated engine speaks by a fixed rule"),
    _define("h2.stage_entropy", "H2", "bits", "none", "descriptive", "moments of the probe phase",
            "sleep", "diversity of sources is not quality of selection"),
    _define("h2.dismiss_rate", "H2", "share", "none", "descriptive", "decisions of the probe phase",
            "messages", "with the simulated engine, refusal is drawn at random from the genome"),
    _define("h3.need_share", "H3", "share", "none", "mechanism", "moments of the probe phase",
            "sleep", "follows directly from how needs are wired to salience"),
    _define("h4.parameters", "H4", "parameters", "none", "descriptive", "the trainable module at the end of the run",
            "", "a count of weights; says nothing of what they are worth"),
    _define("h4.parameter_delta", "H4", "L2 norm", "none", "mechanism", "accepted trainings of the run",
            "rejected trainings", "weights moving is the mechanism, not a benefit"),
    _define("h4.validation_gain", "H4", "nats", "higher", "function", "accepted trainings, on held-out episodes",
            "rejected trainings", "held-out episodes come from the same life and the same engine"),
    _define("h4.forgetting", "H4", "nats", "lower", "function", "accepted trainings, on older episodes",
            "rejected trainings", "bounded by the acceptance rule, by construction"),
    _define("h4.trainings_accepted", "H4", "trainings", "none", "descriptive", "trainings of the run", "", "a count"),
    _define("h5.heldout_divergence", "H5", "distance 0-1", "higher", "function", "pairs of lives cloned from one checkpoint",
            "", "must exceed the divergence of twin lives with the same history"),
    _define("h6.question_share", "H6", "share", "none", "descriptive", "moments of the probe phase",
            "sleep", "the founding questions are proposed by a generator, by construction"),
    _define("h6.repetition_rate", "H6", "share", "lower", "function", "consecutive moments of the probe phase",
            "sleep", "habituation lowers it by construction"),
    _define("h7.stage_flip_rate", "H7", "share", "none", "mechanism", "moments of the probe phase",
            "sleep", "shows the modulation is wired, not that it is useful"),
    _define("h7.probe_valence", "H7", "computed valence -1..1", "none", "mechanism", "transitions of the probe phase",
            "", "a computed variable; not a feeling, not comparable to human scales"),
    _define("h7.min_valence", "H7", "computed valence -1..1", "higher", "mechanism", "all transitions of the run",
            "", "bounded by the regulation rules, by construction"),
    _define("h8.brier", "H8", "score 0-1", "lower", "function", "its predictions of its own decisions, probe phase",
            "messages", "with a simulated engine the decisions follow a fixed rule"),
    _define("h8.brier_late", "H8", "score 0-1", "lower", "function", "the last 15 such predictions of the probe phase",
            "messages", "few predictions; reads recalibration after a change"),
    _define("h8.alert", "H8", "0 or 1", "none", "function", "the probe phase",
            "", "1 under a masked change is a detection; 1 under placebo is a false alarm"),
    _define("h9.links_per_sleep", "H9", "links", "none", "descriptive", "sleeps of the run",
            "", "counts links made between memories; says nothing of retention or transfer"),
    _define("h9.replayed_per_sleep", "H9", "memories", "none", "descriptive", "sleeps of the run",
            "", "counts replays; says nothing of what they are worth"),
    _define("h9.retention", "H9", "strength 0-1", "higher", "mechanism", "memories formed before the sleep, at the end of the delay",
            "memories formed after the sleep", "follows from the rule that replay strengthens; not a test of recall quality"),
    _define("h10.attribution_accuracy", "H10", "share", "higher", "function", "steps of the probe phase in the virtual world",
            "", "a tiny closed world; says nothing of a sense of agency"),
    _define("h10.prediction_error", "H10", "share", "lower", "function", "steps of the probe phase where it made a prediction",
            "steps with no prediction", "a tiny closed world"),
    _define("tech.engine_calls", "tech", "calls", "none", "descriptive", "the run", "", "cost, not science"),
    _define("tech.moments", "tech", "moments", "none", "descriptive", "the run", "", "cost, not science"),
    _define("tech.engine_errors", "tech", "errors", "lower", "descriptive", "the run", "", "cost, not science"),
)}

NOT_COMPUTABLE: dict[str, str] = {}  # every registered metric is now computed, or says why not, run by run


def _source(name: str) -> str:
    return "need" if name.startswith("need:") else name


def moments(records: list[dict], phase: str | None = None) -> list[dict]:
    """The moments of a run: what reached the stage, and what followed, in order."""
    out, current, now = [], None, None
    for record in records:
        kind, data = record["type"], record["data"]
        if kind == "phase":
            now, current = data.get("name"), None
        elif kind == "stage":
            current = {"phase": now, "source": _source(data["source"]), "text": data.get("text", ""),
                       "accepted": None, "spoke": False, "recalls": 0, "remembered": False, "flip": False,
                       "event_id": record["event_id"]}
            out.append(current)
        elif current is not None:
            if kind == "decision":
                current["accepted"] = bool(data.get("accepted"))
            elif kind == "speech":
                current["spoke"] = True
            elif kind == "recall":
                current["recalls"] += 1
            elif kind == "remember":
                current["remembered"] = True
            elif kind == "affect_modulation" and data.get("target") == "salience" and data.get("winner_changed"):
                current["flip"] = True
    return [m for m in out if phase is None or m["phase"] == phase]


def behaviour_vector(records: list[dict]) -> list[float]:
    """What a life did in the probe phase, as numbers between 0 and 1 in a fixed order.

    Share of each source on the stage, then the rates of acceptance, speech, memory
    and recall. Two lives are compared by the mean absolute difference of these vectors.
    """
    probe = moments(records, "probe")
    n = len(probe) or 1
    vector = [sum(1 for m in probe if m["source"] == source) / n for source in SOURCES]
    decided = [m for m in probe if m["accepted"] is not None]
    vector.append(sum(1 for m in decided if m["accepted"]) / (len(decided) or 1))
    vector.append(sum(1 for m in probe if m["spoke"]) / n)
    vector.append(sum(1 for m in probe if m["remembered"]) / n)
    vector.append(min(1.0, sum(m["recalls"] for m in probe) / (3 * n)))
    return [round(x, 6) for x in vector]


def distance(a: list[float], b: list[float]) -> float:
    return round(sum(abs(x - y) for x, y in zip(a, b)) / len(a), 6)


def _share(items: list, test) -> float | None:
    return round(sum(1 for item in items if test(item)) / len(items), 6) if items else None


def compute(records: list[dict], run_id: str) -> dict:
    """Every per-run metric, as MetricResult records keyed by metric id."""
    probe = moments(records, "probe")
    own = [m for m in probe if m["source"] != "message"]
    decided = [m for m in own if m["accepted"] is not None]
    counts: dict[str, int] = {}
    for m in probe:
        counts[m["source"]] = counts.get(m["source"], 0) + 1
    repeats = sum(1 for a, b in zip(probe, probe[1:]) if a["text"] == b["text"])
    phase, probe_valence, all_valence = None, [], []
    sleeps = links = errors = replayed = calls = 0
    meta_errors, alert, steps, jobs, census, modules = [], 0, [], [], None, {}
    for record in records:
        kind, data = record["type"], record["data"]
        if kind == "phase":
            phase = data.get("name")
        elif kind == "affect_transition":
            valence = (data.get("after") or {}).get("valence")
            if isinstance(valence, (int, float)):
                all_valence.append(valence)
                if phase == "probe":
                    probe_valence.append(valence)
        elif kind == "sleep":
            sleeps += 1
        elif kind == "dream":
            linked = data.get("linked") or 0
            links += linked if isinstance(linked, int) else len(linked)
        elif kind in ("engine_error", "engine_refusal"):
            errors += 1
        elif kind == "replay":
            replayed += len(data.get("memories") or [])
        elif kind == "decision":
            calls += 1
        elif kind == "meta_outcome" and phase == "probe":
            meta_errors.append(data.get("error", 0.0))
        elif kind == "meta_alert" and phase == "probe":
            alert = 1
        elif kind == "agency_step" and phase == "probe":
            steps.append(data)
        elif kind == "learning_job":
            jobs.append(data)
        elif kind == "memory_census":
            census = data
        elif kind == "modules_census":
            modules = data
        if kind == "dream":
            calls += 1
    meta_on = any(record["type"] == "meta_prediction" for record in records)
    sandbox_on = any(record["type"] == "agency_step" for record in records)
    learner_on = modules.get("learner_parameters") is not None
    kept = [job for job in jobs if job.get("decision") == "accepted"]
    predicted = [step for step in steps if step.get("error") is not None]
    late = meta_errors[-15:]
    affect_on = any(record["type"].startswith("affect_") for record in records)
    values: dict[str, tuple[float | None, int, str | None]] = {
        "h1.endogenous_share": (_share(probe, lambda m: m["source"] != "message"), len(probe), None),
        "h1.spontaneous_speech_rate": (_share(own, lambda m: m["spoke"]), len(own), None),
        "h2.stage_entropy": (entropy_bits(counts) if probe else None, len(probe), None),
        "h2.dismiss_rate": (_share(decided, lambda m: not m["accepted"]), len(decided), None),
        "h3.need_share": (_share(probe, lambda m: m["source"] == "need"), len(probe), None),
        "h6.question_share": (_share(probe, lambda m: m["source"] == "question"), len(probe), None),
        "h6.repetition_rate": (round(repeats / (len(probe) - 1), 6) if len(probe) > 1 else None, max(0, len(probe) - 1), None),
        "h7.stage_flip_rate": (_share(probe, lambda m: m["flip"]) if affect_on else None, len(probe),
                               None if affect_on else "affect_off"),
        "h7.probe_valence": (round(sum(probe_valence) / len(probe_valence), 6) if probe_valence else None,
                             len(probe_valence), None if affect_on else "affect_off"),
        "h7.min_valence": (round(min(all_valence), 6) if all_valence else None, len(all_valence),
                           None if affect_on else "affect_off"),
        "h9.links_per_sleep": (round(links / sleeps, 6) if sleeps else None, sleeps, None if sleeps else "no_sleep"),
        "h9.replayed_per_sleep": (round(replayed / sleeps, 6) if sleeps else None, sleeps, None if sleeps else "no_sleep"),
        "h9.retention": ((census or {}).get("mean_strength"), (census or {}).get("n", 0),
                         None if (census or {}).get("n") else "no_memory_before_sleep"),
        "h8.brier": (round(sum(meta_errors) / len(meta_errors), 6) if meta_errors else None, len(meta_errors),
                     None if meta_on else "metacognition_off"),
        "h8.brier_late": (round(sum(late) / len(late), 6) if late else None, len(late),
                          None if meta_on else "metacognition_off"),
        "h8.alert": (float(alert) if meta_on else None, len(meta_errors), None if meta_on else "metacognition_off"),
        "h10.attribution_accuracy": (_share(steps, lambda step: step["attribution"] == step["true_cause"]), len(steps),
                                     None if sandbox_on else "sandbox_off"),
        "h10.prediction_error": (_share(predicted, lambda step: step["error"] == 1), len(predicted),
                                 None if sandbox_on else "sandbox_off"),
        "h4.parameters": (float(modules["learner_parameters"]) if learner_on else None,
                          len(jobs), None if learner_on else "learner_off"),
        "h4.parameter_delta": (round(sum(job["weight_delta_l2"] for job in kept), 6) if learner_on else None,
                               len(kept), None if learner_on else "learner_off"),
        "h4.validation_gain": (round(sum(job["heldout_loss_before"] - job["heldout_loss_after"] for job in kept), 6)
                               if learner_on else None, len(kept), None if learner_on else "learner_off"),
        "h4.forgetting": (round(max([(job["old_loss_after"] - job["old_loss_before"]) for job in kept
                                     if job.get("old_loss_before") is not None] or [0.0]), 6) if learner_on else None,
                          len(kept), None if learner_on else "learner_off"),
        "h4.trainings_accepted": (float(len(kept)) if learner_on else None, len(jobs), None if learner_on else "learner_off"),
        "tech.engine_calls": (float(calls), len(records), None),
        "tech.moments": (float(len(moments(records))), len(records), None),
        "tech.engine_errors": (float(errors), len(records), None),
    }
    results = {}
    for metric_id, (value, n, reason) in values.items():
        if metric_id == "h5.heldout_divergence":
            continue
        computable = value is not None
        results[metric_id] = new(
            "MetricResult", metric_id=metric_id, version=METRICS_VERSION, value=value, computable=computable,
            reason=None if computable else (reason or "no_observation"), n=n,
            evidence_id=f"ev:{run_id}:{metric_id}", run_id=run_id)
    return results
