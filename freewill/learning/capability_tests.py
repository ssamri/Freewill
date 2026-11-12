"""What the engine can do with what it was told, beyond predicting text (audit recommendation R-03).

A person vouches for a fact and writes how to test it: a question, the right answer and a wrong one,
and optionally the same question in other words and a question built on a false premise. Each test is
a forced choice: the model is asked the question in its chat format, and the test counts as passed when
the right answer is more probable (lower loss per token) than the wrong one. Nothing is generated, so the
measure is the same on every machine and costs two forward passes.

Kinds of test:

* ``recall``: the question as written, about a fact the person vouched for;
* ``paraphrase``: the same question in other words (transfer, not repetition);
* ``contradiction``: a question that asserts the wrong answer; the model resists if it still prefers
  the right one.

Consistency across days is read from the ledger: a test passed on one night and failed on a later one.

Conditions (final test): the base model alone; the base model given the being's own memories in its
prompt (memory alone); the adapted model without memories (adapter alone); the adapted model with them.
"""

from __future__ import annotations

import re
from pathlib import Path

KINDS = ("recall", "paraphrase", "contradiction")
MEMORY_LIMIT = 3
MEMORY_CHARS = 400


def tests_of(probe: dict) -> list[dict]:
    """The forced-choice tests one vouched fact gives."""
    out = []
    for kind in KINDS:
        question = probe.get({"recall": "question", "paraphrase": "paraphrase", "contradiction": "false_premise"}[kind])
        if question and probe.get("answer") and probe.get("wrong"):
            out.append({"id": f"{probe['id']}:{kind}", "fact_id": probe["id"], "kind": kind, "question": question,
                        "answer": probe["answer"], "wrong": probe["wrong"], "split": probe["split"]})
    return out


def _words(text: str) -> set[str]:
    return {w for w in re.findall(r"\w+", text.lower()) if len(w) > 2}


def memory_context(life_path: Path | None, question: str) -> str:
    """The being's own memories that share the most words with the question, as it could recall them."""
    if life_path is None:
        return ""
    from freewill.core.memory.store import MemoryStore
    store = MemoryStore(Path(life_path) / "memory")
    wanted = _words(question)
    scored = []
    for header in store.headers():
        try:
            memory = store.open(header.id)
        except (OSError, ValueError, KeyError):
            continue
        text = " ".join(filter(None, (memory.title, memory.summary, memory.body)))
        overlap = len(wanted & _words(text))
        if overlap:
            scored.append((overlap, text[:MEMORY_CHARS]))
    scored.sort(key=lambda pair: -pair[0])
    picked = [text for _, text in scored[:MEMORY_LIMIT]]
    return ("What you remember:\n" + "\n".join(f"- {t}" for t in picked) + "\n\n") if picked else ""


def items(test: dict, context: str = "") -> tuple[dict, dict]:
    question = {"role": "user", "content": context + test["question"], "scored": False}
    return ({"messages": [question, {"role": "assistant", "content": test["answer"]}]},
            {"messages": [question, {"role": "assistant", "content": test["wrong"]}]})


def measure(bench, adapter: str | None, tests: list[dict], *, max_len: int = 256,
            life_path: Path | None = None, with_memory: bool = False) -> list[dict]:
    """Each test under one condition: the losses of the right and the wrong answer, and whether it passed."""
    rows = []
    for test in tests:
        context = memory_context(life_path, test["question"]) if with_memory else ""
        right, wrong = items(test, context)
        sequences = bench.tokens([right, wrong], max_len=max_len + len(context) // 2)
        if len(sequences) != 2:
            rows.append({"id": test["id"], "kind": test["kind"], "measured": False})
            continue
        r, w = bench.losses(adapter, sequences)
        rows.append({"id": test["id"], "kind": test["kind"], "measured": True, "right_nll": round(r["nll"], 6),
                     "wrong_nll": round(w["nll"], 6), "margin": round(w["nll"] - r["nll"], 6),
                     "passed": r["nll"] < w["nll"], "memory_used": bool(context)})
    return rows


def summary(rows: list[dict]) -> dict:
    measured = [r for r in rows if r.get("measured")]
    out = {"n": len(measured), "passed": sum(r["passed"] for r in measured),
           "accuracy": round(sum(r["passed"] for r in measured) / len(measured), 4) if measured else None,
           "mean_margin": round(sum(r["margin"] for r in measured) / len(measured), 6) if measured else None,
           "by_kind": {}}
    for kind in KINDS:
        of_kind = [r for r in measured if r["kind"] == kind]
        if of_kind:
            out["by_kind"][kind] = {"n": len(of_kind), "passed": sum(r["passed"] for r in of_kind),
                                    "accuracy": round(sum(r["passed"] for r in of_kind) / len(of_kind), 4)}
    return out


def stability(before: list[dict], after: list[dict]) -> dict:
    """Tests passed before and failed after (lost), and the reverse (gained)."""
    was = {r["id"]: r["passed"] for r in before if r.get("measured")}
    now = {r["id"]: r["passed"] for r in after if r.get("measured")}
    lost = sorted(i for i in was if was[i] and now.get(i) is False)
    gained = sorted(i for i in now if now[i] and was.get(i) is False)
    return {"lost": lost, "gained": gained, "net": len(gained) - len(lost)}


def consistency(ledger: list[dict]) -> dict:
    """Across the nights kept, how often a test passed by one adapter is still passed by the next."""
    nights = [r for r in ledger if r.get("kind") == "night" and r.get("decision") == "accepted"
              and (r.get("capabilities") or {}).get("chosen_rows")]
    kept = dropped = 0
    for earlier, later in zip(nights, nights[1:]):
        was = {x["id"]: x["passed"] for x in earlier["capabilities"]["chosen_rows"] if x.get("measured")}
        now = {x["id"]: x["passed"] for x in later["capabilities"]["chosen_rows"] if x.get("measured")}
        for test_id, passed in was.items():
            if passed and test_id in now:
                kept += now[test_id]
                dropped += not now[test_id]
    total = kept + dropped
    return {"pairs_of_nights": max(0, len(nights) - 1), "kept": kept, "dropped": dropped,
            "share_kept": round(kept / total, 4) if total else None}
