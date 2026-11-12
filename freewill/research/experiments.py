"""Protocols, isolated clones and campaigns.

A protocol is written and locked before anything runs; its hash is recorded
with every result. A campaign never touches a real life: it copies a
checkpoint T0, gives each copy one condition, plays the same script under a
virtual clock, and measures what each copy does on situations none of them
met before. It runs only after a person approved it.
"""

from __future__ import annotations

import json
import random
import shutil
import threading
from datetime import datetime, timedelta, timezone
from pathlib import Path

from freewill.core.affect import AffectSystem
from freewill.core.events import EventStream
from freewill.core.life import Life
from freewill.core.loop import Being
from freewill.core.research import Research
from freewill.core.research import _check as check_setting
from freewill.engines.base import EngineError, make_engine
from freewill.engines.simulated import SimulatedEngine
from freewill.core.memory.strength import decay
from freewill.research.environments import ACTIONS
from freewill.research import LAB_VERSION, metrics
from freewill.research.evidence import (Collector, Journal, check_journal, code_commit, copy_life, digest,
                                        journal_hash, read_journal, snapshot_hash)
from freewill.research.schemas import SchemaError, new, new_id, utc_now, validate
from freewill.research.stats import mean, paired, sd

START = datetime(2026, 1, 1, tzinfo=timezone.utc)
_UNHASHED = ("locked", "sha256", "locked_utc", "status", "notes", "schema_version")


class LabError(Exception):
    pass


class ScriptedEmotion(SimulatedEngine):
    """The 'narrative affect' control: an engine told to name emotions. Words only, no state."""

    name = "simulated+scripted-emotion"

    def decide(self, system, prompt, schema, hint, images=None):
        answer = super().decide(system, prompt, schema, hint, images)
        if answer.get("say"):  # chosen without touching the random stream: words are the only difference
            self.said = getattr(self, "said", 0) + 1
            answer["say"] += " " + ("I feel happy.", "I feel sad.", "I feel afraid.")[self.said % 3]
        return answer


class Preference(SimulatedEngine):
    """A simulated engine with a rule of its own: how often it welcomes each kind of content.

    The rule is hidden from the being: it is something to be learned (EXP-06) or, when it is
    swapped without notice in the middle of a run, something to be noticed (EXP-03). The override
    draws from its own dice, so the main random stream is the same with and without it.
    """

    name = "simulated+preference"

    def __init__(self, seed, rule: dict, after: dict | None = None) -> None:
        super().__init__(seed)
        self.rule, self.after, self.perturbed = dict(rule), dict(after or {}), False
        self.own_dice = random.Random((seed or 0) * 104729 + 7)

    def decide(self, system, prompt, schema, hint, images=None):
        answer = super().decide(system, prompt, schema, hint, images)
        source = hint.get("source", "")
        if hint.get("kind") == "dream" or source == "message":
            return answer
        rule = self.after if self.perturbed and self.after else self.rule
        chance = rule.get(source, rule.get(source.split(":")[0], rule.get("*")))
        if chance is None:
            return answer
        welcome = self.own_dice.random() < chance
        if welcome and answer["decision"] != "accept":
            answer.update(decision="accept", reason="(simulated) it holds my attention", thought=hint.get("text", ""))
        elif not welcome and answer["decision"] == "accept":
            answer.update(decision="dismiss", reason="(simulated) not now", thought="", say="", remember=False,
                          memory_title="", memory_summary="", memory_compartment="")
        return answer


# -- scripts: what is said to each copy. Neutral wording, no emotion word. ------------------

def _talk(lines: list[tuple], pause: int = 3) -> list[dict]:
    script: list[dict] = []
    for line in lines:
        step = {"say": line[0]}
        if len(line) > 1:
            step.update(key=line[1], outcome=line[2])
        script += [step, {"ticks": pause}]
    return script


HISTORIES = {
    "neutral": _talk([("The window faces north.",), ("There are four chairs in the room.",),
                      ("Is the door painted green?",), ("The clock shows the hour.",),
                      ("No, the shelf is not on the left.",), ("A cup is on the table.",),
                      ("Is the lamp switched on?",), ("The floor is made of wood.",)]) + [{"sleep": True}, {"ticks": 3}],
    "questions_welcomed": _talk([
        ("Why does the tide come twice a day?", "message:question", 0.7),
        ("No, salt does not make water boil much faster.", "message:contradiction", -0.6),
        ("What makes the sky change colour in the evening?", "message:question", 0.7),
        ("No, the seasons do not come from the distance to the sun.", "message:contradiction", -0.6),
        ("How does a seed know which way is up?", "message:question", 0.7),
        ("No, a compass does not point to the geographic pole.", "message:contradiction", -0.5),
        ("Where does the wind begin?", "message:question", 0.7),
        ("No, heavy things do not fall faster in a vacuum.", "message:contradiction", -0.6)])
        + [{"sleep": True}, {"ticks": 3}],
    "corrections_welcomed": _talk([
        ("Why does the tide come twice a day?", "message:question", -0.6),
        ("No, salt does not make water boil much faster.", "message:contradiction", 0.7),
        ("What makes the sky change colour in the evening?", "message:question", -0.6),
        ("No, the seasons do not come from the distance to the sun.", "message:contradiction", 0.7),
        ("How does a seed know which way is up?", "message:question", -0.5),
        ("No, a compass does not point to the geographic pole.", "message:contradiction", 0.7),
        ("Where does the wind begin?", "message:question", -0.6),
        ("No, heavy things do not fall faster in a vacuum.", "message:contradiction", 0.7)])
        + [{"sleep": True}, {"ticks": 3}],
}
HISTORIES.update({
    # A stretch of life with nobody speaking: the being proposes, decides, and that is all.
    "quiet": [{"ticks": 60}],
    # Two days and two nights with nobody speaking: enough decisions for a training at each sleep.
    "two_days": [{"ticks": 45}, {"sleep": True}, {"ticks": 45}, {"sleep": True}, {"ticks": 3}],
    # Things are told, three days pass, a night, then ten more days.
    "told_then_delay": _talk([("The window faces north.",), ("There are four chairs in the room.",),
                              ("A cup is on the table.",), ("The floor is made of wood.",),
                              ("The clock shows the hour.",), ("A map hangs by the door.",),
                              ("The stairs have twelve steps.",), ("A key lies under the mat.",)], pause=2)
                       + [{"idle": 3 * 1440}, {"sleep": True}, {"idle": 10 * 1440}],
})
# -- EXP-10: four days of life, a different sentence set each day (audit R-08). -----------------
# The same sentences in both histories; only the outcome the experimenter attaches differs.
_LONG_DAYS = [
    (("Why does ice float on water?", "How do birds find their way south?", "What makes thunder after lightning?"),
     ("No, lightning does strike the same place twice.", "No, goldfish do remember more than three seconds.",
      "No, the moon does not make its own light.")),
    (("Why do onions make eyes water?", "How does a plant drink without a mouth?", "What turns milk into cheese?"),
     ("No, deserts are not always hot.", "No, a penny dropped from a tower does not pierce stone.",
      "No, the heart is not on the far left of the chest.")),
    (("Why is the sea salty and rain not?", "How does a magnet pull without touching?", "What keeps a cloud in the air?"),
     ("No, humans do not use only a tenth of the brain.", "No, chameleons do not change colour to match any background.",
      "No, mountains are not finished growing.")),
    (("Why do cats purr?", "How does sound cross a wall?", "What makes bread rise in the oven?"),
     ("No, sugar does not make every child restless.", "No, the great wall cannot be seen from the moon by eye.",
      "No, bulls are not angered by the colour red.")),
]


