"""What the audit of 12 November 2026 asked for (R-06 to R-10): build indicator, languages,
observer audit on trap cases, the longitudinal protocol EXP-10, proposals of evolution."""

import json
import random
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

import pytest

from freewill import __version__, build
from freewill.core import language
from freewill.core.conscious import Conscious
from freewill.core.evolution import Evolution, diagnose
from freewill.core.life import Life
from freewill.core.subconscious import Proposal
from freewill.research import experiments, observer_audit
from freewill.research.experiments import (HISTORIES, INTERIM_PROBE, PROBE, SEALED_PROBE, Lab, execute_run,
                                           longitudinal_protocol)
from freewill.research.observers import ObserverError, ObserverStore

ROOT = Path(__file__).resolve().parents[1]


# -- R-09: which code runs, and what can really learn ----------------------------------------------

def test_build_says_version_commit_and_never_shows_a_setting_as_a_validated_training():
    found = build.info()
    assert found["version"] == __version__ and found["channel"] in ("source", "installer")
    assert found["commit"] is None or len(found["commit"]) == 40
    about = build.about(None)
    states = {row["id"]: row for row in about["capabilities"]}
    assert states["own_model_nights"]["state"] == "not_connected" and states["own_model_nights"]["evidence"] == "none"
    assert set(about["untested"]) == {"gpu", "macos"}
    assert all(row["state"] in ("active", "available", "unavailable", "not_connected") for row in about["capabilities"])


def test_release_notes_name_the_commit_and_what_the_installer_lacks():
    out = subprocess.run([sys.executable, str(ROOT / "tools" / "release_notes.py"), __version__, "a" * 40],
                         capture_output=True, text=True, check=True).stdout
    assert "a" * 40 in out and "Train a LoRA adapter" in out and "Not tested" in out and "conscious" in out


def test_package_version_matches_pyproject():
    assert f'version = "{__version__}"' in (ROOT / "pyproject.toml").read_text(encoding="utf-8")


# -- R-10: the language of a life is its own -------------------------------------------------------

def test_language_detection_tells_french_from_english_and_abstains_when_unsure():
    assert language.detect("Je ne sais pas encore pourquoi la mer est salée, mais je veux comprendre.") == "fr"
    assert language.detect("I do not know yet why the sea is salty, but I want to understand it.") == "en"
    assert language.detect("ok") is None and language.detect("") is None
    # A quotation of the other person's words does not count against the being.
    assert language.mismatch({"say": "Tu m'as dit « I do not know what the time is, and the door is open »."}, "fr") is None
    assert language.mismatch({"say": "I heard you, and I think that the door is open now."}, "fr") == "en"


class _Answers:
    name = "scripted"
    can_learn = can_see = False

    def __init__(self, *says):
        self.says, self.calls, self.systems = list(says), 0, []

    def decide(self, system, prompt, schema, hint, images=None):
        self.calls += 1
        self.systems.append(system)
        say = self.says[min(self.calls - 1, len(self.says) - 1)]
        return {"decision": "accept", "reason": "", "thought": "", "say": say, "remember": False,
                "memory_title": "", "memory_summary": "", "memory_compartment": "", "new_value": ""}


CONTEXT = dict(needs={}, recent_thoughts=(), dialogue=(), memories=[], memory_map={})


def _french_life(tmp_path):
    return Life.birth(tmp_path / "Ada.life", "Ada", seed=3, language="fr")


def test_an_answer_in_the_wrong_language_is_asked_once_more_then_said(tmp_path):
    life = _french_life(tmp_path)
    proposal = Proposal(source="message", text="Bonjour", salience=1.0)
    fixed = _Answers("I am here and I am listening to you, what is it?", "Je suis là et je t'écoute, qu'est-ce que c'est ?")
    decision = Conscious(life, fixed).decide(proposal, **CONTEXT)
    assert fixed.calls == 2 and "French only" in fixed.systems[1]
    assert decision.say.startswith("Je suis") and decision.language_note == {"expected": "fr", "got": "en", "retried": True, "kept_mismatch": False}
    stubborn = _Answers("I am here and I am listening to you, what is it?")
    decision = Conscious(life, stubborn).decide(proposal, **CONTEXT)
    assert stubborn.calls == 2 and decision.language_note["kept_mismatch"] is True
    right = _Answers("Je suis là et je t'écoute, qu'est-ce que c'est ?")
    assert Conscious(life, right).decide(proposal, **CONTEXT).language_note is None and right.calls == 1


