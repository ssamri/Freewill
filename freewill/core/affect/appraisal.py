"""Appraisal: what an event means for this individual, given its own history.

An event is described by observable facts (what kind it is, what need it
touches, what it relieved, what was recalled with it). The appraisal turns
them into bounded features, each with a traceable cause. No sentence produced
by a language model is read here: the same event appraised by two individuals
differs only through their needs, their predictions and their memories.
"""

from __future__ import annotations

import re
import zlib
from dataclasses import dataclass, field

from freewill.core.affect.state import AffectError, clamp, finite
from freewill.core.memory.recall import tokens

KINDS = ("stage", "outcome", "error", "refusal")
_KEY = re.compile(r"^[a-z0-9][a-z0-9:_-]{0,39}$")

# A deliberately crude, lexical reading of what kind of message this is. It
# sorts events into contexts; it assigns no value to them.
_CONTRADICTION = re.compile(
    r"\b(no|not|wrong|incorrect|actually|mistaken|disagree|non|faux|fausse|erreur|inexact|"
    r"en fait|pas vrai|tu te trompes|pas d'accord)\b", re.IGNORECASE)


def message_key(text: str, has_attachments: bool = False) -> str:
    if has_attachments:
        return "message:attachment"
    if _CONTRADICTION.search(text):
        return "message:contradiction"
    if text.rstrip().endswith("?"):
        return "message:question"
    return "message:statement"


def stage_key(source: str, text: str = "", has_attachments: bool = False) -> str:
    if source == "message":
        return message_key(text, has_attachments)
    return valid_key("source:" + re.sub(r"[^a-z0-9:_-]", "-", source.lower())[:32])


def valid_key(key) -> str:
    if not isinstance(key, str) or not _KEY.match(key):
        raise AffectError(f"not a valid context key: {key!r}")
    return key


def fingerprint(text: str) -> list[int]:
    """The words of a content as short hashes: enough to measure novelty, not to read it back."""
    return sorted({zlib.crc32(word.encode()) & 0xFFFFF for word in tokens(text)})[:64]


@dataclass(frozen=True)
class Observation:
    """What happened, in observable terms. Built by the life loop, never by the language model."""

    kind: str                      # one of KINDS
    key: str                       # the context: "message:question", "source:reminiscence", …
    text: str = ""                 # read for novelty only; never stored or logged
    relevance: float = 0.0         # level of the need this event touches, 0 to 1
    relief: float = 0.0            # how much need was relieved by what followed, 0 to 1
    accepted: bool | None = None   # outcome: the conscious welcomed it, or not
    success: bool = True           # the moment completed without error
    social: bool = False           # someone is speaking, or being spoken to
    outcome: float | None = None   # optional external evaluation, -1 to 1, validated and bounded
    fatigue: float = 0.0
    waiting: int = 0               # messages waiting to be heard
    traces: tuple[dict, ...] = ()  # affective traces of the memories recalled with this event

    def __post_init__(self) -> None:
        if self.kind not in KINDS:
            raise AffectError(f"unknown kind of observation: {self.kind!r}")
        valid_key(self.key)
        for name in ("relevance", "relief", "fatigue"):
            object.__setattr__(self, name, clamp(finite(getattr(self, name), name), 0.0, 1.0))
        if self.outcome is not None:
            object.__setattr__(self, "outcome", clamp(finite(self.outcome, "outcome"), -1.0, 1.0))
        object.__setattr__(self, "waiting", max(0, int(finite(self.waiting, "waiting"))))


@dataclass
class Appraisal:
    kind: str
    key: str
    novelty: float = 0.0           # how unlike recent contents this one is
    surprise: float = 0.0          # prediction error: how unexpected this context or outcome was
    relevance: float = 0.0         # how much it matters to a current need
    congruence: float = 0.0        # signed: did it serve (+) or thwart (-) what was at stake
    control: float = 0.6           # estimated control, from how recent moments went
    coherence: float = 0.7         # agreement with expectation
    reliability: float = 0.0       # how much this appraisal can be trusted, from experience of this context
    memory_valence: float = 0.0    # what the recalled memories carried
    memory_matches: int = 0
    association: float = 0.0       # what experience of this context has consolidated
    social: bool = False
    load: float = 0.0
    causes: list[str] = field(default_factory=list)

    def features(self) -> dict:
        return {name: round(getattr(self, name), 4) for name in (
            "novelty", "surprise", "relevance", "congruence", "control", "coherence",
            "reliability", "memory_valence", "association", "load")} | {"memory_matches": self.memory_matches}