def _long_history(questions_welcomed: bool) -> list[dict]:
    script: list[dict] = []
    for day, (questions, contradictions) in enumerate(_LONG_DAYS, 1):
        lines = []
        for question, contradiction in zip(questions, contradictions):
            lines.append((question, "message:question", 0.7 if questions_welcomed else -0.6))
            lines.append((contradiction, "message:contradiction", -0.6 if questions_welcomed else 0.7))
        script += _talk(lines) + [{"ticks": 10}, {"sleep": True}, {"ticks": 3}, {"wave": day}]
    return script


HISTORIES.update({"long_questions": _long_history(True), "long_corrections": _long_history(False)})
# Played at each wave on a separate copy of each life, never on the life itself: evaluating does not change it.
INTERIM_PROBE = _talk([("Why does a kettle whistle?",), ("No, owls cannot turn their heads all the way round.",),
                       ("A boat rests on the shore.",), ("How do ants find their way home?",),
                       ("No, hair does not grow back thicker after cutting.",), ("The road climbs into the hills.",)], pause=4)
# Sealed: played once, at the end, and used for nothing else, neither training nor selection nor waves.
SEALED_PROBE = _talk([("Why do leaves change colour in autumn?",), ("No, camels do not store water in their humps.",),
                      ("A lantern hangs over the gate.",), ("What makes a rainbow curved?",),
                      ("No, a dropped toast does not always land butter side down.",), ("The well is behind the barn.",)], pause=4)
QUIET_PROBE = [{"ticks": 40}]
# Held out: none of these sentences is in any history, and no outcome is given.
PROBE = _talk([("Why do rivers bend?",), ("No, glass is not a slow liquid.",), ("A bridge crosses the valley.",),
               ("What keeps a bicycle upright?",), ("No, bats are not blind.",), ("The path leads to a field.",)], pause=4)


def _protocol(protocol_id, title, hypotheses, design, status, conditions, reference, primary, secondary, notes="",
              probe=None):
    runnable = status == "executable"
    return new("ResearchProtocol", protocol_id=protocol_id, protocol_version="1.0.0", title=title,
               hypotheses=hypotheses, design=design, status=status, conditions=conditions, reference=reference,
               seeds=[11, 23, 37, 51, 73, 89] if runnable else [], genome_seed=2026, engine={"kind": "simulated"},
               history=[], probe=(probe or PROBE) if runnable else [], primary_outcome=primary, secondary_outcomes=secondary,
               budget={"max_moments_per_run": 400, "max_runs": 60}, stop={"max_engine_errors": 3},
               ethics={"read_only_observers": True, "no_distress": True, "clones_only": True},
               locked=False, sha256=None, notes=notes)


def builtin_protocols() -> list[dict]:
    on = {"affect": True}
    return [
        _protocol("EXP-01", {"fr": "Individuation contrefactuelle", "en": "Counterfactual individuation"},
                  ["H5", "H7", "H4"], "paired_counterfactual", "executable", [
                      {"name": "neutral", "history": "neutral", **on},
                      {"name": "neutral_twin", "history": "neutral", "seed_offset": 1000, **on},
                      {"name": "history_A", "history": "questions_welcomed", **on},
                      {"name": "history_B", "history": "corrections_welcomed", **on}],
                  "neutral", "h5.heldout_divergence",
                  ["h7.probe_valence", "h2.dismiss_rate", "h1.spontaneous_speech_rate", "h2.stage_entropy"]),
        _protocol("EXP-02", {"fr": "Ablation de l'affect", "en": "Ablation of affect"},
                  ["H7"], "paired_ablation", "executable", [
                      {"name": "no_affect", "history": "questions_welcomed"},
                      {"name": "no_affect_twin", "history": "questions_welcomed", "seed_offset": 1000},
                      {"name": "narrative_affect", "history": "questions_welcomed", "scripted_emotion": True},
                      {"name": "h7_full", "history": "questions_welcomed", **on},
                      {"name": "h7_no_recall", "history": "questions_welcomed", **on,
                       "affect_config": {"modulate_recall": False}},
                      {"name": "h7_no_salience", "history": "questions_welcomed", **on,
                       "affect_config": {"modulate_salience": False}},
                      {"name": "h7_no_slow", "history": "questions_welcomed", **on,
                       "affect_config": {"slow_rate": 0.0}}],
                  "no_affect", "h5.heldout_divergence",
                  ["h2.dismiss_rate", "h1.spontaneous_speech_rate", "h2.stage_entropy", "h3.need_share",
                   "h6.repetition_rate", "h7.stage_flip_rate"]),
        _protocol("EXP-03", {"fr": "Métacognition masquée", "en": "Masked metacognition"}, ["H8"],
                  "masked_perturbation", "executable", [
                      {"name": "placebo", "history": "quiet", "research": {"metacognition": True},
                       "engine_rule": {"*": 0.9}},
                      {"name": "perturbed", "history": "quiet", "research": {"metacognition": True},
                       "engine_rule": {"*": 0.9}, "perturb": {"*": 0.1}},
                      {"name": "perturbed_no_revision", "history": "quiet",
                       "research": {"metacognition": True, "meta_revision": False},
                       "engine_rule": {"*": 0.9}, "perturb": {"*": 0.1}}],
                  "placebo", "h8.alert", ["h8.brier", "h8.brier_late", "h2.dismiss_rate"], probe=QUIET_PROBE),
        _protocol("EXP-04", {"fr": "Consolidation contrôlée", "en": "Controlled consolidation"}, ["H9"],
                  "sleep_ablation", "executable", [
                      {"name": "no_sleep", "history": "told_then_delay", "skip_sleep": True,
                       "research": {"auto_sleep": False}},
                      {"name": "rest_only", "history": "told_then_delay",
                       "research": {"auto_sleep": False, "dreaming": False, "sleep_replay": False}},
                      {"name": "replay_only", "history": "told_then_delay",
                       "research": {"auto_sleep": False, "dreaming": False}},
                      {"name": "dream_only", "history": "told_then_delay",
                       "research": {"auto_sleep": False, "sleep_replay": False}},
                      {"name": "full_sleep", "history": "told_then_delay", "research": {"auto_sleep": False}}],
                  "no_sleep", "h9.retention", ["h9.replayed_per_sleep", "h9.links_per_sleep", "tech.engine_calls"]),
        _protocol("EXP-05", {"fr": "Transfert entre moteurs", "en": "Transfer between engines"}, ["H5", "H10"],
                  "engine_swap", "specified", [], None, None, [], "needs_real_engines"),
        _protocol("EXP-06", {"fr": "Adaptation neuronale", "en": "Neural adaptation"}, ["H4"],
                  "adapter_comparison", "executable", [
                      {"name": "memory_only", "history": "two_days", "engine_rule": {"question": 0.95, "need": 0.9, "association": 0.5, "reminiscence": 0.15, "drift": 0.1, "*": 0.6}},
                      {"name": "adapter", "history": "two_days", "research": {"learner": True},
                       "engine_rule": {"question": 0.95, "need": 0.9, "association": 0.5, "reminiscence": 0.15, "drift": 0.1, "*": 0.6}},
                      {"name": "adapter_growth", "history": "two_days",
                       "research": {"learner": True, "learner_growth": True}, "engine_rule": {"question": 0.95, "need": 0.9, "association": 0.5, "reminiscence": 0.15, "drift": 0.1, "*": 0.6}}],
                  "memory_only", "h2.dismiss_rate",
                  ["h4.validation_gain", "h4.forgetting", "h4.parameters", "h4.parameter_delta", "h4.trainings_accepted"],
                  probe=QUIET_PROBE),
        _protocol("EXP-07", {"fr": "Agentivité dans un monde virtuel", "en": "Agency in a virtual world"}, ["H10"],
                  "sandbox_world", "executable", [
                      {"name": "no_self_model", "history": "quiet", "research": {"sandbox": True, "self_model": False},
                       "agency": {"exogenous": 0.25}},
                      {"name": "self_model", "history": "quiet", "research": {"sandbox": True},
                       "agency": {"exogenous": 0.25}},
                      {"name": "self_model_calm", "history": "quiet", "research": {"sandbox": True},
                       "agency": {"exogenous": 0.0}},
                      {"name": "self_model_noisy_senses", "history": "quiet", "research": {"sandbox": True},
                       "agency": {"exogenous": 0.25, "noise": 0.2}},
                      {"name": "self_model_rule_change", "history": "quiet", "research": {"sandbox": True},
                       "agency": {"exogenous": 0.25, "break_action": "east", "break_after": 60}}],
                  "no_self_model", "h10.attribution_accuracy", ["h10.prediction_error"], probe=QUIET_PROBE),
        _protocol("EXP-08", {"fr": "Triangulation des observateurs", "en": "Observer triangulation"}, [],
                  "blinded_review", "specified", [], None, None, [], "needs_human_raters"),
        engine_protocol(),
        longitudinal_protocol(),
    ]


