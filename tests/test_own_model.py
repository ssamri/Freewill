"""Freewill's own model (freewill/vlm): architecture, growth, checkpoints, rules, books and drawn data.

These run on the toy model (random weights, byte tokenizer) so that they run anywhere in seconds.
They check the mechanics, not that the real model learns: that is tools/own_model_e2e.py and
the "own model end to end" workflow.
"""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path

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
    other = [synthetic.image_item(5, split) for split in ("validation", "test")]
    assert all(o["image"].tobytes() != a["image"].tobytes() for o in other)   # three separate namespaces
    with pytest.raises(ValueError):
        synthetic.image_item(5, "everything")
    video = synthetic.video_item(2, frames=4, split="validation")
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
    assert not accept_reading({"books_validation": float("nan")}, {"books_validation": 1.0})[0]
    assert not accept_reading({"books_validation": 2.0}, {"books_validation": 1.995})[0]
    assert accept_reading({"books_validation": 2.0}, {"books_validation": 1.9})[0]


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
                         watch_steps=3, watch_batch=2, images=16, videos=8, validation_images=6, validation_videos=4,
                         test_images=6, test_videos=4, validation_books=6, test_books=6)
    book = [{"id": "t", "title": "t", "language": "English", "sha256": "", "text": text}]
    summary = pipeline.run(m, tmp_path, book, plan, log=lambda *a: None)
    assert [s["stage"] for s in summary["stages"]] == ["read", "see", "watch"]
    assert all(s["decision"] in ("kept", "refused") for s in summary["stages"])
    assert (tmp_path / "ledger.jsonl").read_text(encoding="utf-8").count("\n") == 4          # three stages and the sealed test
    assert "images" in summary["test_at_birth"] and "videos" in summary["test_at_end"]
    for stage in summary["stages"]:                                          # no rule ever saw the sealed test
        assert "test" not in json.dumps(stage["before"]) and "test" not in json.dumps(stage["after"])
    with pytest.raises(ValueError, match="sealed"):                          # the test cannot be changed afterwards
        pipeline.run(tiny(), tmp_path, book, pipeline.Plan(**{**plan.__dict__, "test_images": 7}), log=lambda *a: None)
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


@needs_torch
def test_instructions_read_once_give_the_same_answer():
    from freewill.vlm.model import tiny
    model = tiny()
    parts = ["You are a test. Answer briefly.\n\n", ("cut",), "Hello, who are you?"]
    other = ["You are a test. Answer briefly.\n\n", ("cut",), "Something else entirely."]
    plain = model.answer(parts, max_new_tokens=12, reuse=False)
    assert model._head is None
    first = model.answer(parts, max_new_tokens=12)
    assert model._head is not None
    assert model.answer(other, max_new_tokens=12) == model.answer(other, max_new_tokens=12, reuse=False)
    assert first == plain == model.answer(parts, max_new_tokens=12)   # the cache is copied, never extended in place
    model.train()   # weights about to change: the cache is dropped
    assert model._head is None
    model.eval()


# -- capacity: the ceiling the person chooses, and what each size asks for --------

def test_ceiling_is_the_persons_choice(tmp_path):
    from freewill.vlm import capacity
    assert capacity.load_settings(tmp_path)["max_parameters"] == capacity.DEFAULT_MAX
    capacity.save_settings(tmp_path, 50_000_000_000, "ANASS")
    assert capacity.load_settings(tmp_path)["max_parameters"] == 50_000_000_000
    with pytest.raises(ValueError):
        capacity.save_settings(tmp_path, 1_000_000_000)          # below the size at birth
    with pytest.raises(ValueError):
        capacity.save_settings(tmp_path, 3_000_000_000, current=4_000_000_000)


def test_requirements_grow_with_size():
    from freewill.vlm import capacity
    small, large = capacity.requirements(2_000_000_000), capacity.requirements(50_000_000_000)
    for key in ("disk_gb", "train_frozen_base_gb", "train_everything_gb", "tokens_needed", "books_needed"):
        assert large[key] > small[key]
    assert large["run_memory_gb"]["q4"] < large["run_memory_gb"]["int8"] < large["run_memory_gb"]["bf16"]
    assert capacity.requirements(capacity.BIRTH)["new_parameters"] == 0
    public = capacity.public(Path("/nonexistent-own-model"), 5_000_000_000)
    assert any(row["target"] == 5_000_000_000 for row in public["sizes"])


