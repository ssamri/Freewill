"""Train Freewill's own network on a fixed text, night after night, and write down what really happened.

    python tools/own_model_benchmark.py OUT.json [--nights 8] [--steps 80]

The text is this repository's own documentation, in the order of the file names, cut into equal shares, one per
night. It is a stand-in for a life's text: it shows that the weights change, that the size grows and what each
night costs on this machine. It is not a claim about what the network understands. Needs PyTorch.
"""

from __future__ import annotations

import argparse
import json
import platform
import sys
import tempfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from freewill.learning.own_model import OwnModel, torch_or_none  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("out")
    parser.add_argument("--nights", type=int, default=8)
    parser.add_argument("--steps", type=int, default=80)
    parser.add_argument("--ceiling", type=int, default=5_000_000)
    args = parser.parse_args()
    torch = torch_or_none()
    if torch is None:
        print("PyTorch is not installed: nothing was trained.", file=sys.stderr)
        return 2
    files = sorted(p for p in ROOT.rglob("*.md") if ".git" not in p.parts and "experiments" not in p.parts)
    text = "\n".join(p.read_text(encoding="utf-8") for p in files)
    share = len(text) // args.nights
    events: list = []
    with tempfile.TemporaryDirectory() as folder:
        model = OwnModel(Path(folder), 2026, lambda kind, **data: events.append({"event": kind, **data}))
        nights = []
        for night in range(args.nights):
            model.live([text[night * share:(night + 1) * share]])
            started = time.monotonic()
            report = model.sleep(steps=args.steps, grow=True, ceiling=args.ceiling)
            public = model.public()
            nights.append({"night": night + 1, "decision": report["decision"],
                           "unseen_text_loss_before": report["heldout_loss_before"],
                           "unseen_text_loss_after_training": report["heldout_loss_candidate"],
                           "older_unseen_text_loss_before": report["old_loss_before"],
                           "older_unseen_text_loss_after_training": report["old_loss_candidate"],
                           "parameters_after_night": public["parameters"], "layers_after_night": public["layers"],
                           "weights_sha256": public["weights_sha256"], "corpus_bytes": public["corpus_bytes"],
                           "seconds": round(time.monotonic() - started, 1)})
            print(nights[-1], flush=True)
        sample = model.sample("Freewill ", 160)
    Path(args.out).write_text(json.dumps({
        "what": "Freewill's own network trained on this repository's documentation, one share per night",
        "files": [str(p.relative_to(ROOT)) for p in files], "text_characters": len(text), "nights": nights,
        "growth": [e for e in events if e["event"] == "own_model_growth"], "steps_per_night": args.steps,
        "ceiling_parameters": args.ceiling, "sample_after_last_night": sample,
        "machine": {"processor": platform.processor() or platform.machine(), "threads": torch.get_num_threads(),
                    "gpu": None, "torch": torch.__version__, "python": platform.python_version()},
        "unit": "loss in nats per byte on passages never trained on; lower is better; 5.55 is a uniform guess",
        "limits": "One run, one seed, CPU. The text is documentation, not a life. The network does not speak for a being."},
        indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
