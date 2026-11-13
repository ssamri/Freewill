"""A life's nights, for Freewill's own model: what the being lived is learned while it sleeps.

The same corpus, settings, approval and ledger as the nights of an embedded
model (freewill/learning/engine.py, freewill/learning/corpus.py): units kept
by provenance and split by episode into train, validation and a sealed test
that no night reads; the being's own replies not trained on unless the person
allows it; the person's name needed to turn learning on. What
differs is what is trained and where it is kept:

    trained   the low-rank adapters of Freewill 1.8B-V, in place, in this process
    measured  nats per token on the life's validation units (new ones, and those of
              earlier nights) and on the reference texts shipped with Freewill
    kept      only if the new validation units are predicted better by MIN_GAIN, by
              MIN_GAIN more than a control trained on the same words shuffled, and
              neither the reference texts (against the model before this night) nor
              earlier nights get worse beyond their tolerances; otherwise the weights
              of before the night are restored
    saved     <life>/engine/own/checkpoints/vNNNN: a whole checkpoint of what Freewill
              trained (bridge, adapters, grown weights), which the engine of this life
              loads instead of the shared one

Nothing here decides whether the being "learned" anything in a wider sense.
An end-to-end run with the real bases kept a night (run 43285000884), so
OwnModelEngine.can_learn is True; what that shows, and what it does not, is in
docs/own-model.md, section 6.
"""

from __future__ import annotations

import hashlib
import time
from pathlib import Path

from freewill.learning import corpus as lived
from freewill.learning import engine as nightly

FOLDER = "own"
NIGHT_RANK = 8           # adapters added for the nights if the model has none yet


def folder(life_path: Path) -> Path:
    return Path(life_path) / nightly.FOLDER / FOLDER


def current(life_path: Path) -> Path | None:
    from freewill.vlm.train import current as pointer
    return pointer(folder(life_path))


