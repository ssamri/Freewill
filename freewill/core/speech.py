"""What is said, and what is only thought.

The conversation holds only what the being says to the person. Everything else
that passes through its mind (what reached its attention, its reasons, its
thoughts) belongs to the Subconscious view and is never lost.

An engine is asked to keep the two apart: "thought" for what it thinks, "say"
for what it says aloud. A model does not always do so. Seen with small local
models: the reasoning a model writes before answering (between <think> tags)
ends up in the answer, and, in a moment nobody spoke to it, the model fills
"say" with the very thought it is having, or with the content that rose from
its subconscious, as if speaking were how thinking is written down.

This module tells the two apart with plain rules, the same for every engine.
It moves text from what is said to what is thought; it never invents, rewrites
or drops a word.
"""

from __future__ import annotations

import re

# Reasoning blocks some models write before or inside their answer.
_BLOCK = re.compile(r"<(think|thinking|reasoning|thought)>(.*?)</\1>", re.IGNORECASE | re.DOTALL)
# An opening tag with no closing one: everything after it is reasoning.
_OPEN = re.compile(r"<(think|thinking|reasoning|thought)>(.*)$", re.IGNORECASE | re.DOTALL)
# A closing tag with no opening one (the opening was in the prompt): everything before it is reasoning.
_CLOSE = re.compile(r"^(.*?)</(think|thinking|reasoning|thought)>", re.IGNORECASE | re.DOTALL)
# Stage directions written as speech: *thinks*, (thinking: ...), [pensée] ...
_DIRECTION = re.compile(
    r"^\s*(?:[\*_\(\[]\s*)?(?:thinking|thought|inner thought|inner voice|to myself|"
    r"je pense|pensée|pensée intérieure|pour moi-même|en moi-même|à moi-même)\s*(?:[:\-–—]|[\*_\)\]])",
    re.IGNORECASE)


def strip_reasoning(text: str) -> tuple[str, str]:
    """Split `text` into (what remains, the reasoning set aside). Both are stripped."""
    if not text:
        return "", ""
    kept: list[str] = []

    def take(match: re.Match) -> str:
        kept.append(match.group(2).strip())
        return " "
    rest = _BLOCK.sub(take, text)
    match = _CLOSE.match(rest)
    if match and "<" not in match.group(1):
        kept.insert(0, match.group(1).strip())
        rest = rest[match.end():]
    match = _OPEN.search(rest)
    if match:
        kept.append(match.group(2).strip())
        rest = rest[:match.start()]
    return re.sub(r"[ \t]{2,}", " ", rest).strip(), "\n".join(part for part in kept if part)


def _plain(text: str) -> str:
    return "".join(c for c in (text or "").lower() if c.isalnum())


def same_words(a: str, b: str) -> bool:
    """True if `a` and `b` say the same thing, letter for letter, or one holds the whole of the other
    (a model that writes its thought in "say" often adds or drops a few words around it)."""
    pa, pb = _plain(a), _plain(b)
    if not pa or not pb:
        return False
    if pa == pb:
        return True
    short, long = sorted((pa, pb), key=len)
    return len(short) >= 12 and short in long and len(short) >= 0.6 * len(long)


def is_stage_direction(text: str) -> bool:
    """True if the text presents itself as a thought rather than as words to someone."""
    return bool(_DIRECTION.match(text or ""))


def separate(say: str, *, thought: str, content: str, spoken_to: bool) -> tuple[str, str, str]:
    """Return (what is said, what is thought, why some words were kept inside, or "").

    `content` is what reached the being's attention; `spoken_to` is True when it was something the
    person said. When the person spoke, an answer is expected and is left to the conversation, minus
    any reasoning written into it. When nobody spoke, words that only repeat the thought, or the content
    that rose from the subconscious, or that present themselves as a thought, are a thought: they go to
    the Subconscious, never to the conversation.
    """
    said, reasoning = strip_reasoning(say)
    inner = reasoning
    why = "reasoning" if reasoning else ""
    if said and is_stage_direction(said):
        inner, said, why = "\n".join(p for p in (inner, said) if p), "", "stage_direction"
    if said and not spoken_to and (same_words(said, thought) or same_words(said, content)):
        why = "repeats_thought" if same_words(said, thought) else "repeats_content"
        inner, said = "\n".join(p for p in (inner, said) if p), ""
    if inner and not same_words(inner, thought):
        thought = "\n".join(p for p in (thought, inner) if p)
    return said, thought, why
