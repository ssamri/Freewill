"""Audit observers A, B and C on trap cases, with real APIs under a budget (audit R-07).

    python tools/observer_audit.py OUT_DIR [--anthropic MODEL] [--openai MODEL] [--xai MODEL]
                                   [--language en|fr] [--max-requests 12]

Each named engine becomes one observer (explorer, contradictor, synthesizer in
that order), with its key read from ANTHROPIC_API_KEY, OPENAI_API_KEY or
XAI_API_KEY. Engines with no key are skipped and said so. Two fixed reference
readers are always scored first, to show that the score tells a careful
reading from a credulous one. Nothing here is a result about the being; it
qualifies the observers. Writes OUT_DIR/observer-audit.json.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from freewill.research import observer_audit  # noqa: E402
from freewill.research.observers import ROLES, ObserverError, ObserverStore  # noqa: E402

KEYS = {"anthropic": "ANTHROPIC_API_KEY", "openai": "OPENAI_API_KEY", "xai": "XAI_API_KEY"}


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(prog="observer_audit")
    parser.add_argument("out")
    for kind in KEYS:
        parser.add_argument(f"--{kind}", default=None, metavar="MODEL")
    parser.add_argument("--language", default="en", choices=("en", "fr"))
    parser.add_argument("--max-requests", type=int, default=12)
    args = parser.parse_args(argv)
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)

    report = {"cases_sha256": observer_audit.cases_hash(), "audit_version": observer_audit.AUDIT_VERSION,
              "language": args.language, "reference": {}, "observers": [], "skipped": []}
    for name, reader in (("careful_reader", observer_audit.careful_reader), ("credulous_reader", observer_audit.credulous_reader)):
        report["reference"][name] = observer_audit.summary(
            [observer_audit.score(case, reader(case, args.language), args.language) for case in observer_audit.cases()])

    store = ObserverStore(out / "observers")
    for profile in store.list():  # the three default observers are replaced by the ones asked for
        store.delete(profile["observer_id"])
    store.set_global_budget({"max_requests": args.max_requests * 3, "max_chars": 3_000_000})
    asked = [(kind, model) for kind, model in ((k, getattr(args, k)) for k in KEYS) if model]
    for index, (kind, model) in enumerate(asked):
        key = os.environ.get(KEYS[kind], "").strip()
        if not key:
            report["skipped"].append({"engine": kind, "model": model, "reason": f"{KEYS[kind]} is not set"})
            continue
        letter = "ABC"[index % 3]
        profile = store.create(f"Observer {letter}", ROLES[index % 3], args.language)
        store.update(profile["observer_id"], {"engine": {"kind": kind, "model": model}, "mode": "research",
                                              "budget": {"max_requests": args.max_requests, "max_chars": 1_000_000}})
        store.set_key(profile["observer_id"], key)
        try:
            record = observer_audit.run(store, profile["observer_id"])
        except ObserverError as error:
            report["skipped"].append({"engine": kind, "model": model, "reason": str(error)})
            continue
        report["observers"].append({k: v for k, v in record.items() if k != "answers"} | {"answers": record["answers"]})
    (out / "observer-audit.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"cases {report['cases_sha256'][:16]}  language {args.language}")
    for name, summary in report["reference"].items():
        print(f"  reference {name:17} {json.dumps(summary)}")
    for record in report["observers"]:
        print(f"  {record['name']} {record['llm']:40} {json.dumps(record['summary'])}" + ("" if record["complete"] else f"  INCOMPLETE {record['errors']}"))
    for skipped in report["skipped"]:
        print(f"  skipped {skipped['engine']}:{skipped['model']}: {skipped['reason']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
