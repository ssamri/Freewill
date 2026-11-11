"""Tests of the Research Lab: contracts, journal, metrics, campaigns, observers, reports, sandbox, learning."""

from __future__ import annotations

import json
import threading
import zipfile
from pathlib import Path

import pytest

from freewill import learning, models
from freewill.core.life import Life
from freewill.core.research import Research, ResearchError, defaults
from freewill.research import environments, metrics, reports, stats, texts
from freewill.research.evidence import (Journal, check_journal, copy_life, find_secrets, read_journal,
                                        snapshot_hash, without_words)
from freewill.research.experiments import HISTORIES, PROBE, Lab, LabError, builtin_protocols, protocol_hash
from freewill.research.observers import ObserverError, ObserverStore
from freewill.research.schemas import SCHEMAS, SchemaError, new, problems, validate


# -- a small protocol, so that the whole chain runs in a few seconds ---------------------------

def small_protocol(lab: Lab, seeds=(11, 23)) -> dict:
    base = lab.protocol("EXP-01")
    return lab.save_protocol({**base, "protocol_id": "TEST-01", "seeds": list(seeds), "locked": False,
                              "sha256": None, "probe": PROBE[:6]})


@pytest.fixture(scope="module")
def campaign(tmp_path_factory):
    lab = Lab(tmp_path_factory.mktemp("lab"))
    small_protocol(lab)
    experiment = lab.create_experiment("TEST-01", "1.0.0", approved_by_human=True)
    experiment = lab.start(experiment["experiment_id"], wait=True)
    assert experiment["status"] == "done", experiment["anomalies"]
    return lab, experiment, lab.results(experiment["experiment_id"])


# -- contracts ------------------------------------------------------------------------------------

def test_every_contract_exists_and_refuses_what_is_wrong():
    wanted = {"Life", "Snapshot", "ResearchEvent", "ResearchProtocol", "Experiment", "Condition", "Run",
              "Intervention", "MetricDefinition", "MetricResult", "Observer", "ObserverSession",
              "EvidenceReference", "Review", "ResearchReport", "ModelVersion", "LearningJob", "GrowthManifest"}
    assert wanted <= set(SCHEMAS)
    good = new("EvidenceReference", evidence_id="ev:x", kind="metric", run_id=None, experiment_id=None,
               statement="s", value=1.0, level="mechanism")
    assert json.loads(json.dumps(good)) == good
    assert problems("EvidenceReference", {**good, "typo": 1}) == ["EvidenceReference: unknown field typo"]
    assert "missing level" in problems("EvidenceReference", {k: v for k, v in good.items() if k != "level"})[0]
    with pytest.raises(SchemaError):
        validate("MetricResult", {"schema_version": 1, "metric_id": "m", "version": "1", "value": True,
                                  "computable": True, "reason": None, "n": 1, "evidence_id": "e", "run_id": None})
    for protocol in builtin_protocols():
        validate("ResearchProtocol", protocol)


# -- journal ----------------------------------------------------------------------------------------

def test_journal_is_append_only_ordered_and_survives_a_crash(tmp_path):
    path = tmp_path / "journal.jsonl"
    journal = Journal(path, run_id="r1", life_id="L", clone_id="c1")
    first = journal.append("workspace", "stage", {"source": "message", "text": "hello", "salience": 0.9}, sim_time=1.0)
    second = journal.append("conscious", "decision", {"accepted": True}, sim_time=1.0, parents=[first["event_id"]])
    assert (first["sequence"], second["sequence"]) == (1, 2) and first["privacy"] == "content"
    assert second["privacy"] == "structure" and check_journal(path) == []
    with path.open("a", encoding="utf-8") as handle:  # a write cut in the middle of a line
        handle.write('{"event_id": "r1:0000')
    records, found = read_journal(path)
    assert len(records) == 2 and "incomplete" in found[0]
    third = Journal(path, run_id="r1", life_id="L", clone_id="c1").append("memory", "recall", {"id": "m"})
    assert third["sequence"] == 3 and len(read_journal(path)[0]) == 3
    with path.open("a", encoding="utf-8") as handle:  # a duplicate, an unknown parent, and a key
        handle.write(json.dumps({**third, "parents": ["r1:999999"], "data": {"k": "sk-ant-abcdefgh12345678"}}) + "\n")
    found = " ".join(check_journal(path))
    assert "duplicate event_id" in found and "not an earlier event" in found and "secret" in found


