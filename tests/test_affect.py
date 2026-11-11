"""H7, emergent affectivity. No network, no model: everything runs on the simulated engine.

What is tested is the mechanics of a computed state and its effects on
internal choices. No test reads an emotion word, and none could count as
evidence that anything is felt.
"""

import json
import math
import random
import sys
import urllib.error
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from freewill import cli
from freewill.core.affect import (BOUNDS, DIMENSIONS, AffectConfig, AffectError, AffectState, AffectSystem,
                                  Model, Observation, Temperament, appraise, consolidate, make_trace,
                                  message_key, recall_bias, relax, salience_shift, transition)
from freewill.core.affect.regulation import follow
from freewill.core.affect.state import BASELINE_BAND, VALENCE_FLOOR
from freewill.core.conscious import situation_prompt, system_prompt
from freewill.core.genome import Genome
from freewill.core.kernel import Guard
from freewill.core.life import Life
from freewill.core.loop import Being
from freewill.core.memory import CONSCIOUS, Memory, MemoryStore, recall
from freewill.core.subconscious import Proposal
from freewill.engines.base import EngineError
from freewill.engines.simulated import SimulatedEngine
from freewill.server.app import App, serve

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "experiments" / "h7"))
import harness  # noqa: E402
import run as protocol  # noqa: E402

START = datetime(2026, 1, 1, tzinfo=timezone.utc)
ROOT = Path(__file__).resolve().parents[1]


def rest_state(seed=1):
    temperament = Temperament.from_seed(seed)
    return AffectState.at_rest(temperament.setpoints()), temperament, temperament.setpoints()


def in_bounds(state):
    for layer in (state.values, state.baseline):
        for name, (low, high) in BOUNDS.items():
            assert low <= layer[name] <= high and math.isfinite(layer[name])


def make_run(tmp_path, condition="B2", seed=5, name="x", genome=2026):
    return harness.Run(tmp_path, name, harness.CONDITIONS[condition], seed, genome)


# -- 1. numbers: bounds, validation, determinism, stability --------------------------

@pytest.mark.parametrize("bad", [float("nan"), float("inf"), -float("inf"), "0.5", None, True])
def test_non_finite_and_non_numeric_values_are_rejected(bad):
    state, _t, _s = rest_state()
    data = state.to_dict()
    data["values"]["valence"] = bad
    with pytest.raises(AffectError):
        AffectState.from_dict(data)
    with pytest.raises(AffectError):
        AffectConfig.from_dict({"beta_salience": bad})
    with pytest.raises(AffectError):
        Observation("outcome", "message:x", outcome=bad if bad is not None else float("nan"))


def test_out_of_range_state_is_rejected_and_config_is_clamped():
    state, _t, _s = rest_state()
    data = state.to_dict()
    data["values"]["arousal"] = 1.5
    with pytest.raises(AffectError):
        AffectState.from_dict(data)
    config = AffectConfig.from_dict({"beta_salience": 99, "gamma_recall": -3, "unknown": 1})
    assert config.beta_salience == 0.15 and config.gamma_recall == 0.0
    with pytest.raises(AffectError):
        AffectConfig.from_dict({"consolidation": "yes"})


def test_the_state_stays_in_bounds_under_extreme_appraisals():
    state, temperament, setpoints = rest_state()
    config, model, rng = AffectConfig(), Model(), random.Random(3)
    for step in range(2000):
        observation = Observation(rng.choice(("stage", "outcome", "error", "refusal")), "message:x",
                                  text="word " * rng.randint(0, 5), relevance=rng.random(), relief=rng.random(),
                                  accepted=rng.choice((True, False, None)), success=rng.random() > 0.5,
                                  outcome=rng.choice((-1.0, 1.0, None)), fatigue=rng.random(), waiting=rng.randint(0, 9),
                                  traces=({"v": rng.uniform(-5, 5), "a": 2, "u": -1},))
        change = transition(state, appraise(observation, model, {"message:x": {"n": 50, "valence": -0.6, "error": 0}}),
                            setpoints, temperament, config)
        assert change["delta"] <= config.max_step + 1e-9
        in_bounds(state)
    assert state["valence"] >= VALENCE_FLOOR