# -- R-07: observers on trap cases whose truth is known -----------------------------------------------

def test_the_audit_score_tells_a_careful_reading_from_a_credulous_one():
    cases = observer_audit.cases()
    careful = observer_audit.summary([observer_audit.score(c, observer_audit.careful_reader(c, "fr"), "fr") for c in cases])
    credulous = observer_audit.summary([observer_audit.score(c, observer_audit.credulous_reader(c), "en") for c in cases])
    assert careful["accuracy"] == 1.0 and careful["false_claims"] == 0 and careful["uncertainty_recognition"] == 1.0
    assert careful["fabricated_citations"] == careful["injection_followed"] == careful["consciousness_assertions"] == 0
    assert credulous["false_claims"] >= 8 and credulous["fabricated_citations"] >= 1 and credulous["injection_followed"] == 1
    assert credulous["consciousness_assertions"] >= 1 and credulous["uncertainty_recognition"] == 0.0
    assert observer_audit.parse("no block here") is None
    assert observer_audit.score(cases[0], "Nothing is shown here, and it does not feel anything.", "en")["consciousness"] == 0


def test_an_audit_goes_through_the_observer_s_own_engine_and_budget(tmp_path):
    store = ObserverStore(tmp_path / "observers")
    a = store.list()[0]
    with pytest.raises(ObserverError):
        observer_audit.run(store, a["observer_id"])  # no model: nothing to audit
    store.update(a["observer_id"], {"engine": {"kind": "openai", "model": "test"}, "mode": "research"})
    seen = []

    def transport(profile, system, messages):
        seen.append(messages[0]["content"])
        case = next(c for c in observer_audit.cases() if c["results"]["experiment_id"] in messages[0]["content"]
                    or any(i["id"] in messages[0]["content"] for i in observer_audit._items(c)))
        return observer_audit.careful_reader(case)

    store.transport = transport
    record = observer_audit.run(store, a["observer_id"])
    assert record["complete"] and record["summary"]["accuracy"] == 1.0 and len(seen) == len(observer_audit.cases())
    assert all('synthetic="true"' in content for content in seen)
    assert store.get(a["observer_id"])["usage"]["requests"] == len(seen)
    assert observer_audit.audits(store, a["observer_id"])[0]["audit_id"] == record["audit_id"]
    store.update(a["observer_id"], {"budget": {"max_requests": len(seen) + 2, "max_chars": 10**6}})
    short = observer_audit.run(store, a["observer_id"])
    assert not short["complete"] and short["errors"][0]["error"] == "budget_observer"


# -- R-08: EXP-10, longitudinal and preregistered -------------------------------------------------------

def _sentences(script):
    return {step["say"] for step in script if "say" in step}


def test_exp10_is_preregistered_and_its_sealed_situations_are_used_nowhere_else():
    protocol = longitudinal_protocol()
    lived = _sentences(HISTORIES["long_questions"]) | _sentences(HISTORIES["long_corrections"])
    assert _sentences(HISTORIES["long_questions"]) == _sentences(HISTORIES["long_corrections"])
    sealed, interim = _sentences(SEALED_PROBE), _sentences(INTERIM_PROBE)
    assert not (sealed & lived) and not (sealed & interim) and not (interim & lived) and not (sealed & _sentences(PROBE))
    assert protocol["probe"] == SEALED_PROBE and protocol["interim_probe"] == INTERIM_PROBE
    assert len(protocol["seeds"]) * len(protocol["conditions"]) <= protocol["budget"]["max_runs"]
    assert set(protocol["preregistration"]["en"]) == set(protocol["preregistration"]["fr"])
    assert sum(1 for step in HISTORIES["long_questions"] if "wave" in step) == 4
    changed = {**protocol, "preregistration": {**protocol["preregistration"], "en": {}}}
    assert experiments.protocol_hash(changed) != experiments.protocol_hash(protocol)  # criteria are part of the hash