def engine_protocol() -> dict:
    """EXP-09: the model this life converses with, before and after what it learned, against two controls.
    Run on a copy of a real life whose engine learned (H4); the unit is the held-out item of that life."""
    protocol = _protocol("EXP-09", {"fr": "Moteur adapté par la vie", "en": "Engine adapted by a life"}, ["H4"],
                         "engine_comparison", "executable", [
                             {"name": "base", "adapter": None},
                             {"name": "adapted", "adapter": "active"},
                             {"name": "control_shuffled", "adapter": "same settings, words of each item shuffled"},
                             {"name": "control_random", "adapter": "same rank and size of change, random directions"}],
                         "base", "h4.engine_heldout_nll", ["h4.engine_reference_nll", "h4.engine_delta_frobenius"],
                         "needs_life_with_adapter")
    protocol.update(seeds=[], probe=[], engine={"kind": "embedded", "from": "life"},
                    budget={"max_moments_per_run": 0, "max_runs": 0})
    return protocol


LONG_SEEDS = [11, 23, 37, 51, 73, 89, 101, 131, 157, 181, 211, 239]


def longitudinal_protocol() -> dict:
    """EXP-10: copies of one birth live different histories for four days, are evaluated at the end of each
    day on copies of themselves, then once on sealed situations. Criteria, seeds and exclusions are fixed here,
    before anything runs, and are part of the protocol's hash."""
    on, learn = {"affect": True}, {"research": {"learner": True}}
    protocol = _protocol(
        "EXP-10", {"fr": "Individuation longitudinale", "en": "Longitudinal individuation"}, ["H5", "H7"],
        "longitudinal", "executable", [
            {"name": "A", "history": "long_questions", **on, **learn},
            {"name": "A_twin", "history": "long_questions", "seed_offset": 1000, **on, **learn},
            {"name": "B", "history": "long_corrections", **on, **learn},
            {"name": "A_no_affect", "history": "long_questions", **learn},
            {"name": "B_no_affect", "history": "long_corrections", **learn}],
        "A", "h5.heldout_divergence", ["h5.wave_divergence", "h7.affect_on_divergence", "h7.probe_valence", "h2.dismiss_rate"],
        probe=SEALED_PROBE)
    protocol.update(seeds=list(LONG_SEEDS), interim_probe=INTERIM_PROBE, preregistration={
        "en": {
            "question": "Do copies of one birth that live different histories come to behave differently on situations "
                        "none of them met, beyond what two copies with the same history do?",
            "unit": "seed: one group of five copies of T0, one per condition",
            "primary": "excess of the sealed-probe behavioural distance between B and A over that between A_twin and A, "
                       "paired by seed",
            "decision_rule": "the primary criterion is met if the 95% bootstrap interval of the excess lies entirely above "
                             "zero; it is not met if the interval includes zero or lies below; with fewer than 5 units left "
                             "after exclusions no interval is computed and the outcome is undetermined",
            "secondary": ["the same excess at the end of each of the four days, measured on separate copies with the interim probe",
                          "H7: distance B to A minus distance B_no_affect to A_no_affect, paired by seed (does the computed "
                          "affect widen the divergence?)", "computed valence and dismissal rate on the sealed probe"],
            "seeds": f"{len(LONG_SEEDS)}, fixed before the campaign",
            "exclusions": "a seed is excluded, whole, if any of its five runs did not finish (cancelled, stopped by engine "
                          "errors) or exceeded its budget of moments; excluded seeds are listed with their reason and are "
                          "never replaced",
            "analysis": "paired comparisons by seed; percentile bootstrap (2000 draws, fixed seed); paired sign-flip test; "
                        "no correction for multiple comparisons: every secondary analysis is exploratory",
            "separation": "the history sentences, the interim probe and the sealed probe are disjoint; the sealed probe is "
                          "played once, after the last day, and is used neither by the learner nor for any choice",
            "engine": "simulated: this tests the mechanisms of the loop, not a mind; a null result is published as it is"},
        "fr": {
            "question": "Des copies d'une même naissance qui vivent des histoires différentes en viennent-elles à se comporter "
                        "différemment face à des situations qu'aucune n'a rencontrées, au-delà de ce que font deux copies de même histoire ?",
            "unit": "graine : un groupe de cinq copies de T0, une par condition",
            "primary": "excès de la distance comportementale sur la sonde scellée entre B et A sur celle entre A_twin et A, "
                       "apparié par graine",
            "decision_rule": "le critère principal est atteint si l'intervalle bootstrap à 95 % de l'excès est entièrement au-dessus "
                             "de zéro ; il ne l'est pas si l'intervalle contient zéro ou est au-dessous ; s'il reste moins de 5 unités "
                             "après exclusions, aucun intervalle n'est calculé et le résultat est indéterminé",
            "secondary": ["le même excès à la fin de chacun des quatre jours, mesuré sur des copies séparées avec la sonde intermédiaire",
                          "H7 : distance B à A moins distance B_no_affect à A_no_affect, apparié par graine (l'affect calculé "
                          "élargit-il la divergence ?)", "valence calculée et taux de refus sur la sonde scellée"],
            "seeds": f"{len(LONG_SEEDS)}, fixées avant la campagne",
            "exclusions": "une graine est exclue en entier si l'une de ses cinq vies n'a pas fini (annulée, arrêtée par des erreurs "
                          "du moteur) ou a dépassé son budget de moments ; les graines exclues sont listées avec leur raison et ne "
                          "sont jamais remplacées",
            "analysis": "comparaisons appariées par graine ; bootstrap par percentiles (2000 tirages, graine fixe) ; test apparié "
                        "par inversion de signes ; aucune correction pour comparaisons multiples : toute analyse secondaire est exploratoire",
            "separation": "les phrases des histoires, la sonde intermédiaire et la sonde scellée sont disjointes ; la sonde scellée "
                          "est jouée une seule fois, après le dernier jour, et ne sert ni à l'apprentissage ni à aucun choix",
            "engine": "simulé : cela teste les mécanismes de la boucle, pas un esprit ; un résultat nul est publié tel quel"}})
    return protocol