def _sha(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def night(model, life_path: Path, log=print, force: bool = False) -> dict:
    """One night. Returns the ledger row of the life's engine learning (kind "own_night" or "skipped").
    The units are chosen exactly as for the local model (rules of learning/engine.py): trainable units of the
    train split, validation units that are not near duplicates of training ones, vouched facts always replayed,
    and a control trained on the same words in a random order, which the night must beat."""
    from freewill.vlm.train import MAX_FORGETTING, Trainer

    learning = nightly.EngineLearning(life_path)
    settings = learning.settings
    if not settings.enabled and not force:
        raise nightly.EngineLearningError("engine learning is off for this life")
    learning.collect()
    own = settings.learn_from_own_replies
    train_rows = [r for r in learning._split_rows("train") if lived.trainable(r, own_replies=own)]
    new_items = [r for r in train_rows if r["night"] is None][:nightly.MAX_ITEMS_PER_NIGHT]
    old_items = [r for r in train_rows if r["night"] is not None]
    measured = [r for r in learning._split_rows("validation") if lived.trainable(r, own_replies=own)]
    clean, leaked = lived.without_leaks(measured, train_rows)
    new_held = [r for r in clean if r["night"] is None]
    old_held = [r for r in clean if r["night"] is not None]
    if len(new_items) < nightly.MIN_TRAIN or len(new_held) + len(old_held) < nightly.MIN_HELD_OUT:
        return learning.record("skipped", engine="own", reason="not_enough_lived", new_items=len(new_items),
                               held_out_items=len(new_held) + len(old_held), leaked=len(leaked),
                               needs={"train": nightly.MIN_TRAIN, "held_out": nightly.MIN_HELD_OUT})

    night_id = "n%04d" % (1 + sum(1 for row in learning.ledger() if row.get("kind") == "own_night"))
    facts = [r for r in old_items if r["provenance"] == "verified"]
    others = [r for r in old_items if r["provenance"] != "verified"]
    replay = facts + sorted(others, key=lambda r: _sha(night_id + r["sha256"]))[:int(len(new_items) * nightly.REPLAY_SHARE)]
    rehearsal = []
    if settings.rehearsal:
        pool = sorted(nightly.rehearsal_items(), key=lambda r: _sha(night_id + r["text"]))
        rehearsal = pool[:max(1, int(len(new_items) * nightly.REHEARSAL_SHARE))]
    texts = [nightly.item_text(learning.training_item(r)) for r in new_items + replay] + [r["text"] for r in rehearsal]
    examples = [{"parts": [], "answer": t, "chat": False} for t in texts]
    eval_new = [nightly.item_text(learning.training_item(r)) for r in (new_held or old_held)]
    eval_old = [nightly.item_text(learning.training_item(r)) for r in old_held] if new_held else []
    reference = [nightly.item_text(r) for r in nightly.reference_items()]

    if not model.lora_rank:
        model.add_lora(NIGHT_RANK)
    trainer = Trainer(model, folder(life_path), log)

    def measure() -> dict:
        out = {"life_new": round(trainer.reading_nats(eval_new), 4), "reference": round(trainer.reading_nats(reference), 4)}
        if eval_old:
            out["life_old"] = round(trainer.reading_nats(eval_old), 4)
        return out

    control = None
    if settings.control_each_night:     # the same start, the same steps, the same words in a random order
        start = model.own_state()
        before = measure()
        shuffled = [{"parts": [], "answer": nightly.shuffled_words(t, night_id + str(i)), "chat": False}
                    for i, t in enumerate(texts)]
        control_training = trainer.fit(shuffled, {"lora"}, settings.steps, settings.lr, 2, settings.seed)
        after = measure()
        model.load_own_state(start)
        control = {"before": before, "after": after, "training": control_training,
                   "gain": round(before["life_new"] - after["life_new"], 4)}

    def rule(before: dict, after: dict) -> tuple[bool, str]:
        gain = before["life_new"] - after["life_new"]
        forgot = after["reference"] - before["reference"]
        if gain < nightly.MIN_GAIN:
            return False, f"validation units of this life: {gain:+.4f} nats/token, less than the {nightly.MIN_GAIN} required"
        if control is not None and gain - control["gain"] < nightly.MIN_GAIN:
            return False, (f"validation units: {gain:+.4f} nats/token, but the shuffled-words control gives "
                           f"{control['gain']:+.4f}: the order of the words was not what was learned")
        if forgot > MAX_FORGETTING:
            return False, f"reference texts got worse by {forgot:.4f} nats/token (tolerance {MAX_FORGETTING})"
        if "life_old" in before:
            older = after["life_old"] - before["life_old"]
            if older > nightly.MAX_LIFE_FORGETTING:
                return False, f"earlier nights got worse by {older:.4f} nats/token (tolerance {nightly.MAX_LIFE_FORGETTING})"
        return True, f"validation units of this life predicted better by {gain:.4f} nats/token" + (
            f", {gain - control['gain']:.4f} more than the control" if control else "")

    started = time.monotonic()
    record = trainer.stage("night", examples, {"lora"}, settings.steps, settings.lr, measure, rule,
                           batch=2, seed=settings.seed,
                           notes={"night": night_id, "train_items_new": len(new_items),
                                  "train_items_replayed": len(replay), "train_items_rehearsal": len(rehearsal),
                                  "held_out_new": len(new_held), "held_out_earlier": len(old_held), "leaked": len(leaked),
                                  "reference_items": len(reference), "control": control})
    learning._mark_night({r["sha256"] for r in new_items} | {r["sha256"] for r in new_held}, night_id)
    checkpoint = trainer.save([record])["version"] if record["decision"] == "kept" else None
    return learning.record("own_night", engine="own", night=night_id,
                           decision="accepted" if checkpoint else "rejected", reason=record["reason"],
                           before=record["before"], after=record["after"], training=record["training"],
                           checkpoint=checkpoint, parameters=record["parameters"],
                           seconds=round(time.monotonic() - started, 1),
                           **{k: record[k] for k in ("train_items_new", "train_items_replayed", "train_items_rehearsal",
                                                     "held_out_new", "held_out_earlier", "leaked", "reference_items",
                                                     "control")})