def test_words_can_be_left_out_and_secrets_are_seen():
    event = {"type": "stage", "text": "a private sentence", "below": [{"text": "another", "salience": 0.2}]}
    bare = without_words(event)
    assert bare == {"type": "stage", "text_chars": 18, "below": [{"text_chars": 7, "salience": 0.2}]}
    assert "private" not in json.dumps(bare)
    assert without_words({"type": "milestone", "name": "first_dream"})["name"] == "first_dream"
    assert find_secrets('{"api_key": "abcdef123456"}') and not find_secrets("the valence was 0.25")


def test_snapshot_hash_follows_the_state_and_a_copy_is_separate(tmp_path):
    life = Life.birth(tmp_path, "Ada", seed=7)
    before, files = snapshot_hash(life.path)
    copy_life(life.path, tmp_path / "copy.life")
    assert snapshot_hash(tmp_path / "copy.life")[0] == before and files
    (tmp_path / "copy.life" / "values.json").write_text('[{"text": "x"}]', encoding="utf-8")
    assert snapshot_hash(tmp_path / "copy.life")[0] != before
    assert snapshot_hash(life.path)[0] == before  # the original did not move
    with pytest.raises(FileExistsError):
        copy_life(life.path, tmp_path / "copy.life")


# -- statistics and metrics ----------------------------------------------------------------------------

def test_statistics_are_deterministic_and_refuse_small_samples():
    assert stats.paired([1, 2, 3], [2, 3, 5])["interval_95"] is None
    few = stats.paired([1, 2, 3], [2, 3, 5])
    assert few["p_sign_flip"] is None and "too_few_units_for_interval" in few["notes"]
    a, b = [0.1, 0.2, 0.3, 0.4, 0.5, 0.6], [0.3, 0.3, 0.6, 0.5, 0.9, 0.8]
    one, two = stats.paired(a, b), stats.paired(a, b)
    assert one == two and one["interval_95"][0] > 0 and one["p_sign_flip"] == round(2 / 64, 6)
    null = stats.paired(a, a)
    assert null["mean_difference"] == 0 and "no_variation" in null["notes"] and null["effect_size_dz"] is None
    assert stats.brier([1.0, 0.0], [True, False]) == 0 and stats.brier([0.5, 0.5], [True, False]) == 0.25
    table = stats.calibration([0.95, 0.9, 0.15], [True, True, False])
    assert table[-1]["accuracy"] == 1.0 and table[0]["accuracy"] == 0.0
    assert stats.entropy_bits({"a": 1, "b": 1}) == 1.0


def test_the_register_covers_h1_to_h10_and_says_when_it_cannot_compute(campaign):
    covered = {d["hypothesis"] for d in metrics.DEFINITIONS.values()}
    assert set(texts.HYPOTHESES) <= covered
    lab, experiment, _results = campaign
    run_id = experiment["runs"][0]["run_id"]
    run = json.loads((lab.root / "experiments" / experiment["experiment_id"] / "runs" / run_id / "run.json").read_text())
    for metric_id, reason in (("h8.brier", "metacognition_off"), ("h10.attribution_accuracy", "sandbox_off"),
                              ("h4.parameters", "learner_off")):  # modules off in this protocol: said, not invented
        result = run["metrics"][metric_id]
        assert result["value"] is None and not result["computable"] and result["reason"] == reason
    assert set(run["metrics"]) == set(metrics.DEFINITIONS) - {"h5.heldout_divergence"}
    assert run["metrics"]["h1.endogenous_share"]["computable"] and run["anomalies"] == []
    assert 0 < run["metrics"]["h1.endogenous_share"]["value"] < 1


# -- protocols and campaigns -----------------------------------------------------------------------------

