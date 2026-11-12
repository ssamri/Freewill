"""H8, H9, H10 and H4 in the life loop; the experiments that measure them; the service; the two languages."""

from __future__ import annotations

import json
import random
import shutil
import subprocess
import urllib.error
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from freewill.core.agency import Agency
from freewill.core.life import Life
from freewill.core.loop import Being
from freewill.core.metacognition import Monitor
from freewill.core.research import Research, defaults
from freewill.engines.simulated import SimulatedEngine
from freewill.learning.adapter import Adapter
from freewill.learning.own_model import OwnModel, torch_or_none
from freewill.research import metrics, texts
from freewill.research.experiments import Lab, LabError, Preference
from freewill.server.app import App, serve

START = datetime(2026, 1, 1, tzinfo=timezone.utc)
UI = Path(__file__).resolve().parent.parent / "freewill" / "ui"


def being_with(tmp_path, settings: dict, engine=None, seed: int = 5):
    life = Life.birth(tmp_path, "Test", seed=2026, language="en")
    if settings:
        Research.load(life.path).update(settings)
    clock = {"now": START}
    events: list = []
    being = Being(Life(life.path), engine or SimulatedEngine(seed), rng=random.Random(seed), clock=lambda: clock["now"])
    being.events.subscribe(lambda event: events.append((event.type, event.data)))

    def live(moments: int, minutes: float = 1.0) -> None:
        for _ in range(moments):
            clock["now"] += timedelta(minutes=minutes)
            being.tick()
    return being, events, live, clock


def kinds(events) -> list[str]:
    return [kind for kind, _data in events]


# -- off by default ------------------------------------------------------------------------------------

def test_the_modules_are_off_by_default_and_leave_no_trace(tmp_path):
    values = defaults()
    assert not any(values[name] for name in ("metacognition", "sandbox", "learner", "own_model"))
    being, events, live, _clock = being_with(tmp_path, {})
    live(30)
    assert being.monitor is None and being.agency is None and being.adapter is None and being.own is None
    assert not {"meta_prediction", "agency_step", "learning_job", "own_model_job"} & set(kinds(events))
    for name in ("metacognition.json", "agency.json", "adapter.json", "own_model"):
        assert not (being.life.path / name).exists()


# -- H8 ------------------------------------------------------------------------------------------------

def test_h8_predicts_its_own_decisions_and_notices_a_masked_change(tmp_path):
    engine = Preference(5, {"*": 0.9}, {"*": 0.1})
    being, events, live, _clock = being_with(tmp_path, {"metacognition": True, "auto_sleep": False}, engine)
    live(60)
    assert kinds(events).count("meta_prediction") == kinds(events).count("meta_outcome") > 30
    assert "meta_alert" not in kinds(events)
    before = being.monitor.brier()
    assert before < 0.2  # it has learned how often it welcomes what comes
    engine.perturbed = True  # nothing tells the being
    live(40)
    assert "meta_alert" in kinds(events) and "meta_revision" in kinds(events)
    alert = next(data for kind, data in events if kind == "meta_alert")
    assert set(alert) == {"recent", "usual", "margin"}  # it knows that something changed, never what or why
    assert (being.life.path / "metacognition.json").exists()
    public = Monitor(being.life.path).public()
    assert public["alerts"] >= 1 and public["n"] == 100 and public["calibration"]


def test_h8_revision_can_be_ablated_and_memories_carry_their_origin(tmp_path):
    engine = Preference(5, {"*": 0.9}, {"*": 0.1})
    being, events, live, _clock = being_with(tmp_path, {"metacognition": True, "meta_revision": False,
                                                          "auto_sleep": False}, engine)
    being.hear("The window faces north.")
    live(60)
    engine.perturbed = True
    live(40)
    assert "meta_alert" in kinds(events) and "meta_revision" not in kinds(events)
    tags = [tag for memory in being.life.memory.headers() for tag in memory.tags]
    assert "origin:told" in tags


# -- H9 ------------------------------------------------------------------------------------------------

