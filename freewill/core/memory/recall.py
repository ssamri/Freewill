"""Recall along three paths: by subject, by neighbourhood, by chance.

Their proportions depend on who is recalling. Directed thought stays close to
the subject; the subconscious follows associations; dreams draw mostly at
random.
"""

from __future__ import annotations

import random
import re
import unicodedata
from dataclasses import dataclass

from freewill.core.memory.store import Memory, MemoryStore
from freewill.core.memory.strength import revive


@dataclass(frozen=True)
class Mix:
    subject: float
    neighbourhood: float
    chance: float

    def loosened(self, association: float) -> "Mix":
        """Shift weight from subject to chance for a freely associating temperament."""
        shift = (association - 0.5) * 0.3 * self.subject
        return Mix(self.subject - shift, self.neighbourhood, self.chance + shift)


CONSCIOUS = Mix(0.80, 0.15, 0.05)
SUBCONSCIOUS = Mix(0.30, 0.45, 0.25)
DREAM = Mix(0.10, 0.30, 0.60)

_STOP = {
    "the", "and", "for", "that", "this", "with", "you", "are", "was", "but", "not", "what",
    "about", "tell", "have", "has", "had", "from", "your", "they", "them", "there", "were",
    "can", "did", "does", "how", "why", "who", "when", "into", "than", "then", "just",
    "moi", "toi", "lui", "tes", "nos", "vos", "leur", "aux", "par", "plus", "tout", "tous",
    "ete", "etre", "avoir", "fait", "dit", "comme", "quoi", "quand",
    "les", "des", "une", "que", "qui", "est", "pas", "pour", "dans", "avec", "sur", "mais",
    "elle", "ils", "nous", "vous", "mon", "ton", "son", "ses", "mes", "ces", "cette",
}


def tokens(text: str) -> set[str]:
    plain = unicodedata.normalize("NFKD", text.lower()).encode("ascii", "ignore").decode()
    return {word for word in re.findall(r"[a-z0-9]{3,}", plain) if word not in _STOP}


def _weighted_pick(rng: random.Random, pool: list[Memory], weights: list[float], n: int) -> list[Memory]:
    picked: list[Memory] = []
    pool, weights = list(pool), list(weights)
    while pool and len(picked) < n:
        if sum(weights) <= 0:
            break
        choice = rng.choices(range(len(pool)), weights=weights)[0]
        picked.append(pool.pop(choice))
        weights.pop(choice)
    return picked


def recall(
    store: MemoryStore,
    cue: str,
    mix: Mix,
    *,
    k: int = 3,
    rng: random.Random | None = None,
    active: tuple[str, ...] = (),
    touch: bool = True,
    bias=None,
    now=None,
) -> list[tuple[Memory, str]]:
    """Return up to `k` memories with the path that brought each one back.

    Only headers are read to choose. The chosen memories are then opened in
    full, strengthened, and saved (unless `touch` is False).
    `active` holds the ids of memories recently in mind; the neighbourhood
    path starts from them. `bias`, if given, maps a memory to a weight close
    to 1 that multiplies its score on every path; it reorders candidates that
    relevance has already selected and brings back nothing by itself.
    """
    rng = rng or random.Random()
    headers = store.headers()
    if not headers:
        return []
    weigh = bias or (lambda memory: 1.0)
    by_id = {memory.id: memory for memory in headers}
    total = mix.subject + mix.neighbourhood + mix.chance
    chosen: dict[str, str] = {}

    def take(candidates: list[Memory], weights: list[float], n: int, path: str) -> None:
        pool = [(m, w) for m, w in zip(candidates, weights) if m.id not in chosen and w > 0]
        for memory in _weighted_pick(rng, [m for m, _ in pool], [w for _, w in pool], n):
            chosen[memory.id] = path

    # By subject: overlap of words between the cue and title, summary, tags.
    cue_words = tokens(cue)
    scored = []
    for memory in headers:
        # A word in the title counts double: the title is what the memory is about.
        words = tokens(f"{memory.summary} {' '.join(memory.tags)}")
        title = tokens(memory.title)
        overlap = len(cue_words & (words | title)) + len(cue_words & title)
        if overlap:
            scored.append((memory, overlap * (0.5 + memory.strength) * weigh(memory)))
    scored.sort(key=lambda pair: pair[1], reverse=True)
    n_subject = round(k * mix.subject / total)
    for memory, _ in scored[:n_subject]:
        chosen[memory.id] = "subject"

    # By neighbourhood: links from, and tags shared with, what is already in mind.
    seeds = [by_id[i] for i in (*active, *chosen) if i in by_id]
    neighbours: dict[str, float] = {}
    for seed in seeds:
        for link in seed.links:
            if link in by_id:
                neighbours[link] = neighbours.get(link, 0) + 1.0
        for memory in headers:
            if memory.id == seed.id:
                continue
            shared = len(set(seed.tags) & set(memory.tags))
            if seed.id in memory.links:
                shared += 2
            if memory.compartment == seed.compartment:
                shared += 0.5
            if shared:
                neighbours[memory.id] = neighbours.get(memory.id, 0) + 0.5 * shared
    n_neighbour = round(k * mix.neighbourhood / total)
    take([by_id[i] for i in neighbours], [w * weigh(by_id[i]) for i, w in neighbours.items()],
         n_neighbour, "neighbourhood")

    # By chance: any memory, weighted by strength and importance. Fills the rest.
    take(headers, [m.strength * (0.3 + m.importance) * weigh(m) for m in headers], k - len(chosen), "chance")

    result = []
    for memory_id, path in list(chosen.items())[:k]:
        memory = store.open(memory_id)
        if touch:
            revive(memory, now)
            store.save(memory)
        result.append((memory, path))
    return result