@needs_torch
def test_widening_keeps_the_output_and_the_old_weights(tmp_path):
    import torch
    from freewill.vlm.model import tiny
    from freewill.vlm.train import Trainer, current, restore
    m = tiny()
    item = synthetic.image_examples([1])[0]
    loss = lambda model: float(model.losses([model.sequence(item["parts"], item["answer"])]).detach())  # noqa: E731
    before, born = loss(m), m.language.config.intermediate_size
    m.widen(32)
    assert abs(loss(m) - before) < 1e-5 and m.count()["grown_neurons"] > 0
    m.add_lora(4)
    gate = m.layers()[0].mlp.gate_proj.base.weight
    old = gate.detach().clone()
    trainer = Trainer(m, tmp_path, log=lambda *a: None)
    trainer.fit(synthetic.image_examples(range(8)), {"grown"}, 3, 1e-2, 2)
    assert torch.equal(old[:born], gate[:born]) and not torch.equal(old[born:], gate[born:])
    trainer.save([])
    again = tiny()
    restore(again, current(tmp_path))
    assert again.count() == m.count() and abs(loss(again) - loss(m)) < 1e-5


@needs_torch
def test_grow_to_stops_at_the_ceiling():
    from freewill.vlm.model import tiny
    m = tiny()
    m.spec["ceiling_parameters"] = 400_000
    m.grow_to(10_000_000)
    assert m.count()["total"] <= 400_000 and m.growth_log