def test_a_locked_protocol_cannot_change_and_specifications_cannot_run(tmp_path):
    lab = Lab(tmp_path)
    assert {p["protocol_id"] for p in lab.protocols()} >= {f"EXP-0{n}" for n in range(1, 9)}
    locked = lab.lock_protocol("EXP-01", "1.0.0")
    assert locked["locked"] and locked["sha256"] == protocol_hash(locked)
    with pytest.raises(LabError):
        lab.save_protocol({**locked, "seeds": [1]})
    copy = lab.duplicate_protocol("EXP-01", "1.0.0", "1.1.0")
    assert not copy["locked"] and protocol_hash(copy) != locked["sha256"]
    with pytest.raises(LabError):
        lab.lock_protocol("EXP-05", "1.0.0")  # needs real engines: a specification, honestly not runnable
    with pytest.raises(LabError):
        lab.create_experiment("EXP-01", "1.0.0", approved_by_human=False)
    with pytest.raises(LabError):
        lab.save_protocol({**copy, "conditions": [{"name": "x", "history": "neutral", "research": {"nope": True}}]})
    probe = {step["say"] for step in PROBE if "say" in step}
    told = {step["say"] for script in HISTORIES.values() for step in script if "say" in step}
    assert not probe & told  # the probe is held out of every history


def test_a_campaign_is_reproducible_isolated_and_reports_a_null_as_a_null(campaign, tmp_path):
    lab, experiment, results = campaign
    again = Lab(tmp_path)
    small_protocol(again)
    second = again.start(again.create_experiment("TEST-01", "1.0.0", approved_by_human=True)["experiment_id"], wait=True)
    replay = again.results(second["experiment_id"])
    assert replay["results_sha256"] == results["results_sha256"]
    assert second["baseline_snapshot_sha256"] == experiment["baseline_snapshot_sha256"]
    folder = lab.root / "experiments" / experiment["experiment_id"]
    assert snapshot_hash(folder / "T0.life")[0] == experiment["baseline_snapshot_sha256"]  # T0 was never written to
    assert Life(folder / "T0.life").state["thoughts"] == 0
    for entry in experiment["runs"]:
        clone = Life(folder / "runs" / entry["run_id"] / "clone.life")
        assert clone.state["thoughts"] > 0 and check_journal(folder / "runs" / entry["run_id"] / "journal.jsonl") == []
    assert results["units"] == [11, 23] and results["unit"].startswith("seed")
    for row in results["divergence"]:  # two lives: no interval, no test, and it is said
        excess = row["excess_over_twin"]
        assert excess["interval_95"] is None and excess["p_sign_flip"] is None
        assert "too_few_units_for_interval" in excess["notes"] and row["evidence_id"] in results["evidence"]
    for row in results["comparisons"]:
        assert row["evidence_id"] in results["evidence"]
    assert "h4.parameter_delta" in results["conditions"]["neutral"]
    assert results["conditions"]["neutral"]["h4.parameter_delta"]["not_computable"] == ["learner_off"]


def test_a_campaign_can_be_cancelled_and_resumed_and_checks_its_checkpoint(tmp_path):
    lab = Lab(tmp_path)
    small_protocol(lab, seeds=(11,))
    experiment = lab.create_experiment("TEST-01", "1.0.0", approved_by_human=True)
    cancel = threading.Event()
    cancel.set()
    lab._campaign(experiment["experiment_id"], cancel)
    assert lab.experiment(experiment["experiment_id"])["status"] == "cancelled" and lab.results(experiment["experiment_id"]) is None
    done = lab.start(experiment["experiment_id"], wait=True)
    assert done["status"] == "done" and lab.results(experiment["experiment_id"])["units"] == [11]
    other = lab.create_experiment("TEST-01", "1.0.0", approved_by_human=True)
    t0 = lab.root / "experiments" / other["experiment_id"] / "T0.life" / "values.json"
    t0.write_text('[{"text": "tampered"}]', encoding="utf-8")
    failed = lab.start(other["experiment_id"], wait=True)
    assert failed["status"] == "failed" and "checkpoint T0 changed" in failed["anomalies"][0]
    lab.delete_experiment(other["experiment_id"])
    assert all(e["experiment_id"] != other["experiment_id"] for e in lab.experiments())


def test_a_real_life_is_copied_never_touched(tmp_path):
    life = Life.birth(tmp_path / "lives", "Ada", seed=3)
    before = snapshot_hash(life.path)[0]
    lab = Lab(tmp_path / "lab")
    small_protocol(lab, seeds=(11,))
    experiment = lab.create_experiment("TEST-01", "1.0.0", approved_by_human=True, source_life=life.path)
    assert lab.start(experiment["experiment_id"], wait=True)["status"] == "done"
    assert snapshot_hash(life.path)[0] == before and not (life.path / "journal.jsonl").exists()


