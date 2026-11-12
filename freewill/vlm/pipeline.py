"""The whole course of Freewill's own model: grow, read books, learn to see, learn to watch.

Used by `freewill own-model train` and by the end-to-end workflow. Each stage
is a decision of train.py, and the summary returned here holds every number
that was measured, so that nothing is reported that was not computed.
"""

from __future__ import annotations

import json
import time
from dataclasses import asdict, dataclass
from pathlib import Path

from freewill.vlm import books as bookshelf
from freewill.vlm import synthetic
from freewill.vlm.train import Trainer, accept_reading, accept_skill, binomial_p


@dataclass
class Plan:
    grow: int = 1                 # decoder layers added before reading (0: none)
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
    images: int = 400             # drawn images; one in four is held out
    videos: int = 240
    held_books: int = 24          # held-out passages measured at each stage
    budget_minutes: float = 0     # per stage; 0 for none
    seed: int = 0


def split_books(books: list[dict], words: int) -> tuple[list[str], list[str]]:
    train, held, seen = [], [], set()
    for book in books:
        for passage in bookshelf.passages(book["text"], words):
            if passage in seen:      # a repeated passage would be in both halves at once
                continue
            seen.add(passage)
            (held if bookshelf.held_out(passage) else train).append(passage)
    return train, held


def run(model, root: Path, books: list[dict], plan: Plan, log=print, stages=("read", "see", "watch")) -> dict:
    trainer = Trainer(model, root, log)
    budget = plan.budget_minutes * 60 or None
    started = time.monotonic()
    history, growth_steps = [], []
    train_texts, held_texts = split_books(books, plan.read_words)
    held_texts = held_texts[: plan.held_books]
    summary = {"plan": asdict(plan), "books": [{k: b[k] for k in ("id", "title", "language", "sha256")} for b in books],
               "passages": {"train": len(train_texts), "held_out_measured": len(held_texts)},
               "parameters_at_birth": model.count()}
    log(f"parameters at birth: {json.dumps(summary['parameters_at_birth'])}")

    if plan.grow:
        added = model.grow(plan.grow)
        growth_steps.append(plan.grow)
        log(f"grew by {plan.grow} layer(s) at {added}: {json.dumps(model.count())}")
    if plan.rank:
        model.add_lora(plan.rank)
    summary["parameters_after_growth"] = model.count()

    def books_nats() -> float:
        return round(trainer.reading_nats(held_texts), 4) if held_texts else float("nan")

    if "read" in stages and train_texts:
        examples = [{"parts": [], "answer": t, "chat": False} for t in train_texts]
        history.append(trainer.stage(
            "read", examples, {"lora", "grown"} if plan.grow else {"lora"}, plan.read_steps, plan.read_lr,
            lambda: {"books_held_out": books_nats()}, accept_reading, plan.read_batch, plan.seed, budget,
            {"books": len(books)}))

    seeds_img = range(plan.images)
    img_train = [s for s in seeds_img if not synthetic.held_out(s)]
    img_held = [s for s in seeds_img if synthetic.held_out(s)]
    if "see" in stages:
        def measure_see() -> dict:
            out = {"images": trainer.choose(synthetic.image_choices(img_held)),
                   "images_other_image": trainer.choose(synthetic.image_choices(img_held, "other image"))}
            if held_texts:
                out["books_held_out"] = books_nats()
            return out
        history.append(trainer.stage(
            "see", synthetic.image_examples(img_train), set(plan.see_parts), plan.see_steps, plan.see_lr,
            measure_see, accept_skill("images", controls=["images_other_image"]), plan.see_batch, plan.seed + 1, budget))

    if "watch" in stages:
        vid_seeds = range(plan.videos)
        vid_train = [s for s in vid_seeds if not synthetic.held_out(s)]
        vid_held = [s for s in vid_seeds if synthetic.held_out(s)]
        examples = synthetic.video_examples(vid_train, plan.frames)
        rehearsal = synthetic.image_examples(img_train[: len(vid_train) // 2])  # so that seeing is not forgotten
        def measure_watch() -> dict:
            out = {"videos": trainer.choose(synthetic.video_choices(vid_held, plan.frames)),
                   "videos_reversed": trainer.choose(synthetic.video_choices(vid_held, plan.frames, "reversed")),
                   "videos_one_frame": trainer.choose(synthetic.video_choices(vid_held, plan.frames, "one frame")),
                   "images": trainer.choose(synthetic.image_choices(img_held))}
            if held_texts:
                out["books_held_out"] = books_nats()
            return out
        history.append(trainer.stage(
            "watch", examples + rehearsal, set(plan.watch_parts), plan.watch_steps, plan.watch_lr,
            measure_watch, accept_skill("videos", controls=["videos_reversed", "videos_one_frame"], keep=["images"]), plan.watch_batch, plan.seed + 2, budget))

    manifest = trainer.save(history, growth_steps)
    summary.update(stages=history, checkpoint=manifest["version"], own_sha256=manifest["own_sha256"],
                   parameters=model.count(), seconds=round(time.monotonic() - started, 1),
                   significance=_significance(history))
    (Path(root) / "summary.json").write_text(json.dumps(summary, indent=1, ensure_ascii=False), encoding="utf-8")
    return summary


def _significance(history: list[dict]) -> dict:
    """For each multiple-choice measurement after training: how likely that many right answers are by chance."""
    out = {}
    for record in history:
        for key, value in record["after"].items():
            if isinstance(value, dict) and "accuracy" in value and value["n"]:
                right = round(value["accuracy"] * value["n"])
                out[f"{record['stage']}:{key}"] = {"right": right, "n": value["n"], "chance": round(value["chance"], 4),
                                                   "p_by_chance": binomial_p(right, value["n"], value["chance"])}
    return out
