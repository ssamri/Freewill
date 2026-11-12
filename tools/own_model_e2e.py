"""Freewill's own model, end to end, with the real bases: fetch, assemble, count, grow, read books,
learn to see, learn to watch, save, rebuild from the checkpoint, and answer about unseen images and videos.

    python tools/own_model_e2e.py OUT --data DATA [--read-steps N] [--see-steps N] [--watch-steps N]
    python tools/own_model_e2e.py OUT --tiny        # the same course on the toy model, in a minute

Everything it reports is in OUT/e2e.json and OUT/model/summary.json, computed during the run.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
import traceback
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from freewill.vlm import books as bookshelf  # noqa: E402
from freewill.vlm import pipeline, store, synthetic  # noqa: E402
from freewill.vlm.model import build, tiny  # noqa: E402
from freewill.vlm.train import Trainer, restore  # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("out")
    ap.add_argument("--data", default="own-model-data")
    ap.add_argument("--tiny", action="store_true")
    ap.add_argument("--dtype", default="float32")
    ap.add_argument("--grow", type=int, default=1)
    ap.add_argument("--read-steps", type=int, default=40)
    ap.add_argument("--see-steps", type=int, default=300)
    ap.add_argument("--watch-steps", type=int, default=200)
    ap.add_argument("--images", type=int, default=240)
    ap.add_argument("--videos", type=int, default=160)
    ap.add_argument("--budget-minutes", type=float, default=75)
    args = ap.parse_args()
    out, data = Path(args.out), Path(args.data)
    out.mkdir(parents=True, exist_ok=True)
    report = {"started": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "tiny": args.tiny, "steps": []}

    def step(name, fn, shown=lambda r: r):
        t = time.monotonic()
        print(f"== {name}", flush=True)
        try:
            result = fn()
            report["steps"].append({"step": name, "status": "ok", "seconds": round(time.monotonic() - t, 1), "result": shown(result)})
            return result
        except Exception as error:
            traceback.print_exc()
            report["steps"].append({"step": name, "status": "failed", "seconds": round(time.monotonic() - t, 1),
                                    "error": f"{type(error).__name__}: {error}"})
            raise
        finally:
            (out / "e2e.json").write_text(json.dumps(report, indent=1, ensure_ascii=False, default=lambda o: type(o).__name__), encoding="utf-8")

    log = lambda *a: print(*a, flush=True)  # noqa: E731
    try:
        if args.tiny:
            model = step("assemble the toy model", lambda: tiny())
            text = "\n\n".join(f"Chapter {i}. The keeper of the lighthouse counted {i} ships, and the fox slept "
                               f"under the lemon tree while the bell rang {i % 7} times." for i in range(300))
            books = [{"id": "toy", "title": "toy", "language": "English", "sha256": "", "text": text}]
            plan = pipeline.Plan(grow=args.grow, rank=4, read_steps=args.read_steps, read_lr=3e-3, read_words=40,
                                 see_steps=args.see_steps, see_lr=3e-3, see_batch=8, see_parts=("bridge", "lora"),
                                 watch_steps=args.watch_steps, watch_lr=3e-3, images=args.images, videos=args.videos)
            bases = None
        else:
            bases = data / "bases-root"
            step("fetch the two bases", lambda: {k: {"repo": v["repo"], "revision": v["revision"], "files": len(v["files"])}
                                                 for k, v in (json.loads((bases / "bases.json").read_text())
                                                              if store.bases_ready(bases) and (bases / "bases.json").is_file()
                                                              else store.fetch_bases(bases, log=log)).items()})
            fetched = step("fetch the books", lambda: _books(data / "books"),
                           lambda r: {"read": r["read"], "left_out": r["left_out"]})
            books = fetched["books"]
            model = step("assemble Freewill 1.8B-V", lambda: build(bases / "bases", dtype=args.dtype))
            plan = pipeline.Plan(grow=args.grow, read_steps=args.read_steps, see_steps=args.see_steps,
                                 watch_steps=args.watch_steps, images=args.images, videos=args.videos,
                                 budget_minutes=args.budget_minutes)
        root = out / "model"
        step("count at birth", lambda: model.count())
        summary = step("grow, read, see, watch", lambda: pipeline.run(model, root, books, plan, log),
                       lambda r: {k: r.get(k) for k in ("passages", "parameters", "checkpoint", "seconds", "sealed_test",
                                                       "test_at_birth", "test_at_end", "significance", "growth_refused")}
                       | {"stages": [{k: h[k] for k in ("stage", "decision", "reason", "before", "after", "training")}
                                     for h in r["stages"]]})
        step("answers about unseen images and videos", lambda: _answers(model))

        def rebuilt():
            again = tiny() if args.tiny else build(bases / "bases", dtype=args.dtype)
            folder = root / "checkpoints" / summary["checkpoint"]
            manifest = restore(again, folder)
            items = synthetic.image_choices([3, 7])
            a, b = Trainer(model, root, log).choose(items), Trainer(again, root, log).choose(items)
            same = abs(a["truth_nats"] - b["truth_nats"]) < 1e-4
            if not same:
                raise AssertionError(f"rebuilt model scores {b['truth_nats']}, trained one {a['truth_nats']}")
            return {"version": manifest["version"], "parameters": again.count(), "same_scores": same}
        step("rebuild from the checkpoint", rebuilt)
    except Exception:
        return 1
    return 0


def _books(cache: Path) -> dict:
    books, left = bookshelf.shelf(cache)
    if not books:
        raise RuntimeError("no book could be fetched: " + "; ".join(left))
    return {"books": books, "left_out": left,
            "read": [{k: b[k] for k in ("id", "title", "language", "sha256")} | {"chars": len(b["text"])} for b in books]}


def _answers(model) -> list[dict]:
    """Free answers on items of the sealed test (other seeds than training and validation), shown, never scored."""
    out = []
    for seed in (3, 7, 11):
        item = synthetic.image_item(seed, split="test")
        for q in ("colour", "shape"):
            out.append({"seed": seed, "question": synthetic.QUESTIONS[q], "truth": item[q],
                        "answer": model.answer([("image", item["image"]), "\n" + synthetic.QUESTIONS[q]], max_new_tokens=8)})
    for seed in (3, 7):
        item = synthetic.video_item(seed, split="test")
        out.append({"seed": seed, "question": synthetic.QUESTIONS["motion"], "truth": item["direction"],
                    "answer": model.answer([("video", item["frames"]), "\n" + synthetic.QUESTIONS["motion"]], max_new_tokens=8)})
    item = synthetic.image_item(15, split="test")
    out.append({"seed": 15, "question": "Describe this picture in one sentence.", "truth": f"{item['colour']} {item['shape']}",
                "answer": model.answer([("image", item["image"]), "\nDescribe this picture in one sentence."], max_new_tokens=40)})
    return out


if __name__ == "__main__":
    raise SystemExit(main())
