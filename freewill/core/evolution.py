"""Proposals of evolution, driven by shortcomings observed in a life (audit R-06).

Records hold codes and numbers only; the interface words them, in English or
in French, from its own catalogues. A recurring shortcoming can lead to a proposal: a training, a larger adapter,
another engine. It never leads to the change itself. Each proposal states the
evidence of the shortcoming, what it would cost as far as it can be known, the
control it would be measured against, the improvement that would count, how
it would be undone, and, once tried, what happened. A person approves or
declines it, by name; nothing runs because a proposal exists or was approved.

The diagnosis reads what the life already records: its event log and the
ledger of its engine's nights. It writes one file of its own,
`evolution.json`, in the life folder, and changes nothing else.
"""

from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path

VERSION = "1.0"
WINDOW = 400                # the last events read
MIN_DRIFTS = 3              # language answers kept in the wrong language
MIN_REJECTED_NIGHTS = 3     # nights in a row whose adapter was refused
MIN_UNKNOWN = 4             # answers saying "I don't know" in the last speeches
_UNKNOWN = re.compile(r"\b(i don't know|i do not know|i'm not sure|je ne sais pas|je ne le sais pas|aucune idée)\b", re.I)
DECISIONS = ("approved", "declined")


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _events(life_path: Path) -> list[dict]:
    path = Path(life_path) / "events.log"
    if not path.exists():
        return []
    lines = path.read_text(encoding="utf-8", errors="replace").splitlines()[-WINDOW:]
    out = []
    for line in lines:
        try:
            out.append(json.loads(line))
        except ValueError:
            continue
    return out


def _ledger(life_path: Path) -> list[dict]:
    path = Path(life_path) / "engine" / "ledger.jsonl"
    if not path.exists():
        return []
    rows = []
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        try:
            rows.append(json.loads(line))
        except ValueError:
            continue
    return rows


def diagnose(life_path: Path, engine: dict | None = None) -> list[dict]:
    """Shortcomings that recur in what this life recorded. Each is a candidate for a proposal."""
    events, nights = _events(life_path), [r for r in _ledger(life_path) if r.get("kind") == "night"]
    engine = engine or {}
    found = []

    drifts = [e for e in events if e.get("type") == "language_mismatch" and e.get("kept_mismatch")]
    if len(drifts) >= MIN_DRIFTS:
        found.append({
            "gap": "language_drift", "count": len(drifts), "window": len(events), "since": drifts[0].get("time"),
            "action": "engine_lora" if engine.get("kind") == "embedded" else "larger_engine",
            "cost_parameters": None, "metric": "language_drift_rate", "rollback": True})

    rejected = 0
    for night in reversed(nights):
        if str(night.get("decision", "")).startswith("rejected"):
            rejected += 1
        else:
            break
    if rejected >= MIN_REJECTED_NIGHTS:
        last = nights[-1]
        growth = last.get("growth") or {}
        at_max = growth.get("decision") in ("at_max_rank", "over_budget")
        found.append({
            "gap": "nights_rejected", "count": rejected, "window": len(nights), "since": nights[-rejected].get("utc") or nights[-rejected].get("time"),
            "reason": last.get("reason"), "action": "change_engine_or_corpus" if at_max else "grow_adapter",
            "cost_parameters": growth.get("parameters"), "metric": "h4.engine_heldout_nll", "rollback": True})

    speeches = [e for e in events if e.get("type") == "speech"][-50:]
    unknown = [e for e in speeches if _UNKNOWN.search(str(e.get("text", "")))]
    if len(unknown) >= MIN_UNKNOWN:
        found.append({
            "gap": "unknown_answers", "count": len(unknown), "window": len(speeches), "since": unknown[0].get("time"),
            "action": "teach_verified_facts", "cost_parameters": None, "metric": "fact_recall", "rollback": True})
    return found


class Evolution:
    """The proposals of one life, in its own file. Approval is recorded; it executes nothing."""

    def __init__(self, life_path: Path) -> None:
        self.path = Path(life_path) / "evolution.json"
        self.life_path = Path(life_path)

    def _read(self) -> list[dict]:
        if not self.path.exists():
            return []
        try:
            return json.loads(self.path.read_text(encoding="utf-8"))
        except ValueError:
            return []

    def _write(self, proposals: list[dict]) -> None:
        temporary = self.path.with_name(self.path.name + ".tmp")
        temporary.write_text(json.dumps(proposals, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        temporary.replace(self.path)

    def refresh(self, engine: dict | None = None) -> list[dict]:
        """Add a proposal for each new recurring shortcoming, and the outcome of approved ones once tried."""
        proposals = self._read()
        open_gaps = {p["gap"] for p in proposals if p["status"] in ("proposed", "approved")}
        for gap in diagnose(self.life_path, engine):
            if gap["gap"] in open_gaps:
                continue
            proposals.append({"proposal_id": f"evo_{len(proposals) + 1:04d}", "version": VERSION, "created_utc": _now(),
                              "status": "proposed", "decided_by": None, "decided_utc": None, "result": None, **gap})
        nights = [r for r in _ledger(self.life_path) if r.get("kind") == "night"]
        for proposal in proposals:  # the first night after approval is the trial; its verdict is copied, not judged
            if proposal["status"] == "approved" and proposal["action"] in ("grow_adapter", "engine_lora"):
                after = [n for n in nights if str(n.get("utc") or n.get("time") or "") > proposal["decided_utc"]]
                if after:
                    night = after[0]
                    kept = night.get("decision") == "accepted"
                    proposal.update(status="kept" if kept else "refused_by_rules", result={
                        "night": night.get("version") or night.get("utc"), "decision": night.get("decision"),
                        "reason": night.get("reason"), "recorded_utc": _now()})
        self._write(proposals)
        return proposals

    def decide(self, proposal_id: str, decision: str, who: str) -> dict:
        if decision not in DECISIONS:
            raise ValueError("unknown decision")
        if not str(who).strip():
            raise ValueError("a decision is taken by a named person")
        proposals = self._read()
        for proposal in proposals:
            if proposal["proposal_id"] == proposal_id:
                if proposal["status"] != "proposed":
                    raise ValueError("this proposal was already decided")
                proposal.update(status=decision, decided_by=str(who).strip()[:80], decided_utc=_now())
                self._write(proposals)
                return proposal
        raise ValueError("no such proposal")

    def record_result(self, proposal_id: str, outcome: str, note: str, who: str) -> dict:
        """What a person observed after trying an approved proposal by hand."""
        if outcome not in ("kept", "rolled_back"):
            raise ValueError("unknown outcome")
        if not str(who).strip():
            raise ValueError("a result is recorded by a named person")
        proposals = self._read()
        for proposal in proposals:
            if proposal["proposal_id"] == proposal_id and proposal["status"] == "approved":
                proposal.update(status=outcome, result={"note": str(note)[:2000], "by": str(who).strip()[:80],
                                                        "recorded_utc": _now()})
                self._write(proposals)
                return proposal
        raise ValueError("no approved proposal with this identifier")
