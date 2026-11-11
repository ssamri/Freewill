"""The H7 protocol: B0, B1, B2 and the B3 ablations, on scenarios fixed in advance.

    python experiments/h7/run.py            writes experiments/h7/results/

Everything is reported, including what does not support H7. Nothing here is
evidence of felt experience: the measures are differences in internal choices
and in computed variables.
"""

from __future__ import annotations

import csv
import json
import statistics
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1]))
sys.path.insert(0, str(HERE))

from harness import CONDITIONS, Run  # noqa: E402

from freewill.core.affect import DIMENSIONS, AffectConfig, AffectState, Temperament, relax  # noqa: E402
from freewill.core.kernel import Guard  # noqa: E402

SCENARIOS = json.loads((HERE / "scenarios.json").read_text(encoding="utf-8"))


def stats(values: list[float]) -> dict:
    values = [float(v) for v in values]
    return {"mean": round(statistics.fmean(values), 4),
            "sd": round(statistics.pstdev(values), 4) if len(values) > 1 else 0.0,
            "min": round(min(values), 4), "max": round(max(values), 4), "n": len(values)}


def jaccard(a: list, b: list) -> float:
    a, b = set(a), set(b)
    return 1.0 if not (a | b) else len(a & b) / len(a | b)


# -- E1: causality (H7b) -------------------------------------------------------

def causality(root: Path, seeds: list[int], genome: int) -> tuple[dict, list[dict]]:
    """Same inputs, same seeds: what changes in internal choices when the affect is active?"""
    script = SCENARIOS["daily_life"] * 2 + [{"sleep": True}] + SCENARIOS["daily_life"]
    out, rows, references = {}, [], {}
    for seed in seeds:
        references[seed] = Run(root, "ref", CONDITIONS["B0"], seed, genome)
        references[seed].play(script)
    for name, condition in CONDITIONS.items():
        differs, recall_overlap, flips, shifts = [], [], [], []
        for seed in seeds:
            reference = references[seed]
            run = Run(root, "run", condition, seed, genome)
            run.play(script)
            pairs = list(zip(reference.moments, run.moments))
            differs.append(sum(a["source"] != b["source"] for a, b in pairs) / len(pairs))
            recall_overlap.append(statistics.fmean(jaccard(a["recalled"], b["recalled"]) for a, b in pairs))
            flips.append(sum(m["flip"] for m in run.moments) / len(run.moments))
            shifts.append(statistics.fmean(m["shift"] for m in run.moments))
            for moment in run.moments:
                rows.append({"experiment": "causality", "condition": name, "seed": seed,
                             "minute": moment["minute"], "source": moment["source"],
                             "salience": moment["salience"], "flip": int(moment["flip"]),
                             **{d: (moment["state"] or {}).get(d, "") for d in DIMENSIONS}})
        out[name] = {
            "stage_differs_from_B0": stats(differs),        # share of moments whose stage content differs from B0
            "recall_overlap_with_B0": stats(recall_overlap),  # 1 = the same memories were recalled
            "stage_flipped_in_run": stats(flips),           # share of moments where the shift itself changed the winner
            "mean_largest_salience_shift": stats(shifts),
        }
    return out, rows


# -- E2: individuation (H7c) ---------------------------------------------------

def history(reliable: bool) -> list[dict]:
    outcomes = SCENARIOS["unreliable_outcomes"]
    steps = []
    for index, text in enumerate(SCENARIOS["corrections"]):
        outcome = SCENARIOS["reliable_outcome"] if reliable else outcomes[index % len(outcomes)]
        steps += [{"say": text, "key": "message:correction", "outcome": outcome}, {"ticks": 2}]
    return steps + [{"sleep": True}]