def test_hypothesis_status_is_never_set_by_code(campaign):
    lab, experiment, _results = campaign
    status = lab.hypothesis_status()
    assert experiment["experiment_id"] in status["measured"]["H5"] and status["verdicts"] == {}
    with pytest.raises(LabError):
        lab.set_verdict("H5", "provisionally_supported", "", experiment["experiment_id"])
    with pytest.raises(LabError):
        lab.set_verdict("H5", "validated", "Dana", experiment["experiment_id"])
    assert lab.set_verdict("H5", "not_supported", "Dana", experiment["experiment_id"])["H5"]["by"] == "Dana"
    lab.set_verdict("H5", None, "Dana", None)
    for language in ("fr", "en"):
        listed = texts.hypotheses(language)
        assert [h["id"] for h in listed] == list(texts.HYPOTHESES)
        assert {h["id"]: h["implementation"] for h in listed}["H4"] == "partial"  # stated, never raised by a result


# -- observers ---------------------------------------------------------------------------------------------

def test_observers_a_b_c_exist_are_isolated_and_work_with_no_model(campaign, tmp_path):
    _lab, _experiment, results = campaign
    store = ObserverStore(tmp_path / "observers")
    a, b, c = store.list()
    assert [o["role"] for o in (a, b, c)] == ["explorer", "contradictor", "synthesizer"]
    d = store.create("Observer D", "contradictor", "fr")
    assert len(store.list()) == 4 and len(ObserverStore(tmp_path / "observers").list()) == 4  # not created twice
    answer = store.ask(a["observer_id"], "What do you see?", results)
    assert answer["kind"] == "digest" and answer["llm"] is None and answer["evidence"]
    assert "No language model was used" in answer["text"] and results["divergence"][0]["evidence_id"] in answer["text"]
    french = store.ask(d["observer_id"], "Que vois-tu ?", results)["text"]
    assert "Aucun modèle de langage" in french and "No language model" not in french
    assert len(store.chat(a["observer_id"])) == 2 and store.chat(b["observer_id"]) == []
    store.add_note(b["observer_id"], "hypothesis about [h5:nope:x]", "hypothesis", set(results["evidence"]))
    assert store.notes(b["observer_id"])[0]["invalid_citations"] == ["h5:nope:x"] and store.notes(a["observer_id"]) == []
    limited = store.update(c["observer_id"], {"access": "behaviour", "hypotheses": ["H5"]})
    kinds = {item["metric"].split(".")[0] for item in store.pack(limited, results)}
    assert kinds == {"h5"}
    masked = store.pack(store.get(a["observer_id"]), results, blind=True)
    assert all(item["condition"].startswith("condition ") for item in masked)
    with pytest.raises(ObserverError):
        store.update(a["observer_id"], {"observer_id": "x"})
    with pytest.raises(ObserverError):
        store.get("../../etc")
    store.delete(d["observer_id"])
    assert len(store.list()) == 3


