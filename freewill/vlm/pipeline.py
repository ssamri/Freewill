"""The whole course of Freewill's own model: grow, read books, learn to see, learn to watch.

Used by `freewill own-model train` and by the end-to-end workflow. Each stage
is a decision of train.py, taken on validation sets. A sealed test set, kept
apart by construction (other seeds, other blocks of the books) and fixed by a
hash at the first run, is measured at birth and at the end and only reported.
The summary holds every number that was measured; nothing is reported that
was not computed.
"""

from __future__ import annotations

import hashlib
import json
import time
from dataclasses import asdict, dataclass
from pathlib import Path

from freewill.vlm import books as bookshelf
from freewill.vlm import synthetic
from freewill.vlm.capacity import GrowthRefused
from freewill.vlm.train import Trainer, accept_reading, accept_skill, binomial_p


@dataclass
class Plan:
    grow: int = 1                 # decoder layers added before reading (0: none)
    widen: int = 0                # neurons added to every feed-forward block before reading
    grow_to: int = 0              # or: grow towards this many parameters (neurons first, then layers)
    rank: int = 16
    read_steps: int = 40
    read_lr: float = 1e-4
    read_batch: int = 2
    read_words: int = 120
    see_steps: int = 200
    see_lr: float = 1e-3
    see_batch: int = 4
    see_parts: tuple = ("bridge",)
    watch_steps: int = 150
    watch_lr: float = 5e-4
    watch_batch: int = 2
    watch_parts: tuple = ("bridge", "lora")
    frames: int = 4
    images: int = 300             # drawn training images
    videos: int = 180             # drawn training videos
    validation_images: int = 50   # decide whether "see" is kept
    validation_videos: int = 30
    test_images: int = 50         # sealed: reported only
    test_videos: int = 30
    validation_books: int = 24    # passages measured at each stage to decide
    test_books: int = 40          # sealed passages, reported only
    budget_minutes: float = 0     # per stage; 0 for none
    seed: int = 0