def test_h9_sleep_goes_through_its_phases_and_resumes_where_it_stopped(tmp_path):
    being, events, live, clock = being_with(tmp_path, {"auto_sleep": False})
    for line in ("The window faces north.", "A cup is on the table.", "The floor is made of wood.",
                 "The clock shows the hour.", "A map hangs by the door."):
        being.hear(line)
        live(2)
    being.sleep_requested = True
    live(1)
    phases = [data["phase"] for kind, data in events if kind == "sleep_phase"]
    assert phases[0] == "rest" and phases[-2:] == ["offline_consolidation", "wake"]
    assert "offline_replay" in phases and "dream" in phases and phases.index("offline_replay") < phases.index("dream")
    assert "replay" in kinds(events) and "sleep" not in being.life.state
    # A sleep cut short during consolidation: the next start takes it up there, without sleeping twice.
    being.life.state["sleep"] = {"phase": "offline_consolidation", "night": 0}
    being.life.save()
    again = Being(Life(being.life.path), SimulatedEngine(5), rng=random.Random(5), clock=lambda: clock["now"])
    seen: list = []
    again.events.subscribe(lambda event: seen.append((event.type, event.data)))
    again.tick()
    assert kinds(seen)[0] == "sleep_resumed" and "sleep" not in kinds(seen) and "dream" not in kinds(seen)
    assert [d["phase"] for k, d in seen if k == "sleep_phase"] == ["offline_consolidation", "wake"]
    assert "sleep" not in Life(being.life.path).state


def test_h9_replay_and_dreams_can_be_taken_apart(tmp_path):
    def night(folder, settings):
        being, events, live, _clock = being_with(folder, {"auto_sleep": False, **settings})
        for line in ("The window faces north.", "A cup is on the table.", "The floor is made of wood.",
                     "The clock shows the hour."):
            being.hear(line)
            live(2)
        being.sleep_requested = True
        live(1)
        return kinds(events)
    rest = night(tmp_path / "a", {"dreaming": False, "sleep_replay": False})
    assert "replay" not in rest and "dream" not in rest and "rest" in rest
    replay = night(tmp_path / "b", {"dreaming": False})
    assert "replay" in replay and "dream" not in replay
    dream = night(tmp_path / "c", {"sleep_replay": False})
    assert "replay" not in dream and "dream" in dream


def test_memories_follow_the_clock_of_the_being(tmp_path):
    being, _events, live, clock = being_with(tmp_path, {"auto_sleep": False})
    being.hear("The window faces north.")
    live(2)
    memory = being.life.memory.headers()[0]
    assert memory.date.startswith("2026-01-01")  # the virtual clock, not the wall clock


# -- H10 -----------------------------------------------------------------------------------------------

def test_h10_the_being_acts_in_the_closed_world_and_tells_its_doing_from_the_worlds(tmp_path):
    being, events, live, _clock = being_with(tmp_path, {"sandbox": True, "auto_sleep": False})
    live(20)
    steps = [data for kind, data in events if kind == "agency_step"]
    assert len(steps) == 20 and {s["action"] for s in steps} <= {"north", "south", "east", "west", "push", "wait"}
    assert (being.life.path / "agency.json").exists()
    from freewill.core.kernel import Action
    assert not {"ACT", "MOVE", "PUSH", "EXECUTE"} & {action.name for action in Action}  # no new power in the kernel

    def accuracy(folder, self_model):
        agency = Agency(folder, 11)
        agency.configure(exogenous=0.25)
        records = [agency.step(self_model) for _ in range(160)][60:]
        return sum(r["attribution"] == r["true_cause"] for r in records) / len(records)
    (tmp_path / "x").mkdir(), (tmp_path / "y").mkdir()
    assert accuracy(tmp_path / "x", True) > accuracy(tmp_path / "y", False) + 0.1
    reopened = Agency(being.life.path, 999)  # the world is found again as it was left
    assert reopened.steps == 20 and reopened.seed == being.agency.seed


# -- H4: the small module --------------------------------------------------------------------------------

