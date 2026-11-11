"""Run a protocol from the command line: python -m freewill.research run EXP-01 [--dir DIR] [--lang fr|en]"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from freewill.paths import data_dir
from freewill.research import reports
from freewill.research.experiments import Lab, LabError


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="freewill.research")
    commands = parser.add_subparsers(dest="command", required=True)
    run = commands.add_parser("run", help="run a locked protocol on copies of a synthetic checkpoint")
    run.add_argument("protocol")
    run.add_argument("--version", default="1.0.0")
    run.add_argument("--dir", default=None, help="where the lab keeps its files")
    run.add_argument("--lang", default="en", choices=("en", "fr"))
    run.add_argument("--yes", action="store_true", help="you approve this campaign (required)")
    args = parser.parse_args(argv)
    if not args.yes:
        print("A campaign runs only with a person's approval: add --yes.", file=sys.stderr)
        return 2
    lab = Lab(Path(args.dir) if args.dir else data_dir() / "lab")
    try:
        experiment = lab.create_experiment(args.protocol, args.version, approved_by_human=True)
        experiment = lab.start(experiment["experiment_id"], wait=True)
    except LabError as error:
        print(f"error: {error}", file=sys.stderr)
        return 2
    print(f"{experiment['experiment_id']}: {experiment['status']}")
    for anomaly in experiment["anomalies"]:
        print(f"  anomaly: {anomaly}")
    if experiment["status"] != "done":
        return 1
    results = lab.results(experiment["experiment_id"])
    report = reports.build(lab, experiment["experiment_id"], args.lang)
    print(f"results_sha256 = {results['results_sha256']}")
    for name, path in report["files"].items():
        print(f"  {name}: {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