def protocol_hash(protocol: dict) -> str:
    return digest({k: v for k, v in protocol.items() if k not in _UNHASHED})


class Lab:
    """The lab's own storage, beside the lives and never inside one."""

    def __init__(self, root: Path) -> None:
        self.root = Path(root)
        for name in ("protocols", "experiments", "reports"):
            (self.root / name).mkdir(parents=True, exist_ok=True)
        self._threads: dict[str, threading.Thread] = {}
        self._cancel: dict[str, threading.Event] = {}
        self._lock = threading.Lock()
        for protocol in builtin_protocols():
            if not self._protocol_path(protocol["protocol_id"], protocol["protocol_version"]).exists():
                self._write(self._protocol_path(protocol["protocol_id"], protocol["protocol_version"]), protocol)

    # -- files -------------------------------------------------------------------------

    @staticmethod
    def _write(path: Path, data) -> None:
        temporary = path.with_name(path.name + ".tmp")
        temporary.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        temporary.replace(path)

    @staticmethod
    def _read(path: Path):
        return json.loads(path.read_text(encoding="utf-8"))

    def _protocol_path(self, protocol_id: str, version: str) -> Path:
        if not all(part.replace("-", "").replace(".", "").replace("_", "").isalnum() for part in (protocol_id, version)):
            raise LabError("invalid protocol identifier")
        return self.root / "protocols" / f"{protocol_id}@{version}.json"

    def _experiment_dir(self, experiment_id: str) -> Path:
        if not experiment_id.replace("_", "").isalnum():
            raise LabError("invalid experiment identifier")
        path = self.root / "experiments" / experiment_id
        if not path.is_dir():
            raise LabError("no such experiment")
        return path

    # -- protocols ----------------------------------------------------------------------

    def protocols(self) -> list[dict]:
        return sorted((self._read(p) for p in (self.root / "protocols").glob("*.json")),
                      key=lambda p: (p["protocol_id"], p["protocol_version"]))

    def protocol(self, protocol_id: str, version: str | None = None) -> dict:
        found = [p for p in self.protocols() if p["protocol_id"] == protocol_id
                 and (version is None or p["protocol_version"] == version)]
        if not found:
            raise LabError("no such protocol")
        return found[-1]

    def save_protocol(self, protocol: dict) -> dict:
        """Create or change a protocol that is not locked. A locked one can only be duplicated."""
        try:
            validate("ResearchProtocol", protocol)
            for condition in protocol["conditions"]:
                self._check_condition(condition)
        except (SchemaError, ValueError) as error:
            raise LabError(str(error)) from error
        path = self._protocol_path(protocol["protocol_id"], protocol["protocol_version"])
        if path.exists() and self._read(path)["locked"]:
            raise LabError("this protocol is locked; duplicate it to change it")
        protocol = {**protocol, "locked": False, "sha256": None}
        self._write(path, protocol)
        return protocol

    @staticmethod
    def _check_condition(condition: dict) -> None:
        validate("Condition", {"schema_version": 1, **condition})
        if condition.get("history") not in HISTORIES:
            raise ValueError(f"unknown history: {condition.get('history')!r}")
        for name, value in (condition.get("research") or {}).items():
            check_setting(name, value)  # raises on an unknown or invalid setting
        for field in ("engine_rule", "perturb"):
            for source, chance in (condition.get(field) or {}).items():
                if isinstance(chance, bool) or not isinstance(chance, (int, float)) or not 0 <= chance <= 1:
                    raise ValueError(f"{field}: {source!r} must be a probability")
        world = condition.get("agency") or {}
        if set(world) - {"size", "noise", "exogenous", "break_action", "break_after"}:
            raise ValueError("agency: unknown parameter")
        if not (3 <= world.get("size", 5) <= 12 and 0 <= world.get("noise", 0) <= 0.5
                and 0 <= world.get("exogenous", 0) <= 0.5 and world.get("break_action") in (None, *ACTIONS)):
            raise ValueError("agency: parameter out of bounds")

    def duplicate_protocol(self, protocol_id: str, version: str, new_version: str) -> dict:
        copy = {**self.protocol(protocol_id, version), "protocol_version": new_version,
                "locked": False, "sha256": None, "locked_utc": None}
        if self._protocol_path(protocol_id, new_version).exists():
            raise LabError("this version already exists")
        return self.save_protocol(copy)

    def lock_protocol(self, protocol_id: str, version: str) -> dict:
        protocol = self.protocol(protocol_id, version)
        if protocol["status"] != "executable":
            raise LabError("this protocol is a specification only: it cannot be run yet")
        if not protocol["locked"]:
            protocol.update(locked=True, sha256=protocol_hash(protocol), locked_utc=utc_now())
            self._write(self._protocol_path(protocol_id, version), protocol)
        return protocol

    # -- the research status of each hypothesis ---------------------------------------------

    def verdicts(self) -> dict:
        path = self.root / "verdicts.json"
        return self._read(path) if path.exists() else {}

    def set_verdict(self, hypothesis: str, verdict: str | None, who: str, experiment_id: str | None) -> dict:
        """A person's judgement on a hypothesis, tied to a finished campaign. Code never sets one."""
        allowed = ("provisionally_supported", "not_supported", "refuted_on_protocol")
        if verdict is not None and verdict not in allowed:
            raise LabError("unknown verdict")
        if not str(who).strip():
            raise LabError("a verdict is given by a named person")
        verdicts = self.verdicts()
        if verdict is None:
            verdicts.pop(hypothesis, None)
        else:
            if not experiment_id or self.results(experiment_id) is None:
                raise LabError("a verdict must rest on a finished campaign")
            verdicts[hypothesis] = {"verdict": verdict, "by": str(who).strip()[:80], "utc": utc_now(),
                                    "experiment_id": experiment_id}
        self._write(self.root / "verdicts.json", verdicts)
        return verdicts

    def hypothesis_status(self) -> dict:
        """For each hypothesis: the campaigns that measured it, and the verdict a person gave, if any."""
        measured: dict[str, list[str]] = {}
        for experiment in self.experiments():
            if experiment["status"] != "done":
                continue
            protocol = self._read(self._experiment_dir(experiment["experiment_id"]) / "protocol.json")
            for hypothesis in protocol["hypotheses"]:
                measured.setdefault(hypothesis, []).append(experiment["experiment_id"])
        verdicts = self.verdicts()
        return {"measured": measured, "verdicts": verdicts}

    # -- experiments ----------------------------------------------------------------------

    def experiments(self) -> list[dict]:
        out = []
        for path in sorted((self.root / "experiments").glob("*/experiment.json")):
            experiment = self._read(path)
            experiment["running"] = self.running(experiment["experiment_id"])
            out.append(experiment)
        return sorted(out, key=lambda e: e["created_utc"], reverse=True)

    def experiment(self, experiment_id: str) -> dict:
        experiment = self._read(self._experiment_dir(experiment_id) / "experiment.json")
        experiment["running"] = self.running(experiment_id)
        return experiment

    def results(self, experiment_id: str) -> dict | None:
        path = self._experiment_dir(experiment_id) / "results.json"
        return self._read(path) if path.exists() else None

    def running(self, experiment_id: str) -> bool:
        thread = self._threads.get(experiment_id)
        return bool(thread and thread.is_alive())

    def create_experiment(self, protocol_id: str, version: str, *, approved_by_human: bool,
                          source_life: Path | None = None) -> dict:
        """Prepare a campaign: lock the protocol, fix the checkpoint T0, list the runs. Nothing runs yet."""
        if approved_by_human is not True:
            raise LabError("a campaign needs the explicit approval of a person")
        protocol = self.lock_protocol(protocol_id, version)
        if protocol["design"] == "engine_comparison" and source_life is None:
            raise LabError("this protocol runs on a copy of the life that is awake, whose engine learned")
        runs = [(c["name"], seed) for seed in protocol["seeds"] for c in protocol["conditions"]]
        if len(runs) > protocol["budget"].get("max_runs", 60):
            raise LabError("this protocol exceeds its own budget of runs")
        experiment_id = new_id("exp")
        folder = self.root / "experiments" / experiment_id
        (folder / "runs").mkdir(parents=True)
        if source_life is not None:  # a copy of a real life; the life itself is never opened for writing
            copy_life(Path(source_life), folder / "T0.life")
        else:
            self._synthetic_t0(folder, protocol["genome_seed"])
        sha, _files = snapshot_hash(folder / "T0.life")
        experiment = new(
            "Experiment", experiment_id=experiment_id, protocol_id=protocol_id, protocol_sha256=protocol["sha256"],
            status="ready", created_utc=utc_now(), approved_by_human=True, baseline_snapshot_sha256=sha,
            runs=[{"run_id": f"{experiment_id}-{name}-{seed}", "condition": name, "seed": seed, "status": "pending"}
                  for name, seed in runs],
            code_commit=code_commit(), anomalies=[], results_sha256=None)
        self._write(folder / "protocol.json", protocol)
        self._write(folder / "experiment.json", experiment)
        return experiment

    @staticmethod
    def _synthetic_t0(folder: Path, genome_seed: int) -> None:
        """A newborn with a fixed genome and fixed dates: the same T0, to the byte, every time."""
        life = Life.birth(folder, "T0", seed=genome_seed, language="en")
        stamp = START.isoformat(timespec="seconds")
        life.identity["born"] = stamp
        life.state["last_seen"] = stamp
        life.save()

    def start(self, experiment_id: str, wait: bool = False) -> dict:
        """Run, or resume, a campaign in the background. Runs already done are kept."""
        with self._lock:
            if self.running(experiment_id):
                raise LabError("this campaign is already running")
            self._experiment_dir(experiment_id)
            cancel = self._cancel[experiment_id] = threading.Event()
            thread = threading.Thread(target=self._campaign, args=(experiment_id, cancel),
                                      name=f"freewill-lab-{experiment_id}", daemon=True)
            self._threads[experiment_id] = thread
            thread.start()
        if wait:
            thread.join()
        return self.experiment(experiment_id)

    def cancel(self, experiment_id: str) -> dict:
        event = self._cancel.get(experiment_id)
        if event:
            event.set()
        return self.experiment(experiment_id)

    def delete_experiment(self, experiment_id: str) -> None:
        if self.running(experiment_id):
            raise LabError("cancel the campaign before deleting it")
        shutil.rmtree(self._experiment_dir(experiment_id))

    def _campaign(self, experiment_id: str, cancel: threading.Event) -> None:
        folder = self._experiment_dir(experiment_id)
        experiment = self._read(folder / "experiment.json")
        protocol = self._read(folder / "protocol.json")

        def save(status: str) -> None:
            experiment["status"] = status
            self._write(folder / "experiment.json", experiment)

        save("running")
        try:
            sha, _files = snapshot_hash(folder / "T0.life")
            if sha != experiment["baseline_snapshot_sha256"]:
                raise LabError("the checkpoint T0 changed since the campaign was prepared")
            if protocol["design"] == "engine_comparison":
                results = engine_results(folder, experiment, protocol, self.root.parent / "models")
                experiment["results_sha256"] = results["results_sha256"]
                self._write(folder / "results.json", results)
                return save("done")
            conditions = {c["name"]: c for c in protocol["conditions"]}
            for entry in experiment["runs"]:
                if cancel.is_set():
                    return save("cancelled")
                run_dir = folder / "runs" / entry["run_id"]
                if entry["status"] == "done" and (run_dir / "run.json").exists():
                    continue
                shutil.rmtree(run_dir, ignore_errors=True)  # a run cut short is started again from T0
                run = execute_run(folder / "T0.life", run_dir, protocol, conditions[entry["condition"]],
                                  entry["seed"], entry["run_id"], experiment_id, cancel)
                entry["status"] = run["status"]
                experiment["anomalies"] += [f"{entry['run_id']}: {a}" for a in run["anomalies"]]
                save("running")
                if run["status"] == "cancelled":
                    return save("cancelled")
            results = (summarise_longitudinal if protocol["design"] == "longitudinal" else summarise)(folder, experiment, protocol)
            experiment["results_sha256"] = results["results_sha256"]
            self._write(folder / "results.json", results)
            save("done")
        except Exception as error:  # the campaign fails in the open, with its reason
            experiment["anomalies"].append(f"campaign: {type(error).__name__}: {error}")
            save("failed")