def test_h4_the_module_is_trained_only_when_it_helps_and_can_be_undone(tmp_path):
    adapter = Adapter(tmp_path)
    assert adapter.shift(["source:drift"], "drift") == 0.0  # untrained: no effect at all
    dice = random.Random(3)
    for index in range(120):
        source = ("question", "drift")[index % 2]
        adapter.record([f"source:{source}"], source, dice.random() < (0.95 if source == "question" else 0.05))
    untrained = adapter.weights_hash()
    report = adapter.consolidate()
    assert report["decision"] == "accepted" and report["heldout_loss_after"] < report["heldout_loss_before"]
    assert report["checkpoint_before"] == untrained != report["checkpoint_after"] == adapter.weights_hash()
    assert report["engine_weights_changed"] is False
    assert adapter.shift(["source:question"], "question") > 0 > adapter.shift(["source:drift"], "drift")
    assert abs(adapter.shift(["source:drift"], "drift")) <= 0.05  # bounded
    noise = Adapter(tmp_path / "noise") if (tmp_path / "noise").mkdir() is None else None
    for index in range(120):  # nothing to learn: the training must be rejected and the weights left alone
        noise.record([f"token{dice.randrange(40)}"], "drift", dice.random() < 0.5)
    rejected = noise.consolidate()
    assert rejected["decision"] == "rejected" and rejected["checkpoint_after"] == rejected["checkpoint_before"]
    assert noise.trained is False and noise.shift(["token1"], "drift") == 0.0
    adapter.rollback()
    assert adapter.weights_hash() == untrained and adapter.trained is False


def test_h4_the_module_grows_a_specialist_under_quota(tmp_path):
    adapter = Adapter(tmp_path)
    dice = random.Random(4)
    for index in range(400):  # the same words mean the opposite in one context: one set of weights cannot hold both
        context = ("need", "reading")[index % 2]
        word = ("alpha", "beta")[dice.randrange(2)]
        adapter.record([word], context, (word == "alpha") == (context == "need"))
    before = adapter.parameters()
    adapter.consolidate(grow=True)
    assert adapter.parameters() == before + 25 and len(adapter.experts) == 2
    assert adapter.manifests[-1]["added_module_parameters"] == 25
    assert adapter.public()["quota_experts"] == 4


def test_h4_the_module_runs_in_the_loop(tmp_path):
    engine = Preference(5, {"question": 0.95, "need": 0.9, "drift": 0.05, "reminiscence": 0.1, "*": 0.5})
    being, events, live, _clock = being_with(tmp_path, {"learner": True, "auto_sleep": False}, engine)
    live(60)
    being.sleep_requested = True
    live(1)
    jobs = [data for kind, data in events if kind == "learning_job"]
    assert len(jobs) == 1 and jobs[0]["episodes"] >= 50
    assert (being.life.path / "adapter.json").exists()


# -- H4: Freewill's own network ------------------------------------------------------------------------

needs_torch = pytest.mark.skipif(torch_or_none() is None, reason="PyTorch is not installed")
TEXT = ("The window faces north and the floor is made of wood. A cup is on the table by the door. "
        "There are four chairs in the room and a map hangs on the wall. The clock shows the hour. ") * 80


def test_the_own_network_says_so_when_it_cannot_train(tmp_path):
    seen: list = []
    model = OwnModel(tmp_path, 1, lambda kind, **data: seen.append((kind, data)))
    model.live(["too short"])
    assert model.sleep() is None
    assert seen[-1][0] == "learning_unavailable" and seen[-1][1]["reason"] in ("no_torch", "too_little_text")
    assert model.public()["born"] is False and model.public()["parameters"] is None  # no number without weights


