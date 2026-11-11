"""Strength of memories: decay with time, revival on recall, fading by stages."""

from __future__ import annotations

import math
from datetime import datetime, timezone

from freewill.core.memory.store import COMPLETE, CONDENSED, TRACE, Memory

# Days for an unimportant memory to lose half its strength. An important one
# decays up to four times more slowly.
BASE_HALF_LIFE_DAYS = 7.0
CONDENSE_BELOW = 0.35  # the account is lost; title and summary remain
TRACE_BELOW = 0.12     # only the title remains


def _parse(stamp: str) -> datetime | None:
    try:
        return datetime.fromisoformat(stamp)
    except (TypeError, ValueError):
        return None


def decay(memory: Memory, now: datetime | None = None) -> bool:
    """Weaken `memory` for the time elapsed since it was last alive in mind.

    Returns True if its state changed. Memories the being chose to keep do not
    decay.
    """
    if memory.kept:
        return False
    now = now or datetime.now(timezone.utc)
    last = _parse(memory.last_recall) or _parse(memory.date)
    if last is None:
        return False
    days = max(0.0, (now - last).total_seconds() / 86400)
    half_life = BASE_HALF_LIFE_DAYS * (1 + 3 * memory.importance)
    # The reference point moves forward, so decay is applied once per interval.
    memory.strength = round(memory.strength * math.pow(0.5, days / half_life), 4)
    memory.last_recall = now.isoformat(timespec="seconds")

    before = memory.state
    if memory.strength < TRACE_BELOW:
        memory.state, memory.body, memory.summary = TRACE, "", ""
    elif memory.strength < CONDENSE_BELOW and memory.state == COMPLETE:
        memory.state, memory.body = CONDENSED, ""
    return memory.state != before


def revive(memory: Memory, now: datetime | None = None) -> None:
    """Recalling a memory strengthens it."""
    now = now or datetime.now(timezone.utc)
    memory.strength = round(min(1.0, memory.strength + 0.25 * (1 - memory.strength) + 0.05), 4)
    memory.last_recall = now.isoformat(timespec="seconds")