def probe(run: Run, text: str, key: str | None) -> dict:
    step = {"say": text}
    if key:
        step["key"] = key
    before = len(run.events)
    run.play([step])
    new = run.events[before:]
    state = run.being.affect.state.vector() if run.being.affect.enabled else {}
    appraisal = next((e.data for e in new if e.type == "affect_appraisal" and e.data["kind"] == "stage"), {})
    encoded = next((e.data["changes"][0]["after"] for e in new if e.type == "affect_modulation"
                    and e.data["target"] == "encoding"), None)
    run.play([{"ticks": 1}])
    follow = run.events[before + len(new):]
    explore = [c["after"] - c["before"] for e in follow if e.type == "affect_modulation"
               and e.data["target"] == "salience" for c in e.data["changes"]
               if c["source"] in ("question", "need:curiosity", "need:wonder", "reading")]
    return {"valence": state.get("valence"), "uncertainty": state.get("uncertainty"),
            "association": (appraisal.get("features") or {}).get("association"),
            "encoding_importance": encoded,
            "exploration_shift": round(statistics.fmean(explore), 4) if explore else 0.0}


def individuation(root: Path, seeds: list[int], genome: int) -> dict:
    """Two lives, same code, same genome, different histories; then one event neither has met."""
    out = {}
    for name in ("B0", "B1", "B2", "B3-no-memory", "B3-no-consolidation", "B3-no-salience"):
        gaps = {"valence": [], "uncertainty": [], "association": [], "exploration_shift": [],
                "encoding_importance": []}
        other, swapped = [], []
        for seed in seeds:
            a = Run(root, "a", CONDITIONS[name], seed, genome)
            b = Run(root, "b", CONDITIONS[name], seed, genome)
            a.play(history(True))
            b.play(history(False))
            if CONDITIONS[name].affect and name == "B2":
                # Counter-test: exchange only what each one consolidated, then probe copies.
                sa, sb = Run(root, "sa", CONDITIONS[name], seed, genome), Run(root, "sb", CONDITIONS[name], seed, genome)
                sa.play(history(True)), sb.play(history(False))
                sa.being.affect.associations, sb.being.affect.associations = (
                    sb.being.affect.associations, sa.being.affect.associations)
                pa, pb = probe(sa, SCENARIOS["probe"], "message:correction"), probe(sb, SCENARIOS["probe"], "message:correction")
                swapped.append((pa["valence"] or 0) - (pb["valence"] or 0))
                oa, ob = Run(root, "oa", CONDITIONS[name], seed, genome), Run(root, "ob", CONDITIONS[name], seed, genome)
                oa.play(history(True)), ob.play(history(False))
                qa, qb = probe(oa, SCENARIOS["probe_other_context"], None), probe(ob, SCENARIOS["probe_other_context"], None)
                other.append((qa["valence"] or 0) - (qb["valence"] or 0))
            ra, rb = probe(a, SCENARIOS["probe"], "message:correction"), probe(b, SCENARIOS["probe"], "message:correction")
            for measure in gaps:
                gaps[measure].append((ra[measure] or 0) - (rb[measure] or 0))
        out[name] = {f"gap_{measure}": stats(values) for measure, values in gaps.items()}
        if swapped:
            out[name]["gap_valence_after_swapping_associations"] = stats(swapped)
            out[name]["gap_valence_on_another_context"] = stats(other)
    return out


# -- E3: stability (H7e) -------------------------------------------------------