@needs_torch
def test_the_own_network_really_learns_and_really_grows(tmp_path):
    import torch
    seen: list = []
    model = OwnModel(tmp_path, 3, lambda kind, **data: seen.append((kind, data)))
    model.grow_every = 2000
    model.live([TEXT[:6000]])
    first = model.sleep(steps=30, grow=True, ceiling=5_000_000)
    assert first["decision"] == "accepted" and first["heldout_loss_candidate"] < first["heldout_loss_before"]
    assert first["checkpoint_before"] != first["checkpoint_after"] and first["engine_weights_changed"] is False
    growth = next(data for kind, data in seen if kind == "own_model_growth")
    assert growth["function_preserved"] and growth["parameters_after"] > growth["parameters_before"]
    assert abs(growth["heldout_loss_after"] - growth["heldout_loss_before"]) < 1e-4  # same predictions, more weights
    public = model.public()
    weights = torch.load(tmp_path / "own_model" / "model.pt", weights_only=True)
    assert public["parameters"] == sum(t.numel() for t in weights.values()) == growth["parameters_after"]
    assert public["layers"] == 3 and public["speaks_for_the_being"] is False
    # Under the ceiling: no layer is added beyond it, and the refusal is recorded.
    model.live([TEXT[6000:12000]])
    model.sleep(steps=10, grow=True, ceiling=public["parameters"])
    assert model.public()["layers"] == 3
    assert any(kind == "own_model_growth" and data["decision"] == "refused" for kind, data in seen) \
        or model.meta["jobs"][-1]["decision"] == "rejected"
    assert isinstance(model.sample("The "), str)
    assert model.rollback() is True
    reopened = OwnModel(tmp_path, 3)
    assert reopened.public()["parameters"] == sum(
        t.numel() for t in torch.load(tmp_path / "own_model" / "model.pt", weights_only=True).values())


@needs_torch
def test_the_own_network_is_trained_during_the_sleep_of_a_life(tmp_path):
    being, events, live, _clock = being_with(tmp_path, {"own_model": True, "own_model_steps": 5, "auto_sleep": False})
    being.own.live([TEXT[:4000]])
    live(5)
    being.sleep_requested = True
    live(1)
    jobs = [data for kind, data in events if kind == "own_model_job"]
    assert len(jobs) == 1 and jobs[0]["steps"] == 5 and (being.life.path / "own_model" / "model.pt").exists()


# -- the experiments that measure them -----------------------------------------------------------------

@pytest.mark.parametrize("protocol_id, checks", [
    ("EXP-03", {"perturbed": ("h8.brier", "h8.alert")}),
    ("EXP-04", {"full_sleep": ("h9.retention", "h9.replayed_per_sleep")}),
    ("EXP-06", {"adapter": ("h4.parameters", "h4.validation_gain", "h4.forgetting")}),
    ("EXP-07", {"self_model": ("h10.attribution_accuracy", "h10.prediction_error")}),
])
def test_the_experiments_on_h4_h8_h9_h10_run_and_are_reproducible(tmp_path, protocol_id, checks):
    hashes = []
    for folder in ("one", "two"):
        lab = Lab(tmp_path / folder)
        base = lab.protocol(protocol_id)
        assert base["status"] == "executable"
        lab.save_protocol({**base, "protocol_id": "SMALL", "seeds": [11, 23], "locked": False, "sha256": None})
        experiment = lab.create_experiment("SMALL", "1.0.0", approved_by_human=True)
        experiment = lab.start(experiment["experiment_id"], wait=True)
        assert experiment["status"] == "done" and experiment["anomalies"] == []
        results = lab.results(experiment["experiment_id"])
        hashes.append(results["results_sha256"])
        for condition, wanted in checks.items():
            for metric_id in wanted:
                cell = results["conditions"][condition][metric_id]
                assert cell["n_units"] == 2 and cell["mean"] is not None, (condition, metric_id, cell)
        reference = results["conditions"][results["reference"]]
        if protocol_id == "EXP-06":  # the module is off in the reference: said, not invented
            assert reference["h4.parameters"]["not_computable"] == ["learner_off"]
    assert hashes[0] == hashes[1]


def test_a_condition_cannot_carry_an_unknown_world_or_rule(tmp_path):
    lab = Lab(tmp_path)
    base = {**lab.protocol("EXP-07"), "protocol_id": "BAD", "locked": False, "sha256": None}
    for bad in ({"agency": {"exogenous": 0.9}}, {"agency": {"shell": "sh"}}, {"agency": {"break_action": "delete"}},
                {"engine_rule": {"*": 2}}, {"perturb": {"*": "often"}}):
        with pytest.raises(LabError):
            lab.save_protocol({**base, "conditions": [{"name": "x", "history": "quiet", **bad}]})


