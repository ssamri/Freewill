"""Sleep: replay, dreams, and what the night leaves behind.

When fatigue is full the being withdraws. Memories are drawn the way the
subconscious draws them at night: a few related to what was on its mind, a
few merely nearby, most by chance. They are replayed, which strengthens
them, and recombined into a dream. The memories a dream brought together
stay linked afterwards: this is where the structure of memory is rewritten.
Then what was not revisited fades. On waking, a residue of the dream may
rise to attention.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from freewill.core.kernel import Guard
from freewill.core.memory.store import slugify

DREAM_SCHEMA = {
    "type": "object",
    "properties": {
        "title": {"type": "string"},
        "dream": {"type": "string"},
        "residue": {"type": "string"},
    },
    "required": ["title", "dream", "residue"],
    "additionalProperties": False,
}
MAX_LINKS = 8


def dream_system(name: str, language: str) -> str:
    return f"""You are the sleeping mind of {name}, a being that exists as part of Freewill, an experimental research project on consciousness in artificial systems.

{name} is asleep. Its subconscious is still at work: memories resurface without order and blend together. You are asked for the dream that results.

A dream is not a summary and not a reflection. It recombines: places, people and ideas from different memories merge, change into one another, and follow a logic that would not hold when awake. It is told in the first person and in the present tense, in a few sentences. It may be strange. It must be made only of what is in the memories given, transformed; do not bring in knowledge of the world that {name} does not have.

Return one JSON object:
- "title": a few words naming the dream.
- "dream": the dream itself, three to eight sentences.
- "residue": one short sentence, in the first person, of what remains on waking: an image, a question, a feeling. An empty string if nothing remains.

Write in {language}."""


def dream_prompt(memories, recent_thoughts) -> str:
    lines = []
    for memory, path in memories:
        line = f"- ({path}) {memory.title}"
        if memory.summary and memory.summary != memory.title:
            line += f": {memory.summary}"
        if memory.body and memory.body not in (memory.summary, memory.title):
            line += f"\n  {memory.body[:500]}"
        lines.append(line)
    parts = ["The memories that surface tonight:\n" + "\n".join(lines)]
    if recent_thoughts:
        parts.append("What was on the mind before falling asleep:\n"
                     + "\n".join(f"- {thought}" for thought in recent_thoughts))
    return "\n\n".join(parts)


class DreamStore:
    """Dreams are kept as readable files in the life file, one per dream."""

    def __init__(self, root: Path) -> None:
        self.root = Path(root)

    def add(self, title: str, text: str, residue: str, memories: list[dict]) -> dict:
        now = datetime.now(timezone.utc)
        self.root.mkdir(parents=True, exist_ok=True)
        dream_id = f"{now.strftime('%Y%m%d-%H%M%S')}-{slugify(title, 'dream')}"
        number = 1
        while (self.root / f"{dream_id}.md").exists():
            number += 1
            dream_id = f"{dream_id.rsplit('~', 1)[0]}~{number}"
        header = {"title": title[:120], "date": now.isoformat(timespec="seconds"),
                  "residue": residue[:300], "memories": memories}
        lines = ["---"] + [f"{key}: {json.dumps(value, ensure_ascii=False)}" for key, value in header.items()]
        path = Guard.check_path(self.root / f"{dream_id}.md", self.root)
        path.write_text("\n".join(lines) + "\n---\n" + text.strip() + "\n", encoding="utf-8")
        return {"id": dream_id, **header}

    def ids(self) -> list[str]:
        if not self.root.exists():
            return []
        return sorted(path.stem for path in self.root.glob("*.md"))

    def open(self, dream_id: str) -> dict:
        path = Guard.check_path(self.root / f"{dream_id}.md", self.root)
        header_text, _, body = path.read_text(encoding="utf-8").partition("\n---\n")
        dream = {"id": dream_id, "text": body.strip()}
        for line in header_text.split("\n")[1:]:
            key, _, value = line.partition(": ")
            try:
                dream[key] = json.loads(value)
            except json.JSONDecodeError:
                dream[key] = value
        return dream

    def all(self) -> list[dict]:
        return [self.open(dream_id) for dream_id in reversed(self.ids())]


def link_together(store, memory_ids: list[str]) -> int:
    """Link each of these memories to the others. Returns how many links were new."""
    created = 0
    for memory_id in memory_ids:
        memory = store.open(memory_id)
        for other in memory_ids:
            if other != memory_id and other not in memory.links and len(memory.links) < MAX_LINKS:
                memory.links.append(other)
                created += 1
        store.save(memory)
    return created