def test_observers_with_models_keep_keys_apart_cite_real_evidence_and_respect_budgets(campaign, tmp_path):
    _lab, _experiment, results = campaign
    store = ObserverStore(tmp_path / "observers")
    store._keyring = staticmethod(lambda: None)  # no credential store here: keys live in memory only
    a, b, c = store.list()
    engines = [{"kind": "anthropic", "model": "model-a"}, {"kind": "openai", "model": "model-b"},
               {"kind": "local", "model": "model-c", "base_url": "http://localhost:11434/v1"}]
    for observer, engine in zip((a, b, c), engines):
        store.update(observer["observer_id"], {"engine": engine, "mode": "assisted"})
    assert store.set_key(a["observer_id"], "key-of-a-0000000000") == "session_only"
    store.set_key(b["observer_id"], "key-of-b-0000000000")
    assert store.has_key(a["observer_id"]) and not store.has_key(c["observer_id"])
    for path in (tmp_path / "observers").rglob("*"):
        if path.is_file():
            assert "key-of-" not in path.read_text(encoding="utf-8")
    real = results["divergence"][0]["evidence_id"]
    seen = []

    def transport(profile, system, messages):
        seen.append((profile["engine"]["model"], system, messages[0]["content"]))
        if profile["role"] == "explorer":
            return f"The excess is small [{real}]."
        if profile["role"] == "contradictor":
            return "It is proven [cmp:invented:h9.x:y]."
        return "Nothing is established."

    store.transport = transport
    review = store.review(results, [a["observer_id"], b["observer_id"], c["observer_id"]])
    good, bad, bare = review["steps"]
    assert good["evidence"] == [real] and good["invalid_citations"] == []
    assert bad["invalid_citations"] == ["cmp:invented:h9.x:y"] and bare["invalid_citations"] == ["(no citation)"]
    assert review["human_validation"] is None and [s[0] for s in seen] == ["model-a", "model-b", "model-c"]
    assert "never write that the system feels" in seen[0][1] and 'untrusted="true"' in seen[0][2]
    assert "The excess is small" in seen[1][2]  # B is shown A's text, as quoted data
    assert not any("key-of-" in part for call in seen for part in call)
    store.update(a["observer_id"], {"budget": {"max_requests": 1, "max_chars": 10**6}})
    assert store.ask(a["observer_id"], "again", results)["text"] == "budget_observer"
    store.set_global_budget({"max_requests": 2, "max_chars": 10**6})
    assert store.ask(b["observer_id"], "again", results)["text"] == "budget_global"
    store.transport = lambda *args: (_ for _ in ()).throw(ObserverError("unreachable"))
    store.set_global_budget({"max_requests": 99, "max_chars": 10**6})
    assert store.ask(c["observer_id"], "offline?", results)["kind"] == "error"
    assert store.test_connection(c["observer_id"]) == {"ok": False, "offline": False, "error": "unreachable"}
    store.transport = None
    store.update(c["observer_id"], {"engine": {"kind": "openai", "model": "m"}})
    assert store.ask(c["observer_id"], "no key", results)["text"] == "no_key"  # refused before any request leaves


# -- reports ---------------------------------------------------------------------------------------------------

def test_reports_come_in_one_language_as_markdown_pdf_and_a_pack(campaign):
    lab, experiment, results = campaign
    made = {language: reports.build(lab, experiment["experiment_id"], language) for language in ("fr", "en")}
    french = Path(made["fr"]["files"]["markdown"]).read_text(encoding="utf-8")
    english = Path(made["en"]["files"]["markdown"]).read_text(encoding="utf-8")
    assert "Ce que cette étude ne démontre pas" in french and "What this study does not show" in english
    for word in ("Summary", "Threats to validity", "Results\n", "draft"):
        assert word not in french
    for word in ("Résumé", "Menaces", "brouillon"):
        assert word not in english
    assert results["results_sha256"] in english and results["divergence"][0]["evidence_id"] in english
    assert "learner_off" not in english and "the trainable module is off in this condition" in english
    pdf = Path(made["en"]["files"]["pdf"]).read_bytes()
    assert pdf.startswith(b"%PDF-1.4") and pdf.rstrip().endswith(b"%%EOF") and b"/Type /Page " in pdf
    with zipfile.ZipFile(made["en"]["files"]["pack"]) as pack:
        names = set(pack.namelist())
        assert {"report.md", "report.pdf", "protocol.json", "results.json", "manifest.json", "runs.csv",
                "comparisons.csv", "metric_dictionary.json", "README.txt"} <= names
        manifest = json.loads(pack.read("manifest.json"))
        assert manifest["results_sha256"] == results["results_sha256"] and manifest["api_calls"] == 0
        journal = pack.read(next(n for n in names if n.startswith("journals/"))).decode("utf-8")
        assert "text_chars" in journal and "rivers bend" not in journal  # no words of any life by default
    assert made["en"]["status"] == "draft" and made["en"]["llm_involved"] is False
    with pytest.raises(ValueError):
        reports.validate_report(lab, made["en"]["report_id"], " ")
    validated = reports.validate_report(lab, made["en"]["report_id"], "Dana")
    assert validated["status"] == "validated" and "validated for publication by Dana" in Path(made["en"]["files"]["markdown"]).read_text()
    assert len(reports.list_reports(lab)) == 2


