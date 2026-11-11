"""Sources of proposals.

Each generator emits a seed: a short content with a salience. Generators are
cheap and never call the engine; only what wins the stage is thought through.
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field

from freewill.core.genome import Genome
from freewill.core.kernel.constitution import founding_questions
from freewill.core.kernel.needs import Needs
from freewill.core.memory import SUBCONSCIOUS, DREAM, MemoryStore, recall
from freewill.core.subconscious.drift import Drift


@dataclass
class Proposal:
    source: str        # which generator, or "message" for something heard
    text: str
    salience: float
    memory_ids: tuple[str, ...] = field(default=())


_T = {
    "en": {
        "reminiscence": "A memory comes back: “{title}”. {summary}",
        "curiosity": "I want to understand something I do not understand yet.",
        "wonder": "A question I carry returns: {question}",
        "company": "I feel like talking with {other}.",
        "company_alone": "I feel like talking with someone.",
        "question": "{question}",
        "association": "Is there a link between “{a}” and “{b}”?",
        "drift": "Out of nowhere, I think of “{title}”.",
        "drift_empty": "My mind wanders, with nothing to hold on to yet.",
    },
    "fr": {
        "reminiscence": "Un souvenir me revient : « {title} ». {summary}",
        "curiosity": "J'ai envie de comprendre quelque chose que je ne comprends pas encore.",
        "wonder": "Une question que je porte revient : {question}",
        "company": "J'ai envie de parler avec {other}.",
        "company_alone": "J'ai envie de parler avec quelqu'un.",
        "question": "{question}",
        "association": "Y a-t-il un lien entre « {a} » et « {b} » ?",
        "drift": "Sans raison, je pense à « {title} ».",
        "drift_empty": "Mon esprit vagabonde, sans rien encore à quoi s'accrocher.",
    },
}


class Subconscious:
    def __init__(
        self,
        genome: Genome,
        store: MemoryStore,
        language: str,
        *,
        rng: random.Random | None = None,
        drift: Drift | None = None,
    ) -> None:
        self.genome = genome
        self.store = store
        self.t = _T.get(language, _T["en"])
        self.language = language
        self.rng = rng or random.Random()
        self.drift = drift or Drift(genome.seed)
        # How much each source has been welcomed so far. Learned from the
        # conscious mind's choices: what is dismissed speaks more softly.
        self.weights: dict[str, float] = {}
        # Research settings: sources switched off, and how wide the disorder is.
        self.silenced: set[str] = set()
        self.noise = 0.08

    # -- learning from the arbiter's choices ----------------------------------

    def learn(self, source: str, accepted: bool) -> None:
        current = self.weights.get(source, 1.0)
        target = 1.25 if accepted else 0.75
        self.weights[source] = round(min(1.5, max(0.5, current + 0.1 * (target - current))), 4)

    def _weigh(self, proposal: Proposal) -> Proposal:
        proposal.salience = round(
            max(0.0, min(1.0, proposal.salience * self.weights.get(proposal.source, 1.0))), 4
        )
        return proposal

    # -- generators ------------------------------------------------------------

    def proposals(
        self,
        needs: Needs,
        last_thought: str,
        recent: tuple[str, ...],
        active: tuple[str, ...],
        interlocutor: str | None,
    ) -> list[Proposal]:
        noise = lambda: self.rng.uniform(-self.noise, self.noise)  # noqa: E731
        out: list[Proposal] = []
        on = lambda source: source not in self.silenced  # noqa: E731

        # Reminiscence: something related, or merely nearby, resurfaces.
        mix = SUBCONSCIOUS.loosened(self.genome.association)
        for memory, _path in (recall(self.store, last_thought, mix, k=1, rng=self.rng,
                                     active=active, touch=False) if on("reminiscence") else ()):
            out.append(Proposal(
                "reminiscence",
                self.t["reminiscence"].format(
                    title=memory.title,
                    summary="" if memory.summary == memory.title else memory.summary,
                ).strip(),
                0.25 + 0.35 * memory.strength + 0.15 * memory.importance + noise(),
                (memory.id,),
            ))

        # Need: the most pressing one makes itself felt.
        name, level = needs.most_pressing()
        if not on("need"):
            pass
        elif name == "company":
            text = (self.t["company"].format(other=interlocutor) if interlocutor
                    else self.t["company_alone"])
        elif name == "wonder":
            text = self.t["wonder"].format(question=self.rng.choice(founding_questions(self.language)))
        else:
            text = self.t["curiosity"]
        if on("need"):
            out.append(Proposal(f"need:{name}", text, 0.9 * level + noise()))

        # Question: a founding question, with the pull of wonder.
        if on("question"):
            out.append(Proposal(
                "question",
                self.t["question"].format(question=self.rng.choice(founding_questions(self.language))),
                0.2 + 0.5 * needs.wonder * (0.5 + self.genome.curiosity) + noise(),
            ))

        # Association: two things recently in mind, brought together.
        if len(recent) >= 2 and on("association"):
            a, b = self.rng.sample(list(recent), 2)
            out.append(Proposal(
                "association",
                self.t["association"].format(a=_short(a), b=_short(b)),
                0.25 + 0.3 * self.genome.association + noise(),
            ))

        # Drift: deterministic disorder brings up something unrelated.
        x = self.drift.step()
        if not on("drift"):
            return [self._weigh(proposal) for proposal in out]
        drifted = recall(self.store, "", DREAM, k=1, rng=random.Random(int(x * 1e9)), touch=False)
        if drifted:
            memory = drifted[0][0]
            out.append(Proposal("drift", self.t["drift"].format(title=memory.title),
                                0.55 * x, (memory.id,)))
        else:
            out.append(Proposal("drift", self.t["drift_empty"], 0.3 * x))

        return [self._weigh(proposal) for proposal in out]


def _short(text: str, limit: int = 70) -> str:
    text = " ".join(text.split())
    return text if len(text) <= limit else text[: limit - 1].rstrip() + "…"