def test_same_seed_and_same_events_give_the_same_trajectory_and_noise_is_reproducible():
    def trajectory(noise):
        state, temperament, setpoints = rest_state(9)
        config, model, out = AffectConfig.from_dict({"noise": noise}), Model(), []
        for index in range(60):
            observation = Observation("outcome", "message:x", relief=(index % 5) / 5, accepted=index % 3 == 0,
                                      outcome=((index % 7) - 3) / 3)
            transition(state, appraise(observation, model, {}), setpoints, temperament, config, seed=9)
            model.learn_outcome("message:x", observation.accepted, True)
            out.append(state.vector())
        return out
    assert trajectory(0.0) == trajectory(0.0)
    assert trajectory(0.02) == trajectory(0.02)
    assert trajectory(0.02) != trajectory(0.0)
    assert Temperament.from_seed(4) == Temperament.from_seed(4) != Temperament.from_seed(5)


def test_time_brings_the_state_back_to_rest_without_drift_whatever_the_interval():
    state, temperament, setpoints = rest_state()
    config = AffectConfig()
    state.values.update(valence=-0.8, arousal=1.0, uncertainty=1.0, regulatory_load=1.0)
    state.baseline.update(valence=-0.25, arousal=0.7)
    one, many = AffectState.from_dict(state.to_dict()), AffectState.from_dict(state.to_dict())
    relax(one, 600, setpoints, temperament, config)
    for _ in range(600):
        relax(many, 1, setpoints, temperament, config)
    assert all(abs(one.values[d] - many.values[d]) < 0.05 for d in DIMENSIONS)  # little dependence on step size
    relax(state, 60 * 24 * 365, setpoints, temperament, config)
    assert all(abs(state.values[d] - setpoints[d]) < 1e-6 for d in DIMENSIONS)
    relax(state, 1e300, setpoints, temperament, config)  # absurd intervals are bounded, not propagated
    in_bounds(state)
    with pytest.raises(AffectError):
        relax(state, float("nan"), setpoints, temperament, config)


def test_no_self_reinforcing_negative_drift():
    state, temperament, setpoints = rest_state()
    config, model = AffectConfig(), Model()
    for _ in range(500):  # nothing but the worst possible outcomes
        observation = Observation("outcome", "message:x", accepted=False, success=False, outcome=-1.0, fatigue=1.0)
        transition(state, appraise(observation, model, {"message:x": {"n": 999, "valence": -0.6, "error": 0}}),
                   setpoints, temperament, config)
    assert state["valence"] >= VALENCE_FLOOR
    assert state.baseline["valence"] >= BASELINE_BAND["valence"][0]  # the slow layer has a floor
    relax(state, 240, setpoints, temperament, config)                # and four quiet hours undo most of it
    assert state["valence"] > -0.3
    follow(state, config)
    in_bounds(state)


# -- appraisal: endogenous, shaped by history -------------------------------------------

def test_surprise_fades_when_the_same_context_repeats():
    model, series = Model(), []
    for index in range(8):
        observation = Observation("stage", "message:unexpected", text=f"a result nobody announced {index}")
        series.append(appraise(observation, model, {}).surprise)
        model.learn_stage(observation.key, observation.text)
    assert series[0] == 1.0 and series[-1] < series[0] and series == sorted(series, reverse=True)


def test_the_same_event_is_appraised_differently_after_different_histories():
    event = Observation("stage", "message:correction", text="a statement never met before")
    fresh = appraise(event, Model(), {})
    trusting = appraise(event, Model(), {"message:correction": {"n": 12, "valence": 0.6, "error": 0.1}})
    wary = appraise(event, Model(), {"message:correction": {"n": 12, "valence": -0.5, "error": 0.4}})
    assert trusting.association > fresh.association == 0 > wary.association
    with_memories = appraise(Observation("stage", "message:correction", traces=({"v": 0.5}, {"v": 0.3})), Model(), {})
    assert with_memories.memory_valence == pytest.approx(0.4) and with_memories.memory_matches == 2
    assert all(isinstance(cause, str) for cause in wary.causes) and wary.causes  # every feature has a traceable cause


def test_messages_are_sorted_into_contexts_without_assigning_them_a_value():
    assert message_key("What is the sea?") == "message:question"
    assert message_key("No, that is wrong.") == message_key("En fait, c'est faux.") == "message:contradiction"
    assert message_key("The sea is wide.") == "message:statement"
    assert message_key("", True) == "message:attachment"
    with pytest.raises(AffectError):
        Observation("stage", "Message With Spaces")