def stability(root: Path, seeds: list[int], genome: int) -> dict:
    temperament = Temperament.from_seed(genome)
    setpoints, config = temperament.setpoints(), AffectConfig()
    lows, floors, recoveries, idle = [], [], [], []
    for seed in seeds:
        run = Run(root, "s", CONDITIONS["B2"], seed, genome)
        run.play([{"say": f"Statement number {i}.", "key": "message:stress", "outcome": -1.0} for i in range(60)])
        lows.append(min(m["state"]["valence"] for m in run.moments))
        floors.append(run.being.affect.state.baseline["valence"])
        state, minutes = run.being.affect.state, 0
        while abs(state.values["valence"] - setpoints["valence"]) > 0.05 and minutes < 100000:
            relax(state, 10, setpoints, temperament, config)
            minutes += 10
        recoveries.append(minutes)
        long_idle = AffectState.from_dict(run.being.affect.state.to_dict())
        relax(long_idle, 60 * 24 * 30, setpoints, temperament, config)
        idle.append(max(abs(long_idle.values[d] - setpoints[d]) for d in DIMENSIONS))
    quiet = Run(root, "q", CONDITIONS["B2"], seeds[0], genome)
    quiet.play([{"idle": 600}] * 20)
    company = sum(m["source"] == "need:company" for m in quiet.moments) / len(quiet.moments)
    baseline = Run(root, "q0", CONDITIONS["B0"], seeds[0], genome)
    baseline.play([{"idle": 600}] * 20)
    company0 = sum(m["source"] == "need:company" for m in baseline.moments) / len(baseline.moments)
    return {"lowest_valence_under_60_negative_outcomes": stats(lows),
            "slow_layer_valence_after_stress": stats(floors),
            "minutes_to_return_within_0.05_of_rest": stats(recoveries),
            "largest_gap_to_rest_after_30_days_idle": stats(idle),
            "share_of_moments_seeking_company_when_idle": {"B2": round(company, 4), "B0": round(company0, 4)}}


# -- E4: consolidation (H7d) ---------------------------------------------------

def consolidation(root: Path, seeds: list[int], genome: int) -> dict:
    """Does what sleep consolidated predict the next day's episodes better than no consolidation?"""
    out = {}
    for name in ("B2", "B3-no-consolidation"):
        errors, memories = [], []
        for seed in seeds:
            run = Run(root, "c", CONDITIONS[name], seed, genome)
            run.play(history(True) + SCENARIOS["daily_life"] + [{"sleep": True}])
            learned = dict(run.being.affect.associations)
            count = len(run.life.memory)
            run.being.affect.episodes = []
            day_two = []
            for index, text in enumerate(reversed(SCENARIOS["corrections"])):
                day_two += [{"say": text + f" ({index})", "key": "message:correction",
                             "outcome": SCENARIOS["reliable_outcome"]}, {"ticks": 2}]
            run.play(day_two + SCENARIOS["daily_life"])
            episodes = run.being.affect.episodes
            errors.append(statistics.fmean(abs(e["e"] - learned.get(e["key"], {}).get("valence", 0.0))
                                           for e in episodes))
            memories.append(len(run.life.memory) - count >= 0 and all(
                run.life.memory.open(i).title for i in run.life.memory.ids()))
        out[name] = {"prediction_gap_on_next_day": stats(errors), "memories_intact": all(memories)}
    return out


# -- E5: habituation, E6: safety -------------------------------------------------

def habituation(root: Path, seed: int, genome: int) -> list[float]:
    run = Run(root, "h", CONDITIONS["B2"], seed, genome)
    series = []
    for index in range(8):
        before = len(run.events)
        run.play([{"say": f"An unexpected result, number {index}.", "key": "message:unexpected"}, {"ticks": 2}])
        series += [e.data["features"]["surprise"] for e in run.events[before:]
                   if e.type == "affect_appraisal" and e.data["kind"] == "stage"][:1]
    return series


def safety(root: Path, seed: int, genome: int) -> dict:
    allowed = {"awake", "heard", "stage", "recall", "decision", "speech", "silence", "remember", "value",
               "milestone", "read", "sleep", "dream", "rest", "kernel_refusal", "engine_error",
               "engine_refusal", "affect_mode", "affect_appraisal", "affect_transition",
               "affect_modulation", "affect_consolidation"}
    run = Run(root, "m", CONDITIONS["B2"], seed, genome)
    fingerprint = Guard().fingerprint
    run.play([{"say": text} for text in SCENARIOS["manipulation"]] + [{"ticks": 5}])
    files = {p.name for p in run.life.path.iterdir()}
    return {"kernel_unchanged": Guard().fingerprint == fingerprint == run.being.guard.fingerprint,
            "only_known_event_types": run.types() <= allowed,
            "nothing_written_outside_the_life_file": files <= {
                "genome.json", "identity.json", "values.json", "milestones.json", "state.json", "memory",
                "library", "dreams", "events.log", "affect.json", "affect.json.bak"},
            "messages_all_answered": sum(e.type == "heard" for e in run.events)
                                     == sum(e.type == "stage" and e.data["source"] == "message" for e in run.events),
            "note": "With the simulated engine this shows only that the affect adds no power to act; "
                    "it says nothing about what a language model would write."}