def split_books(books: list[dict], words: int) -> dict[str, list[str]]:
    """Passages of every book, by blocks of consecutive passages, into train, validation and test."""
    out, seen = {"train": [], "validation": [], "test": []}, set()
    for book in books:
        for index, passage in enumerate(bookshelf.passages(book["text"], words)):
            if passage in seen:      # a repeated passage would be in two sets at once
                continue
            seen.add(passage)
            out[bookshelf.split_of(book["id"], index // bookshelf.BLOCK)].append(passage)
    return out


def seal(root: Path, books: dict, plan: Plan) -> dict:
    """The sealed test: what it holds, and its hash. Written at the first run; a later run whose test set
    differs is refused, so that the test cannot be changed after results were seen."""
    content = {"books": [hashlib.sha256(t.encode("utf-8")).hexdigest() for t in books["test"][: plan.test_books]],
               "images": ["image-test-%d" % s for s in range(plan.test_images)],
               "videos": ["video-test-%d-%d" % (s, plan.frames) for s in range(plan.test_videos)]}
    digest = hashlib.sha256(json.dumps(content, sort_keys=True).encode("utf-8")).hexdigest()
    path = Path(root) / "sealed_test.json"
    if path.is_file():
        before = json.loads(path.read_text(encoding="utf-8"))
        if before["sha256"] != digest:
            raise ValueError("the sealed test set differs from the one sealed at the first run "
                             f"({before['sha256'][:12]} → {digest[:12]}); it may not be changed")
    else:
        path.write_text(json.dumps({"sha256": digest, "sealed_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                                    "counts": {k: len(v) for k, v in content.items()}, "content": content}, indent=1),
                        encoding="utf-8")
    return {"sha256": digest, "counts": {k: len(v) for k, v in content.items()}}


def run(model, root: Path, books: list[dict], plan: Plan, log=print, stages=("read", "see", "watch")) -> dict:
    trainer = Trainer(model, root, log)
    budget = plan.budget_minutes * 60 or None
    started = time.monotonic()
    history = []
    texts = split_books(books, plan.read_words)
    train_texts, val_texts, test_texts = texts["train"], texts["validation"][: plan.validation_books], texts["test"][: plan.test_books]
    sealed = seal(root, texts, plan)
    summary = {"plan": asdict(plan), "books": [{k: b[k] for k in ("id", "title", "language", "sha256")} for b in books],
               "passages": {"train": len(train_texts), "validation_measured": len(val_texts), "test_sealed": len(test_texts)},
               "sealed_test": sealed, "parameters_at_birth": model.count()}
    log(f"parameters at birth: {json.dumps(summary['parameters_at_birth'])}")

    def test_measure() -> dict:
        """The sealed test. Its numbers go to the summary only: no rule ever reads them."""
        out = {}
        if test_texts:
            out["books"] = round(trainer.reading_nats(test_texts), 4)
        if "see" in stages or "watch" in stages:
            items = list(range(plan.test_images))
            out["images"] = trainer.choose(synthetic.image_choices(items, split="test"))
            out["images_other_image"] = trainer.choose(synthetic.image_choices(items, "other image", split="test"))
        if "watch" in stages:
            items = list(range(plan.test_videos))
            out["videos"] = trainer.choose(synthetic.video_choices(items, plan.frames, split="test"))
            out["videos_reversed"] = trainer.choose(synthetic.video_choices(items, plan.frames, "reversed", split="test"))
            out["videos_one_frame"] = trainer.choose(synthetic.video_choices(items, plan.frames, "one frame", split="test"))
        return out

    log("[sealed test] at birth")
    summary["test_at_birth"] = test_measure()
    log(f"[sealed test] at birth: {json.dumps(summary['test_at_birth'])}")

    try:
        if plan.grow_to:
            log(f"growing towards {plan.grow_to:,}: {model.grow_to(plan.grow_to)}")
        else:
            if plan.widen:
                model.widen(plan.widen)
            if plan.grow:
                log(f"grew by {plan.grow} layer(s) at {model.grow(plan.grow)}")
    except GrowthRefused as refusal:   # the model goes on at the size it has; the refusal is recorded
        summary["growth_refused"] = refusal.details
        trainer.ledger({"utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "stage": "growth",
                        "decision": "refused", "reason": str(refusal), "details": refusal.details})
        log(f"{refusal}: {json.dumps(refusal.details)}")
    log(f"after growth: {json.dumps(model.count())}")
    if plan.rank:
        model.add_lora(plan.rank)
    summary["parameters_after_growth"] = model.count()

    def books_nats() -> float:
        return round(trainer.reading_nats(val_texts), 4) if val_texts else float("nan")

    if "read" in stages and train_texts:
        examples = [{"parts": [], "answer": t, "chat": False} for t in train_texts]
        history.append(trainer.stage(
            "read", examples, {"lora", "grown"} if model.growth_log else {"lora"}, plan.read_steps, plan.read_lr,
            lambda: {"books_validation": books_nats()}, accept_reading, plan.read_batch, plan.seed, budget,
            {"books": len(books)}))

    img_train, img_val = list(range(plan.images)), list(range(plan.validation_images))
    if "see" in stages:
        def measure_see() -> dict:
            out = {"images": trainer.choose(synthetic.image_choices(img_val)),
                   "images_other_image": trainer.choose(synthetic.image_choices(img_val, "other image"))}
            if val_texts:
                out["books_validation"] = books_nats()
            return out
        history.append(trainer.stage(
            "see", synthetic.image_examples(img_train), set(plan.see_parts), plan.see_steps, plan.see_lr,
            measure_see, accept_skill("images", controls=["images_other_image"]), plan.see_batch, plan.seed + 1, budget))

    if "watch" in stages:
        vid_train, vid_val = list(range(plan.videos)), list(range(plan.validation_videos))
        examples = synthetic.video_examples(vid_train, plan.frames)
        rehearsal = synthetic.image_examples(img_train[: len(vid_train) // 2])  # so that seeing is not forgotten
        def measure_watch() -> dict:
            out = {"videos": trainer.choose(synthetic.video_choices(vid_val, plan.frames)),
                   "videos_reversed": trainer.choose(synthetic.video_choices(vid_val, plan.frames, "reversed")),
                   "videos_one_frame": trainer.choose(synthetic.video_choices(vid_val, plan.frames, "one frame")),
                   "images": trainer.choose(synthetic.image_choices(img_val))}
            if val_texts:
                out["books_validation"] = books_nats()
            return out
        history.append(trainer.stage(
            "watch", examples + rehearsal, set(plan.watch_parts), plan.watch_steps, plan.watch_lr,
            measure_watch, accept_skill("videos", controls=["videos_reversed", "videos_one_frame"], keep=["images"]),
            plan.watch_batch, plan.seed + 2, budget))

    log("[sealed test] at the end")
    summary["test_at_end"] = test_measure()
    log(f"[sealed test] at the end: {json.dumps(summary['test_at_end'])}")
    trainer.ledger({"utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "stage": "sealed test",
                    "decision": "reported only", "sealed_sha256": sealed["sha256"],
                    "at_birth": summary["test_at_birth"], "at_end": summary["test_at_end"]})
    manifest = trainer.save(history)
    summary.update(stages=history, checkpoint=manifest["version"], own_sha256=manifest["own_sha256"],
                   parameters=model.count(), seconds=round(time.monotonic() - started, 1),
                   significance=_significance({"test_at_end": summary["test_at_end"]}))
    (Path(root) / "summary.json").write_text(json.dumps(summary, indent=1, ensure_ascii=False), encoding="utf-8")
    return summary


def _significance(measured: dict) -> dict:
    """For each multiple-choice measurement of the sealed test: how likely that many right answers are by chance
    (with the mean chance of its items: colour has 6 choices, shape 4, motion 4)."""
    out = {}
    for name, block in measured.items():
        for key, value in block.items():
            if isinstance(value, dict) and "accuracy" in value and value["n"]:
                right = round(value["accuracy"] * value["n"])
                out[f"{name}:{key}"] = {"right": right, "n": value["n"], "chance": round(value["chance"], 4),
                                                   "p_by_chance": binomial_p(right, value["n"], value["chance"])}
    return out