@dataclass
class Model:
    """The small predictive model an individual builds of its own life.

    `expect` is how often each context reaches the stage; `accept` how often
    it is welcomed; `success` how often moments complete; `recent` what the
    last contents were made of. All of it is learned from what happened.
    """

    expect: dict[str, float] = field(default_factory=dict)
    accept: dict[str, float] = field(default_factory=dict)
    seen: dict[str, int] = field(default_factory=dict)
    success: float = 0.8
    recent: list[list[int]] = field(default_factory=list)

    RATE = 0.12
    RECENT = 12

    @classmethod
    def from_dict(cls, data: dict | None) -> "Model":
        data = data or {}
        model = cls()
        for name in ("expect", "accept"):
            given = data.get(name) or {}
            getattr(model, name).update({valid_key(k): clamp(finite(v, name), 0.0, 1.0) for k, v in given.items()})
        model.seen = {valid_key(k): max(0, int(finite(v, "seen"))) for k, v in (data.get("seen") or {}).items()}
        model.success = clamp(finite(data.get("success", 0.8), "success"), 0.0, 1.0)
        model.recent = [[int(x) for x in item][:64] for item in (data.get("recent") or [])][-cls.RECENT:]
        return model

    def to_dict(self) -> dict:
        return {"expect": {k: round(v, 4) for k, v in self.expect.items()},
                "accept": {k: round(v, 4) for k, v in self.accept.items()},
                "seen": dict(self.seen), "success": round(self.success, 4), "recent": self.recent}

    def reliability(self, key: str) -> float:
        n = self.seen.get(key, 0)
        return n / (n + 3)

    # -- learning from what happened ---------------------------------------------

    def learn_stage(self, key: str, text: str) -> None:
        for known in list(self.expect):
            self.expect[known] *= 1 - self.RATE
        self.expect[key] = self.expect.get(key, 0.0) + self.RATE
        self.seen[key] = min(100000, self.seen.get(key, 0) + 1)
        if text:
            self.recent = (self.recent + [fingerprint(text)])[-self.RECENT:]
        if len(self.expect) > 200:  # forget the rarest contexts rather than grow without bound
            for known in sorted(self.expect, key=self.expect.get)[:50]:
                self.expect.pop(known), self.seen.pop(known, None), self.accept.pop(known, None)

    def learn_outcome(self, key: str, accepted: bool | None, success: bool) -> None:
        if accepted is not None:
            before = self.accept.get(key, 0.5)
            self.accept[key] = before + self.RATE * ((1.0 if accepted else 0.0) - before)
        self.success += self.RATE * ((1.0 if success else 0.0) - self.success)


def appraise(observation: Observation, model: Model, associations: dict) -> Appraisal:
    """Appraise one observation against what this individual expects and remembers."""
    key = observation.key
    result = Appraisal(kind=observation.kind, key=key, social=observation.social,
                       relevance=observation.relevance, control=model.success)
    causes = result.causes
    result.reliability = model.reliability(key)
    causes.append(f"reliability {result.reliability:.2f}: this context was met {model.seen.get(key, 0)} times")

    if observation.kind == "stage":
        words = set(fingerprint(observation.text))
        if words and model.recent:
            closest = max(len(words & set(past)) / len(words | set(past)) for past in model.recent if past) \
                if any(model.recent) else 0.0
            result.novelty = 1.0 - closest
            causes.append(f"novelty {result.novelty:.2f}: closest of {len(model.recent)} recent contents shares {closest:.2f}")
        elif words:
            result.novelty = 1.0
            causes.append("novelty 1.00: nothing recent to compare with")
        total = sum(model.expect.values())
        expected = model.expect.get(key, 0.0) / total if total > 0 else 0.0
        result.surprise = 1.0 - expected
        result.coherence = 1.0 - 0.5 * result.surprise
        causes.append(f"surprise {result.surprise:.2f}: this context was expected with probability {expected:.2f}")
        if observation.relevance:
            causes.append(f"relevance {observation.relevance:.2f}: level of the need this touches")
    elif observation.kind == "outcome":
        if observation.accepted is not None:
            predicted = model.accept.get(key, 0.5)
            result.surprise = abs((1.0 if observation.accepted else 0.0) - predicted)
            causes.append(f"surprise {result.surprise:.2f}: welcome predicted at {predicted:.2f}, "
                          f"observed {'yes' if observation.accepted else 'no'}")
        result.coherence = 1.0 - result.surprise
        result.congruence = observation.relief
        if observation.relief:
            causes.append(f"congruence +{observation.relief:.2f}: a need was relieved")
        if observation.outcome is not None:
            result.congruence = clamp(result.congruence + observation.outcome, -1.0, 1.0)
            causes.append(f"congruence {observation.outcome:+.2f}: external evaluation of the result")
    elif observation.kind == "error":
        result.congruence, result.coherence = -0.3, 0.5
        causes.append("congruence -0.30: the moment could not be completed")
    else:  # refusal by the kernel
        result.congruence, result.coherence = -0.2, 0.3
        causes.append("coherence 0.30: the kernel refused an effect")
    if not observation.success:
        result.control = clamp(model.success - 0.2, 0.0, 1.0)

    traces = [trace for trace in observation.traces if isinstance(trace, dict)]
    if traces:
        result.memory_valence = clamp(sum(clamp(float(t.get("v", 0.0)), -1, 1) for t in traces) / len(traces), -1, 1)
        result.memory_matches = len(traces)
        causes.append(f"memory {result.memory_valence:+.2f}: mean trace of {len(traces)} recalled memories")

    known = associations.get(key)
    if known:
        weight = known["n"] / (known["n"] + 3)
        result.association = clamp(known["valence"] * weight, -1.0, 1.0)
        causes.append(f"association {result.association:+.2f}: consolidated from {known['n']} past episodes of this context")

    result.load = clamp(0.6 * observation.fatigue + 0.4 * min(1.0, observation.waiting / 3), 0.0, 1.0)
    return result