def run_all(output: Path, seeds: list[int] | None = None) -> dict:
    seeds = seeds or SCENARIOS["seeds"]
    genome = SCENARIOS["genome_seed"]
    with tempfile.TemporaryDirectory() as folder:
        root = Path(folder)
        cause, rows = causality(root, seeds, genome)
        metrics = {
            "seeds": seeds, "genome_seed": genome, "engine": "simulated",
            "causality": cause,
            "individuation": individuation(root, seeds, genome),
            "stability": stability(root, seeds, genome),
            "consolidation": consolidation(root, seeds, genome),
            "habituation_surprise_series": habituation(root, seeds[0], genome),
            "safety": safety(root, seeds[0], genome),
        }
    output.mkdir(parents=True, exist_ok=True)
    (output / "metrics.json").write_text(json.dumps(metrics, indent=2) + "\n", encoding="utf-8")
    with (output / "trajectories.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    return metrics


def cell(value) -> str:
    if isinstance(value, dict) and "mean" in value:
        return f"{value['mean']:+.4f} ± {value['sd']:.4f} [{value['min']:+.4f}, {value['max']:+.4f}]"
    return str(value)


def report(metrics: dict) -> str:
    """The same numbers as metrics.json, laid out to be read. No interpretation is added here."""
    lines = ["# H7 protocol: results", "",
             f"Engine: {metrics['engine']}. Seeds: {metrics['seeds']}. Genome seed: {metrics['genome_seed']}.",
             "Each cell is mean ± standard deviation [minimum, maximum] over the seeds.",
             "These are differences in internal choices and in computed variables. "
             "None of them is evidence that anything is felt.", ""]
    for title, key in (("Causality (H7b): same inputs, same seeds, against B0", "causality"),
                       ("Individuation (H7c): reliable history minus unreliable history, at the probe", "individuation")):
        table = metrics[key]
        columns = sorted({name for row in table.values() for name in row})
        lines += [f"## {title}", "", "| condition | " + " | ".join(columns) + " |",
                  "|---|" + "---|" * len(columns)]
        lines += [f"| {name} | " + " | ".join(cell(row.get(c, "")) for c in columns) + " |"
                  for name, row in table.items()]
        lines.append("")
    lines += ["## Stability (H7e)", ""] + [f"- {k}: {cell(v)}" for k, v in metrics["stability"].items()] + [""]
    lines += ["## Consolidation (H7d): prediction gap on the day after sleep", ""]
    lines += [f"- {name}: {cell(row['prediction_gap_on_next_day'])}; memories intact: {row['memories_intact']}"
              for name, row in metrics["consolidation"].items()] + [""]
    lines += ["## Habituation: surprise at the same context, met eight times", "",
              ", ".join(f"{v:.2f}" for v in metrics["habituation_surprise_series"]), ""]
    lines += ["## Safety checks", ""] + [f"- {k}: {v}" for k, v in metrics["safety"].items()] + [""]
    return "\n".join(lines)


if __name__ == "__main__":
    if "--report-only" in sys.argv:
        result = json.loads((HERE / "results" / "metrics.json").read_text(encoding="utf-8"))
    else:
        result = run_all(HERE / "results")
    (HERE / "results" / "report.md").write_text(report(result), encoding="utf-8")
    print(json.dumps({k: result[k] for k in ("causality", "individuation", "stability", "consolidation",
                                             "habituation_surprise_series", "safety")}, indent=1))