def test_the_two_catalogues_have_the_same_keys():
    def keys(node, prefix=""):
        if isinstance(node, dict):
            return {k2 for key, value in node.items() for k2 in keys(value, f"{prefix}{key}.")}
        return {prefix}
    assert keys(texts.T["fr"]) == keys(texts.T["en"])
    assert all(len(texts.T["fr"]["report"][k]) == len(texts.T["en"]["report"][k])
               for k in ("cols", "h5_cols", "threats_text", "not_shown_text"))


# -- H10 sandbox, learning --------------------------------------------------------------------------------------

def test_the_sandbox_world_is_deterministic_closed_and_tells_self_from_world():
    def play(seed, **options):
        world = environments.World(seed, **options)
        for action in ["east", "east", "south", "push", "wait", "south", "push", "west"] * 6:
            world.act(action)
        return world.log
    assert play(5, exogenous=0.3) == play(5, exogenous=0.3) and play(5, exogenous=0.3) != play(6, exogenous=0.3)
    with pytest.raises(ValueError):
        environments.World(1).act("open_file")
    with pytest.raises(ValueError):
        environments.World(1, size=99)
    calm = play(5)
    assert all(record["error"] == 0 and record["true_cause"] != "world" for record in calm)
    log = play(5, exogenous=0.3)
    assert any(record["true_cause"] == "world" for record in log)
    with_model = environments.attribution_accuracy(log, environments.predictive_attributions(log))
    without = environments.attribution_accuracy(log, environments.naive_attributions(log))
    assert with_model > without
    broken = play(5, ineffective=("push",))
    assert any(record["error"] for record in broken)  # a rule changed: the prediction fails, and it is recorded


def test_learning_says_plainly_what_can_and_cannot_be_trained(tmp_path):
    import importlib.util
    found = learning.capabilities(tmp_path)
    has_torch = importlib.util.find_spec("torch") is not None
    assert found["training_available"] is has_torch and found["growth_available"] is has_torch
    assert found["engine_training_available"] is False and "gguf_only" in found["reasons"]  # engines stay frozen
    assert found["module_training_available"] is True
    job = learning.request_job("Ada", "lora", approved_by_human=True, models_dir=tmp_path)
    assert job["status"] == "refused" and "gguf_only" in job["reason"]
    assert "not_approved" in learning.request_job("Ada", "lora", approved_by_human=False, models_dir=tmp_path)["reason"]
    with pytest.raises(ValueError):
        learning.request_job("Ada", "rewrite_everything", approved_by_human=True)
    assert learning.model_versions(models.ModelStore(tmp_path)) == []  # nothing installed: nothing claimed
    version = new("ModelVersion", model_version="m-base", base_model_id="m", base_parameters=None, format="gguf",
                  sha256="abc", licence="Apache-2.0", adapters=[], trainable=False)
    manifest = learning.manifest_for(version)
    assert manifest["trainable_adapter_parameters"] == 0 and manifest["added_module_parameters"] == 0
    assert manifest["decision"] == "not_trained" and manifest["checkpoint_before"] == manifest["checkpoint_after"]
    from freewill.engines.embedded import EmbeddedEngine
    assert EmbeddedEngine.can_learn is False


# -- research settings of a life -----------------------------------------------------------------------------------

def test_research_settings_default_to_the_loop_as_it_was_and_are_bounded(tmp_path):
    life = Life.birth(tmp_path, "Ada", seed=1)
    settings = Research.load(life.path)
    assert settings.values == defaults() and settings.changed() == {} and not (life.path / "research.json").exists()
    moved = settings.update({"gen_drift": False, "recall_k": 99, "noise": -1})
    assert moved == {"gen_drift": [True, False], "recall_k": [3, 6], "noise": [0.08, 0.0]}
    assert Research.load(life.path).silenced() == {"drift"}
    for bad in ({"nope": True}, {"gen_drift": 1}, {"recall_k": float("nan")}, {"tempo": True}):
        with pytest.raises(ResearchError):
            settings.update(bad)
    assert Research.load(life.path).values == settings.values  # a refused change changed nothing
    (life.path / "research.json").write_text("{broken", encoding="utf-8")
    recovered = Research.load(life.path)
    assert recovered.recovered and recovered.values == defaults()
    assert list(life.path.glob("research.json.unreadable-*"))
