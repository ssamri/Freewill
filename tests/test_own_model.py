"""Freewill's own model (freewill/vlm): architecture, growth, checkpoints, rules, books and drawn data.

These run on the toy model (random weights, byte tokenizer) so that they run anywhere in seconds.
They check the mechanics, not that the real model learns: that is tools/own_model_e2e.py and
the "own model end to end" workflow.
"""

from __future__ import annotations

import importlib.util

import pytest

pytest.importorskip("PIL", reason="the drawn images need Pillow")

from freewill.vlm import books, synthetic  # noqa: E402

HAS_TORCH = all(importlib.util.find_spec(n) for n in ("torch", "transformers", "safetensors"))
needs_torch = pytest.mark.skipif(not HAS_TORCH, reason="needs torch, transformers and safetensors")


# -- data, no torch needed ----------------------------------------------------------

def test_gutenberg_markers_and_language():
    raw = ("Title: A Test\nLanguage: French\n\n*** START OF THE PROJECT GUTENBERG EBOOK A TEST ***\n"
           "Il était une fois.\n\n*** END OF THE PROJECT GUTENBERG EBOOK A TEST ***\nlicence text")
    assert books.header_field(raw, "Language") == "French"
    assert books.strip_gutenberg(raw) == "Il était une fois."
    with pytest.raises(ValueError):
        books.strip_gutenberg("no markers here")


def test_passages_keep_paragraphs_and_drop_scraps():
    text = "\n\n".join(" ".join(f"w{i}_{k}" for k in range(50)) for i in range(10)) + "\n\nshort."
    out = books.passages(text, words=120)
    assert all(20 <= len(p.split()) <= 120 for p in out)
    assert out[-1].endswith("short.")          # a short paragraph joins the passage before it
    assert sum(len(p.split()) for p in out) == 501
    assert books.passages("a scrap of five words") == []


def test_drawn_items_are_reproducible_and_split():
    a, b = synthetic.image_item(5), synthetic.image_item(5)
    assert a["colour"] == b["colour"] and a["image"].tobytes() == b["image"].tobytes()
    held = [s for s in range(100) if synthetic.held_out(s)]
    assert len(held) == 25
    video = synthetic.video_item(2, frames=4)
    assert len(video["frames"]) == 4 and video["direction"] in synthetic.DIRECTIONS
    reversed_ = synthetic.video_choices([2], 4, "reversed")[0]["parts"][0][1]
    assert reversed_[0][1].tobytes() == video["frames"][-1][1].tobytes()
    assert [t for t, _ in reversed_] == [t for t, _ in video["frames"]]  # times stay in order, pictures do not
    assert len(synthetic.video_choices([2], 4, "one frame")[0]["parts"][0][1]) == 1


def test_skill_rule_requires_beating_controls():
    from freewill.vlm.train import accept_skill
    before = {"images": {"accuracy": 0.2}, "images_other_image": {"accuracy": 0.2}}
    after = {"images": {"accuracy": 0.5}, "images_other_image": {"accuracy": 0.48}}
    kept, reason = accept_skill("images", controls=["images_other_image"])(before, after)
    assert not kept and "do not depend" in reason
    after["images_other_image"]["accuracy"] = 0.25
    assert accept_skill("images", controls=["images_other_image"])(before, after)[0]


def test_reading_rule_refuses_what_cannot_be_measured():
    from freewill.vlm.train import accept_reading
    assert not accept_reading({"books_held_out": float("nan")}, {"books_held_out": 1.0})[0]
    assert not accept_reading({"books_held_out": 2.0}, {"books_held_out": 1.995})[0]
    assert accept_reading({"books_held_out": 2.0}, {"books_held_out": 1.9})[0]


# -- the model ----------------------------------------------------------------------

@needs_torch
def test_growth_starts_as_identity_and_adds_parameters():
    from freewill.vlm.model import tiny
    m = tiny()
    item = synthetic.image_examples([1])[0]
    seq = m.sequence(item["parts"], item["answer"])
    before, count = float(m.losses([seq])), m.count()
    added = m.grow(2)
    assert len(added) == 2 and m.count()["layers"] == count["layers"] + 2
    assert m.count()["total"] > count["total"] and m.count()["grown_layers"] > 0
    assert abs(float(m.losses([m.sequence(item["parts"], item["answer"])])) - before) < 1e-5
    m.add_lora(4)
    assert abs(float(m.losses([m.sequence(item["parts"], item["answer"])])) - before) < 1e-5
    with pytest.raises(ValueError):
        m.grow(1)  # adapters are in place


@needs_torch
def test_growth_refused_above_ceiling():
    from freewill.vlm.model import tiny
    m = tiny()
    m.spec["ceiling_parameters"] = m.count()["total"] + 10
    with pytest.raises(ValueError, match="ceiling"):
        m.grow(1)


@needs_torch
def test_only_chosen_parts_train():
    from freewill.vlm.model import tiny
    m = tiny()
    m.grow(1)
    m.add_lora(4)
    names = {n for n, p in m.named_parameters() if p in set(m.trainable({"bridge"}))}
    assert names and all(n.startswith("bridge.") for n in names)
    grown = [n for n, p in m.named_parameters() if p.requires_grad] if m.trainable({"grown"}) else []
    assert grown and all(n.startswith(f"language.model.layers.{m.grown[0]}.") for n in grown)


@needs_torch
def test_pipeline_saves_and_rebuilds_the_same_model(tmp_path):
    from freewill.vlm import pipeline
    from freewill.vlm.model import tiny
    from freewill.vlm.train import Trainer, current, restore
    m = tiny()
    text = "\n\n".join(f"Chapter {i}. The keeper counted {i} ships while the fox slept under the lemon tree "
                       f"and the bell rang {i % 7} times over the harbour." for i in range(120))
    plan = pipeline.Plan(grow=1, rank=4, read_steps=5, read_lr=3e-3, read_words=40, see_steps=5, see_batch=2,
                         watch_steps=3, watch_batch=2, images=16, videos=8, held_books=6)
    summary = pipeline.run(m, tmp_path, [{"id": "t", "title": "t", "language": "English", "sha256": "", "text": text}],
                           plan, log=lambda *a: None)
    assert [s["stage"] for s in summary["stages"]] == ["read", "see", "watch"]
    assert all(s["decision"] in ("kept", "refused") for s in summary["stages"])
    assert (tmp_path / "ledger.jsonl").read_text().count("\n") == 3
    again = tiny()
    manifest = restore(again, current(tmp_path))
    assert manifest["parameters"] == again.count() == m.count()
    items = synthetic.image_choices([3])
    assert abs(Trainer(m, tmp_path).choose(items)["truth_nats"] - Trainer(again, tmp_path).choose(items)["truth_nats"]) < 1e-5


@needs_torch
def test_engine_answers_in_json_or_says_why():
    import base64
    import io
    from freewill.engines.base import EngineError
    from freewill.engines.own_model import OwnModelEngine
    from freewill.vlm.model import tiny
    buffer = io.BytesIO()
    synthetic.image_item(1)["image"].save(buffer, "PNG")
    engine = OwnModelEngine(model=tiny())
    try:
        engine.decide("You are a test.", "Hello", {"properties": {"say": {}}}, {},
                      [{"media_type": "image/png", "data": base64.b64encode(buffer.getvalue()).decode()}])
    except EngineError as error:  # a toy model with random weights does not write JSON
        assert "JSON" in str(error)
    assert engine.can_see and not engine.can_learn