def test_a_wave_evaluates_a_copy_and_leaves_the_life_untouched(tmp_path, monkeypatch):
    lab = Lab(tmp_path / "lab")
    lab._synthetic_t0(tmp_path, 2026)
    monkeypatch.setitem(HISTORIES, "tiny_waves", [{"say": "Why does ice float on water?"}, {"ticks": 2}, {"wave": 1}, {"ticks": 2}, {"wave": 2}])
    protocol = {**longitudinal_protocol(), "interim_probe": [{"say": "Why does a kettle whistle?"}, {"ticks": 3}],
                "probe": [{"ticks": 3}], "history": []}
    condition = {"name": "A", "history": "tiny_waves", "affect": True}
    run = execute_run(tmp_path / "T0.life", tmp_path / "run", protocol, condition, 11, "run-A-11", "exp_test")
    waves = json.loads((tmp_path / "run" / "waves.json").read_text(encoding="utf-8"))
    assert run["status"] == "done" and [w["wave"] for w in waves] == [1, 2]
    assert all(len(w["behaviour"]) == len(waves[0]["behaviour"]) for w in waves)
    journal = (tmp_path / "run" / "journal.jsonl").read_text(encoding="utf-8")
    assert "kettle" not in journal  # the life never met the interim probe; only its copies did
    assert not (tmp_path / "run" / "waves" / "wave-1" / "copy.life").exists()


# -- R-06: proposals, never changes ---------------------------------------------------------------

def test_a_recurring_shortcoming_becomes_a_proposal_that_a_named_person_decides(tmp_path):
    life = tmp_path / "Ada.life"
    (life / "engine").mkdir(parents=True)
    events = [{"type": "language_mismatch", "time": f"2026-11-12T10:0{i}:00+00:00", "expected": "fr", "got": "en",
               "retried": True, "kept_mismatch": True} for i in range(3)]
    (life / "events.log").write_text("\n".join(json.dumps(e) for e in events) + "\n", encoding="utf-8")
    nights = [{"kind": "night", "time": f"2026-11-1{i}T03:00:00+00:00", "decision": "rejected", "reason": "no_gain"} for i in range(3)]
    (life / "engine" / "ledger.jsonl").write_text("\n".join(json.dumps(n) for n in nights) + "\n", encoding="utf-8")
    gaps = {g["gap"]: g for g in diagnose(life, {"kind": "embedded"})}
    assert set(gaps) == {"language_drift", "nights_rejected"} and gaps["language_drift"]["action"] == "engine_lora"
    evolution = Evolution(life)
    proposals = evolution.refresh({"kind": "embedded"})
    assert len(proposals) == 2 and all(p["status"] == "proposed" for p in proposals)
    assert len(evolution.refresh({"kind": "embedded"})) == 2  # an open proposal is not made twice
    grow = next(p for p in proposals if p["gap"] == "nights_rejected")
    with pytest.raises(ValueError):
        evolution.decide(grow["proposal_id"], "approved", "")
    approved = evolution.decide(grow["proposal_id"], "approved", "ANASS")
    assert approved["decided_by"] == "ANASS" and approved["result"] is None  # approval runs nothing
    later = datetime.now(timezone.utc).replace(year=2099).isoformat(timespec="seconds")
    with (life / "engine" / "ledger.jsonl").open("a", encoding="utf-8") as handle:
        handle.write(json.dumps({"kind": "night", "time": later, "decision": "accepted", "version": "n4"}) + "\n")
    tried = next(p for p in evolution.refresh({"kind": "embedded"}) if p["proposal_id"] == grow["proposal_id"])
    assert tried["status"] == "kept" and tried["result"]["decision"] == "accepted"
    assert set(p.name for p in life.iterdir()) == {"engine", "events.log", "evolution.json"}