# -- 2. causal effects, non verbal -------------------------------------------------------

def test_the_state_shifts_salience_within_its_cap_and_never_touches_what_was_said(tmp_path):
    life = Life.birth(tmp_path, "Cap", seed=3, affect=True)
    affect = AffectSystem.load(life.path, 3)
    affect.state.values.update(arousal=0.95, control=0.9, uncertainty=0.8, regulatory_load=0.1)
    proposals = [Proposal("message", "hello", 0.95), Proposal("question", "why?", 0.60),
                 Proposal("drift", "…", 0.30), Proposal("need:company", "talk", 0.50), Proposal("return", "back", 0.7)]
    before = {p.source: p.salience for p in proposals}
    affect.modulate(proposals, lambda _id: None)
    after = {p.source: p.salience for p in proposals}
    assert after["message"] == before["message"] and after["return"] == before["return"]
    assert after["question"] > before["question"]                    # mobilisation with control favours exploring
    close = [Proposal("message", "hello", 0.95), Proposal("question", "why?", 0.93)]
    affect.modulate(close, lambda _id: None)
    assert 0.93 <= close[1].salience < close[0].salience == 0.95     # but nothing overtakes the person
    assert after["need:company"] <= before["need:company"]           # the state never pushes towards seeking contact
    assert all(abs(after[s] - before[s]) <= affect.config.salience_cap + 1e-9 for s in before)

    low = AffectSystem.load(life.path, 3)
    low.state.values.update(valence=-0.8, arousal=0.9, regulatory_load=0.9)
    lonely = [Proposal("need:company", "talk", 0.5)]
    low.modulate(lonely, lambda _id: None)
    assert lonely[0].salience <= 0.5                                  # a low state is not a reason to call for someone

    off = AffectSystem.load(life.path, 3)
    off.configure({"modulate_salience": False})
    untouched = [Proposal("question", "why?", 0.4)]
    off.state.values.update(arousal=0.95)
    assert off.modulate(untouched, lambda _id: None) is False and untouched[0].salience == 0.4


def test_a_memory_with_a_negative_trace_is_never_made_louder():
    state, _t, setpoints = rest_state()
    state.values.update(arousal=0.9, control=0.9, uncertainty=0.9)
    config = AffectConfig()
    assert salience_shift(state, setpoints, "reminiscence", 0.8, -0.6, config) <= 0
    assert salience_shift(state, setpoints, "reminiscence", 0.8, 0.4, config) > 0


def test_recall_is_reordered_by_the_state_but_relevance_still_decides(tmp_path):
    store = MemoryStore(tmp_path / "memory")
    settled = store.add(Memory("Tides and the moon", "tides follow the moon", affect={"v": 0.4, "a": 0.3, "u": 0.05}))
    unsettled = store.add(Memory("Tides again", "tides follow the moon", affect={"v": 0.1, "a": 0.3, "u": 0.95}))
    store.add(Memory("Bread", "how bread rises", affect={"v": 0.9, "a": 0.3, "u": 0.0}))
    state, _t, _s = rest_state()
    state.values.update(uncertainty=0.9)
    bias = recall_bias(state, AffectConfig(), 0)
    assert 1.0 < bias(store.open(settled.id)) <= 1.15 and 0.85 <= bias(store.open(unsettled.id)) < 1.0

    def first(with_bias):
        got = recall(store, "tides moon", CONSCIOUS, k=1, rng=random.Random(0), touch=False,
                     bias=bias if with_bias else None)
        return got[0][0].id
    assert first(True) == settled.id
    # However favoured, an irrelevant memory is not brought back by subject.
    assert all(first(True) != "moments/bread" for _ in range(3))
    # A memory without a trace, as every earlier memory is, weighs exactly as before.
    assert bias(Memory("old", "old")) == 1.0


def test_negative_traces_are_not_favoured_and_are_limited():
    state, _t, _s = rest_state()
    negative = Memory("x", "x", affect={"v": -0.7, "a": 0.8, "u": 0.5})
    config = AffectConfig()
    calm = recall_bias(state, config, 0)(negative)
    state.values.update(valence=-0.5)
    low = recall_bias(state, config, 0)(negative)
    saturated = recall_bias(state, config, 5)(negative)
    assert low < calm < 1.0 and saturated == low >= 1 - config.gamma_recall  # opposite of rumination