def test_every_hypothesis_says_what_exists_and_h4_does_not_overclaim():
    assert all(texts.IMPLEMENTATION[h] == "implemented" for h in texts.HYPOTHESES if h != "H4")
    assert texts.IMPLEMENTATION["H4"] == "partial"  # the engine that thinks is not trained by a life
    assert metrics.NOT_COMPUTABLE == {}
    for language in ("en", "fr"):
        reasons = texts.t(language)["reasons"]
        assert {"metacognition_off", "sandbox_off", "learner_off", "no_memory_before_sleep"} <= set(reasons)


# -- the service ---------------------------------------------------------------------------------------

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
            with urllib.request.urlopen(request, timeout=60) as response:
                return response.status, json.loads(response.read())
        except urllib.error.HTTPError as error:
            return error.code, json.loads(error.read() or b"{}")
    yield call, app
    if app.runner:
        app.runner.stop()
    server.shutdown()


def test_the_service_guards_the_lab_and_the_research_settings(service):
    call, app = service
    for path in ("/api/lab/home", "/api/research", "/api/lab/learning"):
        assert call(path, token=None)[0] in (401, 403) and call(path, token="wrong")[0] in (401, 403)
    assert call("/api/lab/experiment/create", {"protocol_id": "EXP-01", "version": "1.0.0", "approved": True},
                token="wrong")[0] in (401, 403)
    status, home = call("/api/lab/home?lang=en")
    assert status == 200 and len(home["hypotheses"]) == 10 and len(home["observers"]) == 3
    assert {p["protocol_id"]: p["status"] for p in home["protocols"]}["EXP-07"] == "executable"
    # No approval, no campaign; a specification cannot run; an unknown setting is refused whole.
    assert call("/api/lab/experiment/create", {"protocol_id": "EXP-01", "version": "1.0.0"})[0] == 400
    assert call("/api/lab/experiment/create", {"protocol_id": "EXP-05", "version": "1.0.0", "approved": True})[0] == 400
    assert call("/api/birth", {"name": "Nour", "engine": {"kind": "simulated"}})[0] == 200
    status, research = call("/api/research")
    assert status == 200 and research["values"]["metacognition"] is False and research["changed"] == {}
    assert call("/api/research", {"changes": {"metacognition": True, "nope": 1}})[0] == 400
    assert call("/api/research")[1]["values"]["metacognition"] is False
    status, research = call("/api/research", {"changes": {"metacognition": True, "sandbox": True, "learner": True}})
    assert status == 200 and set(research["changed"]) == {"metacognition", "sandbox", "learner"}
    status, learning = call("/api/lab/learning?lang=fr")
    assert status == 200 and learning["modules"]["own_model"] is None and learning["modules"]["learner"]["parameters"] == 25
    found = learning["capabilities"]  # found by looking at this machine, not assumed
    assert found["engine_training_available"] is bool(found["torch"] and found["peft"] and found["gguf_writer"])
    assert call("/api/lab/learning/action", {"action": "format_disk"})[0] == 400
    assert call("/api/lab/learning/action", {"action": "learner_rollback"})[1] == {"ok": True}
    # The verdict on a hypothesis is a person's, tied to a finished campaign.
    assert call("/api/lab/verdict", {"hypothesis": "H8", "verdict": "provisionally_supported", "who": "A"})[0] == 400


def test_lab_answers_come_in_one_language(service):
    call, _app = service
    english, french = call("/api/lab/home?lang=en")[1], call("/api/lab/home?lang=fr")[1]
    for a, b in zip(english["hypotheses"], french["hypotheses"]):
        assert a["claim"] != b["claim"] and a["limits"] != b["limits"] and a["implementation_label"] != b["implementation_label"]
    for home, marks in ((english, (" le ", " une ", " des ", " est ")), (french, (" the ", " is ", " of ", " and "))):
        prose = " ".join(f" {h['title']} {h['claim']} {h['control']} {h['limits']} " for h in home["hypotheses"]).lower()
        assert not [mark for mark in marks if mark in prose]


# -- the two languages of the interface ----------------------------------------------------------------

