"""Images and videos drawn here, with questions whose answers are known exactly.

They exist to measure, without doubt about the answer, whether the model uses
what it sees: the colour and the shape of a figure in an image, the direction
in which a figure moves across the frames of a video. Every item is drawn from
a seed, so a run can be reproduced to the pixel. Items come from three
separate namespaces of seeds: "train" (trained on), "validation" (used to
decide whether a stage is kept) and "test" (sealed: never trained on, never
used to decide anything, measured only to report). The same seed number in two
namespaces draws two unrelated items.

The controls matter as much as the scores: the same questions asked about the
image of another item, or about a video's frames in reverse order, or about a
single frame of it. A model that answers from the picture must do worse on
them; a model that answers from habit does not.

Drawn figures are not the world. Passing these tests shows that the eye and
the bridge carry colour, shape and motion to the language model, nothing more.
"""

from __future__ import annotations

import random

from PIL import Image, ImageDraw

COLOURS = {"red": (220, 40, 40), "green": (40, 170, 60), "blue": (40, 80, 220),
           "yellow": (235, 205, 40), "purple": (140, 60, 180), "orange": (240, 140, 30)}
SHAPES = ["circle", "square", "triangle", "cross"]
DIRECTIONS = ["left", "right", "up", "down"]
QUESTIONS = {
    "colour": "What colour is the shape? Answer with one word.",
    "shape": "What is the shape? Answer with one word.",
    "motion": "Which way does the shape move? Answer with one word: left, right, up or down.",
}
SIZE = 224


def _draw(shape: str, colour: tuple, centre: tuple[float, float], radius: float, background: tuple, size: int = SIZE) -> Image.Image:
    image = Image.new("RGB", (size, size), background)
    d = ImageDraw.Draw(image)
    x, y, r = centre[0] * size, centre[1] * size, radius * size
    if shape == "circle":
        d.ellipse([x - r, y - r, x + r, y + r], fill=colour)
    elif shape == "square":
        d.rectangle([x - r, y - r, x + r, y + r], fill=colour)
    elif shape == "triangle":
        d.polygon([(x, y - r), (x - r, y + r), (x + r, y + r)], fill=colour)
    else:
        w = r / 3
        d.rectangle([x - r, y - w, x + r, y + w], fill=colour)
        d.rectangle([x - w, y - r, x + w, y + r], fill=colour)
    return image


def _background(rng: random.Random) -> tuple:
    grey = rng.randint(200, 250)
    return (grey, grey, rng.randint(200, 250))


SPLITS = ("train", "validation", "test")


def _key(kind: str, split: str, seed: int) -> str:
    if split not in SPLITS:
        raise ValueError(f"unknown split {split!r}")
    return f"{kind}-{split}-{seed}"


def image_item(seed: int, split: str = "train") -> dict:
    rng = random.Random(_key("image", split, seed))
    colour = rng.choice(list(COLOURS))
    shape = rng.choice(SHAPES)
    centre = (rng.uniform(0.3, 0.7), rng.uniform(0.3, 0.7))
    image = _draw(shape, COLOURS[colour], centre, rng.uniform(0.14, 0.24), _background(rng))
    return {"seed": seed, "split": split, "image": image, "colour": colour, "shape": shape}


def video_item(seed: int, frames: int = 4, split: str = "train") -> dict:
    rng = random.Random(_key("video", split, seed))
    colour, shape, direction = rng.choice(list(COLOURS)), rng.choice(SHAPES), rng.choice(DIRECTIONS)
    background, radius = _background(rng), rng.uniform(0.1, 0.15)
    start, end = rng.uniform(0.2, 0.3), rng.uniform(0.7, 0.8)
    other = rng.uniform(0.35, 0.65)
    shots = []
    for k in range(frames):
        t = start + (end - start) * k / max(1, frames - 1)
        along = {"right": t, "left": 1 - t, "down": t, "up": 1 - t}[direction]
        centre = (along, other) if direction in ("left", "right") else (other, along)
        shots.append((k * 0.5, _draw(shape, COLOURS[colour], centre, radius, background)))
    return {"seed": seed, "split": split, "frames": shots, "colour": colour, "shape": shape, "direction": direction}


def image_examples(seeds, split: str = "train") -> list[dict]:
    """Training examples: two questions per image."""
    out = []
    for seed in seeds:
        item = image_item(seed, split)
        out.append({"parts": [("image", item["image"]), "\n" + QUESTIONS["colour"]], "answer": item["colour"]})
        out.append({"parts": [("image", item["image"]), "\n" + QUESTIONS["shape"]], "answer": item["shape"]})
    return out


def video_examples(seeds, frames: int = 4, split: str = "train") -> list[dict]:
    out = []
    for seed in seeds:
        item = video_item(seed, frames, split)
        out.append({"parts": [("video", item["frames"]), "\n" + QUESTIONS["motion"]], "answer": item["direction"]})
    return out


def image_choices(seeds, control: str | None = None, split: str = "validation") -> list[dict]:
    """Multiple-choice items. control="other image": each question is asked about another item's image."""
    items = [image_item(s, split) for s in seeds]
    out = []
    for k, item in enumerate(items):
        shown = items[(k + 1) % len(items)]["image"] if control == "other image" else item["image"]
        out.append({"kind": "colour", "parts": [("image", shown), "\n" + QUESTIONS["colour"]],
                    "candidates": list(COLOURS), "truth": list(COLOURS).index(item["colour"])})
        out.append({"kind": "shape", "parts": [("image", shown), "\n" + QUESTIONS["shape"]],
                    "candidates": SHAPES, "truth": SHAPES.index(item["shape"])})
    return out


def video_choices(seeds, frames: int = 4, control: str | None = None, split: str = "validation") -> list[dict]:
    """control="reversed": frames in reverse order (the true answer flips);
    control="one frame": only the middle frame (motion cannot be seen)."""
    out = []
    for seed in seeds:
        item = video_item(seed, frames, split)
        shots = item["frames"]
        if control == "reversed":
            shots = [(t, f) for (t, _), (_, f) in zip(shots, reversed(shots))]
        elif control == "one frame":
            shots = [shots[len(shots) // 2]]
        out.append({"kind": "motion", "parts": [("video", shots), "\n" + QUESTIONS["motion"]],
                    "candidates": DIRECTIONS, "truth": DIRECTIONS.index(item["direction"])})
    return out