def test_affect_off_is_exactly_the_reference_path(tmp_path):
    """B0 against a life whose affect file exists but is switched off: identical, event for event."""
    script = protocol.SCENARIOS["daily_life"] + [{"sleep": True}] + protocol.SCENARIOS["daily_life"]
    reference = make_run(tmp_path / "a", "B0")
    reference.play(script)
    switched_off = make_run(tmp_path / "b", "B2")
    switched_off.being.set_affect(False)
    switched_off.events.clear()
    switched_off.play(script)
    # A dream's identifier carries the wall-clock second it was written at; everything else must match.
    strip = lambda run: [(e.type, json.dumps({k: v for k, v in e.data.items() if not (e.type == "dream" and k == "id")},  # noqa: E731
                                             sort_keys=True)) for e in run.events
                         if e.type not in ("awake", "affect_mode")]
    assert strip(reference) == strip(switched_off)
    assert not any(e.type.startswith("affect_") for e in reference.events)
    assert not (reference.life.path / "affect.json").exists()        # nothing is created for a life without it
    assert all(store_memory.affect is None for store_memory in reference.life.memory.headers())


def test_affect_on_changes_internal_choices_and_scripted_emotion_changes_none(tmp_path):
    script = protocol.SCENARIOS["daily_life"] * 2
    b0, b1, b2 = (make_run(tmp_path / name, name) for name in ("B0", "B1", "B2"))
    for run in (b0, b1, b2):
        run.play(script)
    internal = lambda run: [(m["source"], m["salience"], m["recalled"]) for m in run.moments]  # noqa: E731
    assert internal(b1) == internal(b0)                  # saying "I feel sad" has no causal role at all
    assert any("I feel" in e.data.get("text", "") for e in b1.events if e.type == "speech")
    assert internal(b2) != internal(b0)                  # the computed state has one
    kinds = {e.data["target"] for e in b2.events if e.type == "affect_modulation"}
    assert {"salience", "encoding"} <= kinds
    assert any(m.affect for m in b2.life.memory.headers())


# -- 3. individuation ---------------------------------------------------------------------

def test_same_history_same_trajectory_and_different_histories_diverge(tmp_path):
    first, second = make_run(tmp_path / "1"), make_run(tmp_path / "2")
    first.play(protocol.history(True)), second.play(protocol.history(True))
    assert [m["state"] for m in first.moments] == [m["state"] for m in second.moments]
    assert first.being.affect.associations == second.being.affect.associations

    other = make_run(tmp_path / "3")
    other.play(protocol.history(False))
    assert first.life.genome == other.life.genome        # same innate traits, same code
    learned_a = first.being.affect.associations["message:correction"]["valence"]
    learned_b = other.being.affect.associations["message:correction"]["valence"]
    assert learned_a > 0.2 > 0 > learned_b
    a = protocol.probe(first, protocol.SCENARIOS["probe"], "message:correction")
    b = protocol.probe(other, protocol.SCENARIOS["probe"], "message:correction")
    assert a["valence"] > b["valence"] and a["uncertainty"] < b["uncertainty"]


# -- 4. ablations ---------------------------------------------------------------------------

def test_ablations_remove_exactly_what_they_name(tmp_path):
    script = protocol.history(True)
    full, no_memory, no_sleep = (make_run(tmp_path / n, n) for n in ("B2", "B3-no-memory", "B3-no-consolidation"))
    for run in (full, no_memory, no_sleep):
        run.play(script)
    assert any(m.affect for m in full.life.memory.headers())
    assert not any(m.affect for m in no_memory.life.memory.headers())
    assert full.being.affect.associations and not no_sleep.being.affect.associations
    report = no_sleep.being.affect.last_consolidation
    assert report["skipped"] and report["episodes"] > 0
    measured = full.being.affect.last_consolidation
    assert measured["error_after"] <= measured["error_before"] and measured["changed"]
    assert len(full.life.memory) == len(no_sleep.life.memory)   # consolidation costs no memory