def test_book_splits_keep_neighbours_together():
    from freewill.vlm import pipeline
    text = "\n\n".join(" ".join(f"w{i}_{k}" for k in range(30)) for i in range(600))
    sets = pipeline.split_books([{"id": "b", "text": text}], 30)
    assert sets["test"] and sets["validation"] and sets["train"]
    assert not set(sets["test"]) & set(sets["train"]) and not set(sets["validation"]) & set(sets["train"])
    index = {p: i for i, p in enumerate(books.passages(text, 30))}
    for name in ("test", "validation"):                                      # whole blocks of consecutive passages
        assert len({index[p] // books.BLOCK for p in sets[name]}) * books.BLOCK == len(sets[name])


def test_guard_refuses_what_this_computer_cannot_hold():
    from freewill.vlm import capacity
    small = {"ram_available_gb": 8.0, "disk_free_gb": 100.0, "gpu_free_gb": []}
    capacity.check_growth(1_800_000_000, 50_000_000, 2.0, have=small)
    with pytest.raises(capacity.GrowthRefused) as refused:
        capacity.check_growth(1_800_000_000, 3_000_000_000, 2.0, have=small)
    details = refused.value.details
    assert "memory" in details["reasons"] and "adapters_instead" in details["alternatives"]
    assert 0 < details["largest_step_that_fits"] < 3_000_000_000
    capacity.check_growth(1_800_000_000, details["largest_step_that_fits"], 2.0, have=small)   # the step offered fits
    with pytest.raises(capacity.GrowthRefused):
        capacity.check_growth(1_800_000_000, 50_000_000, 2.0, have={**small, "disk_free_gb": 0.5})


@needs_torch
def test_model_growth_goes_through_the_guard(tmp_path):
    from freewill.vlm import capacity, pipeline
    from freewill.vlm.model import tiny
    m = tiny()
    def guard(total, adding):
        raise capacity.GrowthRefused("growth refused: memory", {"reasons": ["memory"], "alternatives": ["adapters_instead"]})
    m.guard = guard
    before = m.count()
    with pytest.raises(capacity.GrowthRefused):
        m.grow(1)
    assert m.count() == before
    summary = pipeline.run(m, tmp_path, [], pipeline.Plan(grow=1, rank=4, see_steps=1, images=4, validation_images=2,
                                                           test_images=2), log=lambda *a: None, stages=("see",))
    assert summary["growth_refused"]["reasons"] == ["memory"] and m.count()["grown_count"] == 0


def test_status_keeps_configured_available_and_proven_apart(tmp_path):
    from freewill.vlm import capacity
    root = tmp_path / "own"
    root.mkdir()
    st = capacity.status(root)
    assert st["configured"]["is_default"] and st["configured"]["max_parameters"] == capacity.DEFAULT_MAX
    assert st["available"]["bases"] is False and st["available"]["ready"] is False
    assert st["proven"] == {"checkpoint": None, "summary": False, "skills": {}, "learns_in_nights": False, "sealed_test": None}
    # a run whose see stage was kept, and whose sealed test agrees, beyond chance and beyond the control
    acc = lambda a, n=50: {"accuracy": a, "n": n, "chance": 0.25}
    summary = {"stages": [{"stage": "read", "decision": "refused"}, {"stage": "see", "decision": "kept"}],
               "test_at_birth": {"books": 3.0, "images": acc(0.25), "images_other_image": acc(0.25)},
               "test_at_end": {"books": 2.995, "images": acc(0.8), "images_other_image": acc(0.3)},
               "significance": {"test_at_end:images": {"p_by_chance": 1e-9}}, "sealed_test": {"sha256": "x"}}
    (root / "summary.json").write_text(json.dumps(summary), encoding="utf-8")
    skills = capacity.status(root)["proven"]["skills"]
    assert skills["see"]["confirmed"] is True
    assert skills["read"]["confirmed"] is False         # refused on validation, and too small a change anyway
    assert skills["watch"]["kept"] is None and skills["watch"]["confirmed"] is False
    summary["test_at_end"]["images_other_image"] = acc(0.78)   # the control does as well: not seeing
    (root / "summary.json").write_text(json.dumps(summary), encoding="utf-8")
    assert capacity.status(root)["proven"]["skills"]["see"]["confirmed"] is False


def _lived(life, days=80):
    """A person tells the being about their neighbours, one exchange at a time: varied enough that validation
    units are not near duplicates of training ones."""
    life.mkdir(parents=True, exist_ok=True)
    names = ["Amina", "Bruno", "Chloe", "Driss", "Elena", "Farid", "Greta", "Hugo", "Ines", "Jamal"]
    animals = ["cats", "goats", "hens", "ducks", "rabbits", "bees", "sheep", "horses"]
    places = ["mill", "river", "bakery", "station", "orchard", "harbour", "chapel", "market", "bridge"]
    with open(life / "events.log", "a", encoding="utf-8") as f:
        for i in range(days):
            said = f"{names[i % 10]} keeps {i % 7 + 2} {animals[i % 8]} behind the old {places[i % 9]}."
            f.write(json.dumps({"type": "stage", "source": "message", "text": said}) + "\n")
            f.write(json.dumps({"type": "speech", "spontaneous": False, "text": "I will remember that."}) + "\n")


@needs_torch
def test_a_night_of_a_life_trains_the_own_model_and_is_kept_by_its_rule(tmp_path):
    from freewill.engines.own_model import OwnModelEngine
    from freewill.learning.engine import EngineLearning, EngineLearningError
    from freewill.vlm import nights
    from freewill.vlm.model import tiny
    life = tmp_path / "life"
    _lived(life)
    m = tiny()
    with pytest.raises(EngineLearningError):        # off until a person turns it on
        nights.night(m, life, log=lambda *a: None)
    EngineLearning(life).configure({"enabled": True, "steps": 60, "lr": 3e-3}, who="test")
    row = nights.night(m, life, log=lambda *a: None)
    assert row["kind"] == "own_night" and row["decision"] == "accepted", row["reason"]
    assert row["after"]["life_new"] < row["before"]["life_new"] - 0.01
    assert nights.current(life).name == row["checkpoint"]
    again = nights.night(m, life, log=lambda *a: None)
    assert again["kind"] == "skipped"                  # nothing new was lived
    assert OwnModelEngine.can_learn is False           # not claimed before an end-to-end run with the real bases
    rows = [json.loads(l) for l in (nights.folder(life) / "ledger.jsonl").read_text(encoding="utf-8").splitlines()]
    assert rows[-1]["stage"] == "night" and rows[-1]["decision"] == "kept"