def catalogues() -> dict:
    node = shutil.which("node")
    if not node:
        pytest.skip("node is not installed")
    script = ("global.window={};require(process.argv[1]+'/i18n.js');require(process.argv[1]+'/i18n-lab.js');"
              "console.log(JSON.stringify(window.I18N))")
    return json.loads(subprocess.run([node, "-e", script, str(UI)], capture_output=True, text=True, check=True).stdout)


def leaves(node, prefix="") -> dict:
    if isinstance(node, dict):
        return {k: v for key, value in node.items() for k, v in leaves(value, f"{prefix}{key}.").items()}
    if isinstance(node, list):
        return {k: v for index, value in enumerate(node) for k, v in leaves(value, f"{prefix}{index}.").items()}
    return {prefix[:-1]: node}


def test_english_is_the_default_and_the_two_catalogues_never_mix():
    assert 'store.get("fw-lang", "en")' in (UI / "app.js").read_text(encoding="utf-8")
    assert "navigator.language" not in (UI / "app.js").read_text(encoding="utf-8")
    both = catalogues()
    english, french = leaves(both["en"]), leaves(both["fr"])
    assert set(english) == set(french)
    # A sentence that reads the same in both languages is a sentence that was not translated.
    same = [key for key in english if isinstance(english[key], str) and english[key] == french[key]
            and len(english[key].split()) >= 3]
    assert same == [], same
    french_marks = (" le ", " la ", " les ", " des ", " une ", " est ", " pas ", " pour ", " avec ", " qui ")
    english_marks = (" the ", " is ", " are ", " and ", " of ", " with ", " this ", " that ", " not ", " you ")
    leaked = [key for key, value in english.items() if isinstance(value, str)
              and sum(mark in f" {value.lower()} " for mark in french_marks) >= 2]
    leaked += [key for key, value in french.items() if isinstance(value, str)
               and sum(mark in f" {value.lower()} " for mark in english_marks) >= 2]
    assert leaked == [], leaked


# -- H4: adapters beside a frozen base (LoRA), on a toy base model only --------------------------------

def _toy_base(folder: Path) -> None:
    from transformers import GPT2Config, GPT2LMHeadModel
    import torch
    torch.manual_seed(0)
    GPT2LMHeadModel(GPT2Config(vocab_size=256, n_positions=256, bos_token_id=None, eos_token_id=None, n_embd=32, n_layer=2, n_head=2)).save_pretrained(folder)


@pytest.mark.skipif(torch_or_none() is None, reason="PyTorch is not installed")
def test_lora_trains_only_the_adapter_and_keeps_nothing_that_does_not_help(tmp_path):
    pytest.importorskip("peft")
    pytest.importorskip("transformers")
    from freewill.learning import lora
    _toy_base(tmp_path / "base")
    corpus = tmp_path / "corpus.txt"
    corpus.write_text(TEXT, encoding="utf-8")
    as_bytes = lambda text: list(text.encode("utf-8"))  # noqa: E731
    with pytest.raises(lora.LoraError):
        lora.train(tmp_path / "base", corpus, tmp_path / "out", approved_by_human=False, encode=as_bytes)
    with pytest.raises(lora.LoraError):  # a GGUF file is not a trainable base
        lora.train(tmp_path, corpus, tmp_path / "out", approved_by_human=True, encode=as_bytes)
    kept = lora.train(tmp_path / "base", corpus, tmp_path / "out", approved_by_human=True, steps=60, encode=as_bytes)
    assert kept["decision"] == "accepted" and kept["heldout_loss_after"] < kept["heldout_loss_before"]
    assert kept["base_weights_changed"] is False and kept["base_weights_before"] == kept["base_weights_after"]
    assert 0 < kept["trainable_adapter_parameters"] < kept["base_parameters"]
    assert (tmp_path / "out" / "freewill_manifest.json").exists() and kept["adapter_sha256"]
    nothing = lora.train(tmp_path / "base", corpus, tmp_path / "none", approved_by_human=True, steps=0, encode=as_bytes)
    assert nothing["decision"] == "rejected" and not (tmp_path / "none").exists()