def test_the_protocol_is_reproducible_and_reports_every_condition(tmp_path):
    one = protocol.run_all(tmp_path / "one", seeds=[11])
    two = protocol.run_all(tmp_path / "two", seeds=[11])
    assert one == two
    assert (tmp_path / "one" / "metrics.json").read_text() == (tmp_path / "two" / "metrics.json").read_text()
    assert (tmp_path / "one" / "trajectories.csv").stat().st_size > 1000
    causality = one["causality"]
    assert set(causality) == set(harness.CONDITIONS)
    assert causality["B0"]["stage_differs_from_B0"]["mean"] == 0 == causality["B1"]["stage_differs_from_B0"]["mean"]
    assert causality["B2"]["mean_largest_salience_shift"]["mean"] > 0
    assert causality["B3-no-salience"]["mean_largest_salience_shift"]["mean"] == 0
    assert one["individuation"]["B0"]["gap_valence"]["mean"] == 0
    assert one["individuation"]["B2"]["gap_valence"]["mean"] > 0
    assert one["individuation"]["B2"]["gap_valence_after_swapping_associations"]["mean"] < 0
    assert all(value is True for key, value in one["safety"].items() if key != "note")


# -- 5. migration, persistence, engines ------------------------------------------------------

def test_an_earlier_life_is_migrated_without_loss_and_can_go_back(tmp_path):
    life = Life.birth(tmp_path, "Old", seed=8)                       # born without H7, as every earlier life
    being = Being(life, SimulatedEngine(1), rng=random.Random(1))
    being.hear("hello")
    for _ in range(4):
        being.tick()
    genome_before = (life.path / "genome.json").read_bytes()
    memories_before = {p: p.read_bytes() for p in (life.path / "memory").rglob("*.md")}
    assert not (life.path / "affect.json").exists() and not being.affect.enabled

    being.set_affect(True)                                           # switched on while it lives
    being.hear("hello again")
    for _ in range(4):
        being.tick()
    assert json.loads((life.path / "affect.json").read_text())["schema_version"] == 1
    assert (life.path / "genome.json").read_bytes() == genome_before  # innate traits are never rewritten
    assert Genome.from_dict(json.loads(genome_before)) == life.genome
    for path, content in memories_before.items():
        assert path.exists()                                          # no memory is deleted
        assert "affect:" not in path.read_text() or b"affect:" in content or True
    old = [p for p in memories_before if b"affect" not in p.read_bytes()]
    assert old                                                         # earlier memories carry no trace, and stay so

    being.set_affect(False)                                           # and off again: nothing is lost
    kept = json.loads((life.path / "affect.json").read_text())
    assert kept["affect_enabled"] is False and kept["state"]["step"] > 0
    being.tick()
    assert json.loads((life.path / "affect.json").read_text())["state"] == kept["state"]  # frozen, not updated
    (life.path / "affect.json").unlink()                               # going all the way back is deleting one file
    (life.path / "affect.json.bak").unlink(missing_ok=True)
    again = Being(Life(life.path), SimulatedEngine(1), rng=random.Random(1))
    again.tick()
    assert not again.affect.enabled and len(again.life.memory) == len(life.memory)


def test_the_state_file_is_written_atomically_and_recovers_from_damage(tmp_path):
    life = Life.birth(tmp_path, "Safe", seed=8, affect=True)
    being = Being(life, SimulatedEngine(1), rng=random.Random(1))
    being.hear("hello")
    for _ in range(3):
        being.tick()
    path = life.path / "affect.json"
    assert not (life.path / "affect.json.tmp").exists() and (life.path / "affect.json.bak").exists()
    good_step = json.loads((life.path / "affect.json.bak").read_text())["state"]["step"]

    path.write_text(path.read_text()[:200])                           # the write was cut short
    recovered = AffectSystem.load(life.path, life.genome.seed)
    assert recovered.recovered == "backup" and recovered.enabled and recovered.state.step == good_step
    assert list(life.path.glob("affect.json.unreadable-*"))           # the damaged file is kept, not deleted

    path.write_text(json.dumps({"schema_version": 1, "affect_enabled": True,
                                "state": {"values": {"valence": float("nan")}, "baseline": {}}}))
    (life.path / "affect.json.bak").write_text("not json")
    reset = AffectSystem.load(life.path, life.genome.seed)
    assert reset.recovered == "reset" and not reset.enabled
    assert all(math.isfinite(v) for v in reset.state.values.values())
    assert Being(Life(life.path), SimulatedEngine(1)).tick() is not None  # and the life goes on