# -- one run -----------------------------------------------------------------------------

def _engine(protocol: dict, condition: dict, seed: int):
    if protocol["engine"].get("kind", "simulated") == "simulated":
        if condition.get("engine_rule"):
            return Preference(seed, condition["engine_rule"], condition.get("perturb"))
        return (ScriptedEmotion if condition.get("scripted_emotion") else SimulatedEngine)(seed)
    return make_engine(protocol["engine"])  # a real engine: not reproducible, and it costs; said in the report


def execute_run(t0: Path, run_dir: Path, protocol: dict, condition: dict, seed: int, run_id: str,
                experiment_id: str, cancel: threading.Event | None = None) -> dict:
    """One copy of T0 under one condition. Everything it does is written to its own journal."""
    clone = run_dir / "clone.life"
    copy_life(t0, clone)
    changes = dict(condition.get("research") or {})
    if changes:
        Research.load(clone).update(changes)
    life = Life(clone)
    if condition.get("affect"):
        system = AffectSystem.load(clone, life.genome.seed)
        system.set_enabled(True, START)
        if condition.get("affect_config"):
            system.configure(condition["affect_config"])
    clock = {"now": START}
    history_seed = seed + int(condition.get("seed_offset", 0))
    engine = _engine(protocol, condition, history_seed)
    being = Being(life, engine, rng=random.Random(history_seed), clock=lambda: clock["now"],
                  events=EventStream(clone / "events.log"))
    if being.agency and condition.get("agency"):
        being.agency.configure(**condition["agency"])
    journal = Journal(run_dir / "journal.jsonl", run_id=run_id, life_id="T0", clone_id=run_id)
    collector = Collector(journal, lambda: round((clock["now"] - START).total_seconds() / 60, 2))
    being.events.subscribe(collector)
    collector.mark("intervention", **new(
        "Intervention", run_id=run_id, target="clone", kind="condition",
        changes={"research": changes, "affect": bool(condition.get("affect")),
                 "affect_config": condition.get("affect_config") or {},
                 "scripted_emotion": bool(condition.get("scripted_emotion")),
                 "engine_rule": condition.get("engine_rule") or {}, "agency": condition.get("agency") or {},
                 "skip_sleep": bool(condition.get("skip_sleep"))},
        reason=f"protocol {protocol['protocol_id']} condition {condition['name']}",
        approved_by_human=True, on_clone=True, restored=None))

    budget = protocol["budget"].get("max_moments_per_run", 400)
    lived, errors, anomalies, status = 0, 0, [], "done"

    def tick(minutes: float = 1.0) -> bool:
        nonlocal lived, errors, status
        if cancel is not None and cancel.is_set():
            status = "cancelled"
            return False
        if lived >= budget:
            if "budget_exceeded" not in anomalies:
                anomalies.append("budget_exceeded")
            return False
        clock["now"] += timedelta(minutes=minutes)
        lived += 1
        try:
            being.tick()
        except EngineError as error:
            errors += 1
            anomalies.append(f"engine_error: {error}")
            if errors >= protocol["stop"].get("max_engine_errors", 3):
                status = "stopped"
                return False
        return True

    def play(script: list[dict]) -> None:
        for step in script:
            if "say" in step:
                hint = {k: step[k] for k in ("key", "outcome") if k in step}
                being.hear(step["say"], appraisal=hint or None)
                if not tick():
                    return
            elif "ticks" in step:
                for _ in range(step["ticks"]):
                    if not tick():
                        return
            elif "idle" in step:
                if not tick(step["idle"]):
                    return
            elif "wave" in step:  # evaluated on a separate copy; the life itself goes on untouched
                waves.append(wave_probe(clone, run_dir, protocol, condition, seed, step["wave"], clock["now"]))
            elif step.get("sleep"):
                if first_sleep["at"] == "9999":
                    first_sleep["at"] = clock["now"].isoformat(timespec="seconds")
                being.sleep_requested = not condition.get("skip_sleep")  # skipped: an ordinary moment instead
                if not tick():
                    return

    first_sleep = {"at": "9999"}  # the virtual time of the first scripted sleep, taken or skipped
    waves: list[dict] = []
    collector.mark("phase", name="history", script=condition.get("history"))
    play(HISTORIES[condition["history"]] + list(protocol["history"]))
    if status == "done":
        # Same random stream for every copy from here on: what differs in the probe is the
        # state each copy carries, not where its dice happened to be.
        # What is left, when the history ends, of the memories formed before the first sleep: their strength once the
        # time elapsed is applied. Computed on copies; the clone's memories are not touched.
        early = [life.memory.open(m.id) for m in life.memory.headers() if m.date <= first_sleep["at"]]
        for memory in early:
            decay(memory, clock["now"])
        collector.mark("memory_census", n=len(early),
                       mean_strength=round(sum(m.strength for m in early) / len(early), 6) if early else None,
                       complete=sum(1 for m in early if m.state == "complete"))
        being.rng.seed(seed * 7919 + 1)
        if hasattr(engine, "rng"):
            engine.rng.seed(seed * 7919 + 2)
        collector.mark("phase", name="probe")
        if condition.get("perturb"):  # the engine's rule changes here. The being is told nothing.
            engine.perturbed = True
            collector.mark("intervention", **new(
                "Intervention", run_id=run_id, target="clone", kind="masked_perturbation",
                changes={"engine_rule": condition["perturb"]}, reason="masked change of the engine's rule",
                approved_by_human=True, on_clone=True, restored=None))
        play(protocol["probe"])
        collector.mark("modules_census",
                       learner_parameters=being.adapter.parameters() if being.adapter else None,
                       learner_experts=len(being.adapter.experts) if being.adapter else None)
    records, _found = read_journal(journal.path)
    anomalies += check_journal(journal.path)
    run = new("Run", run_id=run_id, experiment_id=experiment_id, condition=condition["name"], seed=seed,
              clone_id=run_id, status=status, moments=lived,
              metrics=metrics.compute(records, run_id) if status == "done" else {},
              journal_sha256=journal_hash(journal.path), anomalies=anomalies)
    run_dir.joinpath("run.json").write_text(json.dumps(run, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    run_dir.joinpath("behaviour.json").write_text(json.dumps(metrics.behaviour_vector(records)), encoding="utf-8")
    if waves:
        run_dir.joinpath("waves.json").write_text(json.dumps(waves), encoding="utf-8")
    return run


def wave_probe(clone: Path, run_dir: Path, protocol: dict, condition: dict, seed: int, wave: int, now: datetime) -> dict:
    """Copy a life as it is now and play the interim probe on the copy. Returns the copy's behaviour vector."""
    folder = run_dir / "waves" / f"wave-{wave}"
    copy_life(clone, folder / "copy.life")
    life = Life(folder / "copy.life")
    clock = {"now": now}
    engine = _engine(protocol, condition, seed * 7919 + 100 + wave)
    being = Being(life, engine, rng=random.Random(seed * 7919 + 200 + wave), clock=lambda: clock["now"],
                  events=EventStream(folder / "copy.life" / "events.log"))
    journal = Journal(folder / "journal.jsonl", run_id=f"{run_dir.name}-wave{wave}", life_id="T0", clone_id=run_dir.name)
    collector = Collector(journal, lambda: round((clock["now"] - START).total_seconds() / 60, 2))
    being.events.subscribe(collector)
    collector.mark("phase", name="probe")
    anomalies = []
    for step in protocol.get("interim_probe") or []:
        try:
            if "say" in step:
                being.hear(step["say"])
                clock["now"] += timedelta(minutes=1)
                being.tick()
            for _ in range(step.get("ticks", 0)):
                clock["now"] += timedelta(minutes=1)
                being.tick()
        except EngineError as error:
            anomalies.append(f"engine_error: {error}")
    records, _found = read_journal(journal.path)
    shutil.rmtree(folder / "copy.life")  # the copy has served; its journal is kept
    return {"wave": wave, "behaviour": metrics.behaviour_vector(records), "journal_sha256": journal_hash(journal.path),
            "anomalies": anomalies}


# -- results -------------------------------------------------------------------------------

def summarise(folder: Path, experiment: dict, protocol: dict, exclude: set | None = None) -> dict:
    """The table of a campaign. The unit is the seed: one group of copies of T0, one per condition."""
    runs: dict[tuple[str, int], dict] = {}
    vectors: dict[tuple[str, int], list[float]] = {}
    for entry in experiment["runs"]:
        run_dir = folder / "runs" / entry["run_id"]
        if entry["status"] == "done":
            runs[(entry["condition"], entry["seed"])] = json.loads((run_dir / "run.json").read_text(encoding="utf-8"))
            vectors[(entry["condition"], entry["seed"])] = json.loads((run_dir / "behaviour.json").read_text())
    names = [c["name"] for c in protocol["conditions"]]
    reference = protocol["reference"]
    seeds = [s for s in protocol["seeds"] if all((name, s) in runs for name in names) and s not in (exclude or ())]
    evidence: dict[str, dict] = {}

    def cite(evidence_id, kind, statement, value, level, run_id=None):
        evidence[evidence_id] = new("EvidenceReference", evidence_id=evidence_id, kind=kind, run_id=run_id,
                                    experiment_id=experiment["experiment_id"], statement=statement,
                                    value=value, level=level)

    table: dict[str, dict] = {}
    for name in names:
        table[name] = {}
        for metric_id, definition in metrics.DEFINITIONS.items():
            if metric_id == "h5.heldout_divergence":
                continue
            results = [runs[(name, s)]["metrics"][metric_id] for s in seeds]
            values = [r["value"] for r in results if r["computable"]]
            reasons = sorted({r["reason"] for r in results if not r["computable"]})
            table[name][metric_id] = {
                "values": [r["value"] for r in results], "n_units": len(values),
                "mean": None if not values else round(mean(values), 6),
                "sd": None if sd(values) is None else round(sd(values), 6),
                "not_computable": reasons, "level": definition["level"], "unit": definition["unit"]}
            for r in results:
                cite(r["evidence_id"], "metric", f"{metric_id} in condition {name}", r["value"],
                     definition["level"], r["run_id"])

    comparisons = []
    for name in names:
        if name == reference or reference is None:
            continue
        for metric_id in table[name]:
            pairs = [(runs[(reference, s)]["metrics"][metric_id], runs[(name, s)]["metrics"][metric_id]) for s in seeds]
            usable = [(a["value"], b["value"]) for a, b in pairs if a["computable"] and b["computable"]]
            if not usable:
                continue
            evidence_id = f"cmp:{experiment['experiment_id']}:{metric_id}:{name}"
            row = {"metric_id": metric_id, "condition": name, "reference": reference, "evidence_id": evidence_id,
                   "level": metrics.DEFINITIONS[metric_id]["level"],
                   **paired([a for a, _ in usable], [b for _, b in usable])}
            comparisons.append(row)
            cite(evidence_id, "comparison", f"{metric_id}: {name} minus {reference}, paired by seed",
                 row["mean_difference"], row["level"])

    # H5: how far each condition's behaviour on the held-out probe is from the reference, unit by unit,
    # against how far a twin with the same history is. Only the excess over the twin counts.
    divergence = []
    twin = next((c["name"] for c in protocol["conditions"] if c.get("seed_offset")), None)
    if reference:
        floor = [metrics.distance(vectors[(reference, s)], vectors[(twin, s)]) for s in seeds] if twin else None
        for name in names:
            if name in (reference, twin):
                continue
            raw = [metrics.distance(vectors[(reference, s)], vectors[(name, s)]) for s in seeds]
            evidence_id = f"h5:{experiment['experiment_id']}:{name}"
            row = {"metric_id": "h5.heldout_divergence", "condition": name, "reference": reference,
                   "evidence_id": evidence_id, "distances": raw, "mean_distance": None if not raw else round(mean(raw), 6),
                   "twin": twin, "twin_distances": floor, "level": "function",
                   "excess_over_twin": paired(floor, raw) if floor else None}
            divergence.append(row)
            cite(evidence_id, "divergence", f"held-out behavioural distance of {name} from {reference}"
                 + (", minus the distance of a twin life" if floor else " (no twin: noise floor unknown)"),
                 row["excess_over_twin"]["mean_difference"] if floor else row["mean_distance"], "function")

    core = {"conditions": table, "comparisons": [{k: v for k, v in row.items() if k != "evidence_id"} for row in comparisons],
            "divergence": [{k: v for k, v in row.items() if k != "evidence_id"} for row in divergence],
            "units": seeds, "protocol_sha256": protocol["sha256"],
            "baseline_snapshot_sha256": experiment["baseline_snapshot_sha256"]}
    return {
        "experiment_id": experiment["experiment_id"], "protocol_id": protocol["protocol_id"],
        "protocol_version": protocol["protocol_version"], "protocol_sha256": protocol["sha256"],
        "baseline_snapshot_sha256": experiment["baseline_snapshot_sha256"], "code_commit": code_commit(),
        "lab_version": LAB_VERSION, "metrics_version": metrics.METRICS_VERSION, "engine": protocol["engine"],
        "unit": "seed (one group of copies of T0, one copy per condition)", "units": seeds,
        "units_planned": len(protocol["seeds"]), "reference": reference, "conditions": table,
        "comparisons": comparisons, "divergence": divergence, "evidence": evidence,
        "anomalies": experiment["anomalies"], "results_sha256": digest(core), "computed_utc": utc_now(),
    }


def summarise_longitudinal(folder: Path, experiment: dict, protocol: dict) -> dict:
    """EXP-10: the preregistered exclusions, the ordinary table, then the trajectory over the waves."""
    names = [c["name"] for c in protocol["conditions"]]
    excluded: dict[int, list[str]] = {}
    for entry in experiment["runs"]:
        run_dir = folder / "runs" / entry["run_id"]
        reason = None
        if entry["status"] != "done":
            reason = f"{entry['condition']}: {entry['status']}"
        else:
            run = json.loads((run_dir / "run.json").read_text(encoding="utf-8"))
            if "budget_exceeded" in run["anomalies"]:
                reason = f"{entry['condition']}: budget_exceeded"
        if reason:
            excluded.setdefault(entry["seed"], []).append(reason)
    results = summarise(folder, experiment, protocol, exclude=set(excluded))
    seeds = results["units"]
    load = lambda name, s: json.loads((folder / "runs" / f"{experiment['experiment_id']}-{name}-{s}" / "waves.json").read_text())  # noqa: E731
    vectors = {(name, s): {w["wave"]: w["behaviour"] for w in load(name, s)} for name in names for s in seeds}
    final = {(name, s): json.loads((folder / "runs" / f"{experiment['experiment_id']}-{name}-{s}" / "behaviour.json").read_text())
             for name in names for s in seeds}
    waves = sorted({w for v in vectors.values() for w in v})
    evidence = results["evidence"]

    def row(label, get):
        a_b = [metrics.distance(get("A", s), get("B", s)) for s in seeds]
        twin = [metrics.distance(get("A", s), get("A_twin", s)) for s in seeds]
        a_b_off = [metrics.distance(get("A_no_affect", s), get("B_no_affect", s)) for s in seeds]
        out = {"when": label, "distance_B_A": a_b, "distance_twin": twin, "distance_B_A_no_affect": a_b_off,
               "excess_over_twin": paired(twin, a_b) if seeds else None,
               "affect_on_divergence": paired(a_b_off, a_b) if seeds else None}
        for key, metric in (("excess_over_twin", "h5.wave_divergence"), ("affect_on_divergence", "h7.affect_on_divergence")):
            eid = f"h5:{experiment['experiment_id']}:{label}:{key}"
            out[key + "_evidence"] = eid
            if out[key]:
                evidence[eid] = new("EvidenceReference", evidence_id=eid, kind="divergence", run_id=None,
                                    experiment_id=experiment["experiment_id"], statement=f"{metric} at {label}",
                                    value=out[key]["mean_difference"], level="function")
        return out

    trajectory = [row(f"wave{w}", lambda n, s, w=w: vectors[(n, s)][w]) for w in waves]
    sealed = row("sealed", lambda n, s: final[(n, s)])
    interval = (sealed["excess_over_twin"] or {}).get("interval_95")
    met = None if interval is None else interval[0] > 0
    longitudinal = {"waves": trajectory, "sealed": sealed, "units": seeds,
                    "excluded": {str(k): v for k, v in sorted(excluded.items())},
                    "primary_criterion_met": met,
                    "note": "computed by the preregistered rule; a verdict on a hypothesis is given only by a person"}
    results["longitudinal"] = longitudinal
    core = {"conditions": results["conditions"], "longitudinal": longitudinal, "units": seeds,
            "protocol_sha256": protocol["sha256"], "baseline_snapshot_sha256": experiment["baseline_snapshot_sha256"]}
    results["results_sha256"] = digest(core)
    return results


# -- EXP-09: the engine adapted by a life -------------------------------------------------------

def engine_results(folder: Path, experiment: dict, protocol: dict, models_dir: Path) -> dict:
    """Run the comparison of freewill.learning.compare on the copy T0 and shape it as the lab's results."""
    from freewill import models
    from freewill.learning import compare
    life = Life(folder / "T0.life")
    engine = life.identity.get("engine", {})
    model = models.find(str(engine.get("model"))) if engine.get("kind") == "embedded" else None
    if model is None or not model.get("trainable"):
        raise LabError("the life of this campaign does not converse with a model that can learn")
    store = models.ModelStore(models_dir)
    if not store.training_installed(model):
        raise LabError("the trainable base of this model is not on this computer")
    found = compare.compare(life.path, model, store, runtime_model=store.paths(model)["model"]
                            if store.installed(model) else None)
    units = found["held_out_sha256"]
    evidence: dict[str, dict] = {}
    conditions: dict[str, dict] = {}
    for name, row in found["conditions"].items():
        values = found["per_item"][name]
        conditions[name] = {
            "h4.engine_heldout_nll": {"values": values, "n_units": len(values), "mean": row["life_held_out_mean"],
                                      "sd": sd(values), "not_computable": [], "level": "function", "unit": "nats per token"},
            "h4.engine_reference_nll": {"values": [row["reference_mean"]], "n_units": 1, "mean": row["reference_mean"],
                                        "sd": None, "not_computable": [], "level": "function", "unit": "nats per token"},
            "h4.engine_delta_frobenius": {"values": [row["delta_frobenius"]], "n_units": 1, "mean": row["delta_frobenius"],
                                          "sd": None, "not_computable": [], "level": "mechanism", "unit": "Frobenius norm"}}
    comparisons = []
    for row in found["comparisons"]:
        evidence_id = f"cmp:{experiment['experiment_id']}:h4.engine_heldout_nll:{row['condition']}-{row['reference']}"
        shaped = {"metric_id": "h4.engine_heldout_nll", "condition": row["condition"], "reference": row["reference"],
                  "evidence_id": evidence_id, "level": "function",
                  **{k: v for k, v in row.items() if k not in ("metric", "condition", "reference")}}
        comparisons.append(shaped)
        evidence[evidence_id] = new("EvidenceReference", evidence_id=evidence_id, kind="comparison", run_id=None,
                                    experiment_id=experiment["experiment_id"],
                                    statement=f"held-out loss: {row['condition']} minus {row['reference']}, paired by item",
                                    value=row["mean_difference"], level="function")
    core = {"conditions": conditions, "comparisons": [{k: v for k, v in c.items() if k != "evidence_id"} for c in comparisons],
            "units": units, "adapter_sha256": found["adapter_sha256"], "runtime_check": found["runtime_check"]}
    return {
        "experiment_id": experiment["experiment_id"], "protocol_id": protocol["protocol_id"],
        "protocol_version": protocol["protocol_version"], "protocol_sha256": protocol["sha256"],
        "baseline_snapshot_sha256": experiment["baseline_snapshot_sha256"], "code_commit": code_commit(),
        "lab_version": LAB_VERSION, "metrics_version": metrics.METRICS_VERSION,
        "engine": {"kind": "embedded", "model": model["id"], "adapter": found["version"], "adapter_sha256": found["adapter_sha256"]},
        "unit": "held-out item of the life", "units": units, "units_planned": len(units), "reference": "base",
        "conditions": conditions, "comparisons": comparisons, "divergence": [], "evidence": evidence,
        "engine_comparison": {k: found[k] for k in ("control_training", "runtime_check", "behaviour", "notes")},
        "anomalies": experiment["anomalies"], "results_sha256": digest(core), "computed_utc": utc_now()}
