"""What a life gives its engine to learn from, kept by provenance and split by episode.

Audit of 12 November 2026, recommendations R-01 and R-02:

* Every unit of the corpus says where it comes from: words the person said (``heard``), passages the
  being read (``read``), facts a person vouched for (``verified``), and the being's own replies
  (``reply``). The being's replies are model output: they are kept, but never trained on unless the
  person allows it, so that the engine does not learn its own style back as if it were knowledge.
* Units are split by *episode*, not sentence by sentence: a run of at most four exchanges within one
  conversation, or four passages of one document. All units of an episode go to the same split, so a
  fact said twice in one breath cannot be both trained on and tested.
* Three splits: ``train`` changes the weights; ``validation`` decides whether a night is kept and
  whether to grow; ``test`` is sealed: no night ever reads it. It is read only by the final test,
  and every reading is written to ``test_access.jsonl``.
* Before any measure, an evaluation unit whose word 5-grams are mostly found in the training units is
  set aside as a near duplicate (a semantic leak), and counted.
"""

from __future__ import annotations

import hashlib
import json
import re
from datetime import datetime
from pathlib import Path

SPLITS = ("train", "validation", "test")
PROVENANCES = ("heard", "read", "verified", "reply")
EPISODE_GAP_MINUTES = 30      # a pause this long starts a new conversation
EPISODE_MAX_UNITS = 4         # exchanges (or passages) per episode
TEST_EVERY = 5                # one episode in five is sealed for the final test
VALIDATION_EVERY = 5          # one in five decides the nights; the other three train
LEAK_NGRAM = 5
LEAK_CONTAINMENT = 0.5        # more than half of a unit's word 5-grams found in training: a near duplicate
MAX_UNIT_CHARS = 2000


def sha(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def split_of(episode: str) -> str:
    """The split of an episode, fixed by the hash of its name: reproducible, and blind to its content."""
    bucket = int(sha("split:" + episode)[:8], 16) % (TEST_EVERY * VALIDATION_EVERY)
    if bucket % TEST_EVERY == 0:
        return "test"
    if bucket % VALIDATION_EVERY == 1:
        return "validation"
    return "train"


def probe_split(fact_id: str) -> str:
    """Questions about a vouched fact are either validation (they help decide the nights) or sealed test."""
    return "test" if int(sha("probe:" + fact_id)[:8], 16) % 2 == 0 else "validation"


def _time(value) -> datetime | None:
    try:
        return datetime.fromisoformat(str(value))
    except (TypeError, ValueError):
        return None


def gather(life_path: Path, since: int = 0, cursor: dict | None = None) -> tuple[list[dict], int, dict, dict]:
    """Read the life's event log from byte `since`. Returns the units, the new offset, counts of what was
    left out and why, and the episode cursor to pass back next time (so that episodes run across calls)."""
    life_path = Path(life_path)
    log = life_path / "events.log"
    cursor = dict(cursor or {"conversation": 0, "exchanges": 0, "last_time": None})
    if not log.exists():
        return [], since, {}, cursor
    units, skipped = [], {"too_long": 0, "unanswered": 0, "unreadable": 0}
    heard: str | None = None
    library = None

    def episode_for_exchange(when: str | None) -> str:
        now, last = _time(when), _time(cursor.get("last_time"))
        if (now and last and (now - last).total_seconds() > EPISODE_GAP_MINUTES * 60) or cursor["exchanges"] >= EPISODE_MAX_UNITS:
            cursor["conversation"] += 1
            cursor["exchanges"] = 0
        cursor["exchanges"] += 1
        if when:
            cursor["last_time"] = when
        return f"talk:{cursor['conversation']}"

    with log.open("rb") as handle:
        handle.seek(since)
        for raw in handle:
            try:
                event = json.loads(raw.decode("utf-8"))
            except (UnicodeDecodeError, json.JSONDecodeError):
                skipped["unreadable"] += 1
                continue
            kind = event.get("type")
            if kind == "stage" and event.get("source") == "message":
                if heard is not None:
                    skipped["unanswered"] += 1
                heard = str(event.get("text") or "")
            elif kind == "speech" and event.get("spontaneous") is False and heard is not None:
                said = str(event.get("text") or "")
                if len(heard) > MAX_UNIT_CHARS or len(said) > MAX_UNIT_CHARS:
                    skipped["too_long"] += 1
                else:
                    episode = episode_for_exchange(event.get("time"))
                    units.append({"provenance": "heard", "text": heard, "episode": episode, "time": event.get("time")})
                    units.append({"provenance": "reply", "text": said, "heard": heard, "episode": episode,
                                  "time": event.get("time")})
                heard = None
            elif kind == "silence" and heard is not None:
                heard = None
            elif kind == "read" and event.get("id"):
                if library is None:
                    from freewill.core.library import Library
                    library = Library(life_path / "library")
                first = int(event.get("number") or 1) - 1
                last = int(event.get("last") or event.get("number") or 1)
                for number in range(first, last):
                    try:
                        text = library.passage(str(event["id"]), number)
                    except (OSError, IndexError, ValueError, KeyError):
                        skipped["unreadable"] += 1
                        continue
                    units.append({"provenance": "read", "text": text[:MAX_UNIT_CHARS * 2],
                                  "episode": f"read:{event['id']}:{number // EPISODE_MAX_UNITS}",
                                  "document": event.get("name"), "passage": number + 1, "time": event.get("time")})
        offset = handle.tell()
    return units, offset, skipped, cursor


# -- leaks -----------------------------------------------------------------------------------------

def _grams(text: str, n: int = LEAK_NGRAM) -> set[tuple[str, ...]]:
    words = re.findall(r"\w+", text.lower())
    if len(words) < n:
        return {tuple(words)} if words else set()
    return {tuple(words[i:i + n]) for i in range(len(words) - n + 1)}


def without_leaks(units: list[dict], train: list[dict]) -> tuple[list[dict], list[dict]]:
    """Split evaluation units into those safe to measure and near duplicates of training units."""
    seen: set[tuple[str, ...]] = set()
    for row in train:
        seen |= _grams(row["text"])
    clean, leaked = [], []
    for row in units:
        grams = _grams(row["text"])
        share = (len(grams & seen) / len(grams)) if grams else 0.0
        (leaked if share > LEAK_CONTAINMENT else clean).append(row)
    return clean, leaked


def trainable(row: dict, *, own_replies: bool) -> bool:
    """Whether a unit may change the weights. The being's replies only when the person allowed it."""
    if row.get("provenance") == "reply":
        return own_replies or bool(row.get("approved"))
    return row.get("provenance") in ("heard", "read", "verified")


def legacy_units(row: dict, split: str) -> list[dict]:
    """A corpus row of rules h4-engine-1.x (a pair heard -> reply), as units of the new corpus."""
    messages = row.get("messages") or []
    episode = f"legacy:{row.get('sha256') or sha(json.dumps(messages))}"
    out = []
    if messages:
        out.append({"provenance": "heard", "text": messages[0]["content"], "episode": episode, "time": row.get("time")})
        if len(messages) > 1:
            out.append({"provenance": "reply", "text": messages[-1]["content"], "heard": messages[0]["content"],
                        "episode": episode, "time": row.get("time")})
    elif row.get("text"):
        out.append({"provenance": "heard", "text": row["text"], "episode": episode, "time": row.get("time")})
    for unit in out:
        unit.update(split=split, night=row.get("night"), legacy=True)
    return out