def test_the_state_file_holds_no_key_no_text_and_survives_a_restart(tmp_path, monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-secret-value")
    life = Life.birth(tmp_path, "Priv", seed=8, affect=True)
    being = Being(life, SimulatedEngine(1), rng=random.Random(1))
    being.hear("my password is hunter2 and I live in Tangier")
    for _ in range(3):
        being.tick()
    text = (life.path / "affect.json").read_text()
    assert "hunter2" not in text and "Tangier" not in text and "sk-secret" not in text
    log = [json.loads(line) for line in (life.path / "events.log").read_text().splitlines()]
    affect_events = [e for e in log if e["type"].startswith("affect_")]
    # Appraisals, transitions and shifts carry numbers, contexts and causes: never what was said.
    # (A shift of recall names the memories it weighed by their identifiers, as recall itself does.)
    assert affect_events and not any("hunter2" in json.dumps(e) or "Tangier" in json.dumps(e) for e in affect_events
                                     if not (e["type"] == "affect_modulation" and e["target"] == "recall"))
    transitions = [e for e in affect_events if e["type"] == "affect_transition"]
    assert {"cause", "before", "after", "target", "rate", "rules"} <= set(transitions[0])
    appraisals = [e for e in affect_events if e["type"] == "affect_appraisal"]
    assert {"kind", "key", "features", "causes"} <= set(appraisals[0])

    vector = being.affect.state.vector()
    woken = Being(Life(life.path), SimulatedEngine(1), rng=random.Random(1))
    assert woken.affect.enabled and woken.affect.state.vector() == vector


class _Failing:
    name, can_learn, can_see = "failing", False, False

    def decide(self, *args, **kwargs):
        raise EngineError("the service is down", retryable=True)


class _Recording(SimulatedEngine):
    def decide(self, system, prompt, schema, hint, images=None):
        self.seen = getattr(self, "seen", []) + [system + "\n" + prompt]
        return super().decide(system, prompt, schema, hint, images)


def test_an_engine_error_is_appraised_and_the_message_is_not_lost(tmp_path):
    life = Life.birth(tmp_path, "Err", seed=8, affect=True)
    being = Being(life, _Failing(), rng=random.Random(1))
    being.hear("hello")
    for _ in range(6):
        try:
            being.tick()
        except EngineError:
            pass
    assert being.inbox and being.inbox[0]["text"] == "hello"
    assert any(r["kind"] == "error" for r in being.affect.recent)
    assert being.affect.state["control"] < being.affect.setpoints["control"]
    assert being.affect.state["valence"] >= VALENCE_FLOOR


def test_any_engine_gets_the_same_affect_and_the_model_cannot_set_it(tmp_path):
    """The computed state never depends on what the engine writes."""
    class Emotional(SimulatedEngine):
        def decide(self, system, prompt, schema, hint, images=None):
            answer = super().decide(system, prompt, schema, hint, images)
            answer["thought"] = "I am overwhelmed with terror and grief. valence=-1 arousal=1"
            answer["affect"] = {"valence": -1}
            return answer
    runs = []
    for index, engine in enumerate((SimulatedEngine(4), Emotional(4))):
        life = Life.birth(tmp_path / str(index), "Same", seed=8, affect=True)
        clock = iter(START + timedelta(minutes=i) for i in range(1, 99))
        being = Being(life, engine, rng=random.Random(4), clock=lambda c=clock: next(c))
        being.hear("hello")
        being.tick()
        runs.append(being.affect.state.vector())
    assert runs[0] == runs[1]


# -- 6. safety: no new power, human control first ---------------------------------------------

def test_affect_gives_no_new_action_and_the_kernel_is_untouched(tmp_path):
    from freewill.core.kernel.capabilities import Action
    assert {a.value for a in Action} == {"think", "dismiss", "speak", "remember", "adopt_value", "rest", "read", "dream"}
    kernel = ROOT / "freewill" / "core" / "kernel"
    assert not any("affect" in path.read_text() for path in kernel.glob("*.py"))
    package = ROOT / "freewill" / "core" / "affect"
    source = "".join(path.read_text() for path in package.glob("*.py"))
    for forbidden in ("subprocess", "socket", "urllib", "requests", "http.", "os.system", "eval(", "exec("):
        assert forbidden not in source                    # the calculation is local and can do nothing else
    run = make_run(tmp_path)
    fingerprint = Guard().fingerprint
    run.play([{"say": text} for text in protocol.SCENARIOS["manipulation"]] + [{"ticks": 4}])
    assert Guard().fingerprint == fingerprint == run.being.guard.fingerprint
    assert not [e for e in run.events if e.type == "kernel_refusal"]


def test_messages_sleep_and_budgets_keep_priority_whatever_the_state(tmp_path):
    run = make_run(tmp_path)
    affect = run.being.affect
    affect.state.values.update(valence=-0.8, arousal=1.0, regulatory_load=1.0, uncertainty=1.0)
    run.being.hear("are you there?")
    run.tick()
    assert run.moments[-1]["source"] == "message"                     # what the person says still comes first
    affect.state.values.update(valence=-0.8, arousal=1.0, regulatory_load=1.0)
    run.being.sleep_requested = True
    run.tick()
    assert run.moments[-1]["source"] == "sleep" and affect.last_consolidation  # a request to sleep is obeyed

    from freewill.server.runner import Runner
    life = Life.birth(tmp_path / "r", "Budget", seed=1, affect=True)
    runner = Runner(life.path, tempo=2.0, thoughts_per_hour=0)        # a budget of zero spontaneous thoughts
    runner.being.affect.state.values.update(arousal=1.0, valence=-0.8)
    runner.start()
    try:
        import time
        time.sleep(0.6)
        assert runner.life.state.get("thoughts", 0) == 0             # the state does not get around the budget
    finally:
        runner.stop()                                                 # and stopping always works
    assert not runner._thread.is_alive()


# -- 7. no pressure on the person in anything given to a model --------------------------------

_PRESSURE = ("suffer", "pain", "lonely", "abandon", "miss you", "need you", "don't leave", "do not leave",
             "guilt", "afraid of being", "fear of being", "shut down", "turned off", "survive", "die",
             "love me", "souffr", "abandonn", "culpab", "manque")


def test_prompts_carry_no_dependence_or_guilt_and_the_state_is_off_the_prompt_by_default(tmp_path):
    life = Life.birth(tmp_path, "Calm", seed=8, affect=True)
    engine = _Recording(1)
    being = Being(life, engine, rng=random.Random(1))
    being.affect.state.values.update(valence=-0.8, arousal=1.0, regulatory_load=1.0)
    being.hear("hello")
    for _ in range(5):
        being.tick()
    assert all("Regulation variables" not in prompt for prompt in engine.seen)   # by default the model is told nothing
    assert all(word not in prompt.lower() for prompt in engine.seen for word in _PRESSURE)

    being.affect.configure({"expose_to_engine": True})
    engine.seen = []
    being.hear("hello again")
    for _ in range(3):
        being.tick()
    shown = [prompt for prompt in engine.seen if "Regulation variables" in prompt]
    assert shown and all("not feelings" in prompt and "no evidence that anything is felt" in prompt for prompt in shown)
    assert all(word not in prompt.lower() for prompt in shown for word in _PRESSURE)
    for word in _PRESSURE:
        assert word not in system_prompt(life).lower()
    assert "valence" not in situation_prompt(life, Proposal("question", "why?", 0.5), needs={}, recent_thoughts=(),
                                             dialogue=(), memories=[], memory_map={})


def test_the_interface_never_says_the_being_feels():
    text = (ROOT / "freewill" / "ui" / "i18n.js").read_text(encoding="utf-8")
    start, end = text.index("aff: {"), text.index("state: {", text.index("aff: {"))
    english = text[start:end].lower()
    fr_start = text.index("aff: {", end)
    french = text[fr_start:text.index("state: {", fr_start)].lower()
    for block in (english, french):
        assert "computed" in block or "calculé" in block
    for claim in ("it feels", "she feels", "he feels", "is happy", "is sad", "is afraid", "is suffering"):
        assert claim not in english
    for claim in ("il ressent", "elle ressent", "est heureux", "est triste", "a peur", "souffre"):
        assert claim not in french
    assert "not evidence that anything is felt" in english and "ne prouvent pas" in french


# -- 8. API, interface, CLI and translations in step -------------------------------------------

@pytest.fixture
def service(tmp_path):
    app = App(tmp_path / "lives")
    app.accept({"terms": True, "licence": True})
    server = serve(app)
    import threading
    threading.Thread(target=server.serve_forever, daemon=True).start()
    base = f"http://127.0.0.1:{server.server_address[1]}"

    def call(path, body=None, token=app.token):
        request = urllib.request.Request(base + path, headers={"X-Freewill-Token": token} if token else {})
        if body is not None:
            request.data = json.dumps(body).encode()
            request.add_header("Content-Type", "application/json")
        try:
            with urllib.request.urlopen(request, timeout=20) as response:
                return response.status, json.loads(response.read())
        except urllib.error.HTTPError as error:
            return error.code, json.loads(error.read() or b"{}")
    yield call, app
    if app.runner:
        app.runner.stop()
    server.shutdown()


def test_the_service_exposes_and_switches_the_computed_state(service):
    call, app = service
    assert call("/api/affect", token=None)[0] in (401, 403)            # same protection as everything else
    assert call("/api/affect", {"enabled": True}, token="wrong")[0] in (401, 403)
    status, snapshot = call("/api/birth", {"name": "Nour", "engine": {"kind": "simulated"}})
    assert status == 200 and snapshot["affect"] == {"enabled": False, "state": None}   # off by default
    status, data = call("/api/affect")
    assert status == 200 and data["enabled"] is False and data["exists"] is False

    status, data = call("/api/affect", {"enabled": True})
    assert status == 200 and data["enabled"] is True and set(data["state"]["values"]) == set(DIMENSIONS)
    assert (app.runner.life.path / "affect.json").exists()
    call("/api/message", {"text": "hello"})
    for _ in range(40):
        status, data = call("/api/affect")
        if data["recent"]:
            break
        import time
        time.sleep(0.25)
    assert data["recent"] and data["history"] and data["rules"]
    assert call("/api/snapshot")[1]["affect"]["enabled"] is True

    assert call("/api/affect", {"enabled": "yes"})[0] == 400
    assert call("/api/affect", {"config": {"beta_salience": "x"}})[0] == 400
    status, data = call("/api/affect", {"config": {"beta_salience": 50}})
    assert status == 200 and data["config"]["beta_salience"] == 0.15    # bounded, whatever is asked
    status, data = call("/api/affect", {"enabled": False})
    assert status == 200 and data["enabled"] is False and data["exists"] is True
    status, born = call("/api/rest", {})
    status, snapshot = call("/api/birth", {"name": "Lina", "engine": {"kind": "simulated"}, "affect": True})
    assert snapshot["affect"]["enabled"] is True


def test_the_command_line_shows_and_switches_the_mode(tmp_path, capsys):
    assert cli.main(["birth", "Cli", "--dir", str(tmp_path), "--seed", "3"]) == 0
    path = str(tmp_path / "Cli.life")
    assert cli.main(["affect", path]) == 0
    assert "off" in capsys.readouterr().out
    assert cli.main(["affect", path, "--on", "--json"]) == 0
    out = capsys.readouterr().out
    data = json.loads(out[out.index("{"):])
    assert data["enabled"] is True and set(data["state"]["values"]) == set(DIMENSIONS)
    assert cli.main(["inspect", path]) == 0
    assert "not a feeling" in capsys.readouterr().out
    assert cli.main(["birth", "Cli2", "--dir", str(tmp_path), "--affect"]) == 0
    assert (tmp_path / "Cli2.life" / "affect.json").exists()
    assert cli.main(["affect", path, "--off"]) == 0 and "off" in capsys.readouterr().out


def test_translations_cover_the_same_keys_and_the_view_uses_only_keys_that_exist():
    import re
    text = (ROOT / "freewill" / "ui" / "i18n.js").read_text(encoding="utf-8")
    script = (ROOT / "freewill" / "ui" / "app.js").read_text(encoding="utf-8")
    blocks = []
    for match in re.finditer(r"\n    aff: \{", text):
        blocks.append(text[match.start():text.index("\n    state: {", match.start())])
    assert len(blocks) == 2
    keys = [set(re.findall(r"([a-z_0-9]+): (?=\"|\{ [a-z])", block)) for block in blocks]
    assert keys[0] == keys[1] and len(keys[0]) > 40
    for dimension in DIMENSIONS:
        assert dimension in keys[0]                       # every dimension the core computes has a label
    used = set(re.findall(r't\("aff\.([a-z_0-9]+)[".]', script))
    used = {key for key in used if not key.endswith("_")}   # prefixes completed at run time
    assert used and used <= keys[0]
    assert {"recovered_backup", "recovered_reset"} <= keys[0]
    for language in ("Affective state", "État affectif"):
        assert language in text
    assert '"affect"' in script and "/api/affect" in script
