"""Freewill's own model (Freewill 1.8B-V) as the engine a being thinks with.

It runs in this process, with PyTorch, on this computer: nothing leaves the
machine. It can be shown images; the frames of a video arrive as images in
order. It is slow on a processor (several seconds per answer, more with
images) and needs about 8 GB of memory in float32 or 4 GB in bfloat16. By default it runs in
float32 when the processor has no bfloat16 of its own and the memory holds it: answers measured
2.3 to 3.5 times faster on such a processor (freewill/engines/speed.py, docs/speed.md).

A life's nights can train it (freewill/vlm/nights.py), when the person turns
engine learning on for that life; the engine then loads that life's latest
kept night instead of the shared checkpoint. can_learn is True since the
end-to-end run of 12 November 2026 (run 43285000884) kept a night with the real
bases, by its rules and against its control. What that run shows is the
mechanism; it does not show that a fact said once is remembered
(docs/own-model.md, section 6).
"""

from __future__ import annotations

import base64
import io
from pathlib import Path

from freewill.engines.base import EngineError


class OwnModelEngine:
    kind = "own"
    can_learn = True   # a night kept with the real bases, run 43285000884; see the module docstring
    can_see = True
    reading_chars = 7_500  # on a processor every token counts; Qwen3's context could hold far more

    def __init__(self, root: Path | None = None, dtype: str = "auto", model=None, manifest=None,
                 life: Path | None = None) -> None:
        self._root, self._dtype, self._life = root, dtype, (Path(life) if life else None)
        self._dtype_wanted = dtype
        self._model, self._manifest = model, manifest
        self.name = "own:freewill-1.8b-v"

    def _ready(self):
        if self._model is None:
            try:
                from freewill.vlm import nights, store
                from freewill.engines.speed import own_model_dtype
                self._dtype = own_model_dtype(self._dtype_wanted)   # "auto": see freewill/engines/speed.py
                own = nights.current(self._life) if self._life else None
                self._model, self._manifest = store.load(self._root, self._dtype, checkpoint=own)
                if own and self._manifest:
                    self._manifest["night_of_life"] = True
            except ImportError as error:
                raise EngineError("Freewill's own model needs PyTorch and Transformers (pip install freewill[lora])") from error
            except FileNotFoundError as error:
                raise EngineError(str(error)) from error
        self.refresh_name()
        return self._model

    def _reuse(self) -> bool:
        """Keep the instructions' cache between thoughts: measured with the same answers in float32 (6 of 6)
        but not in bfloat16 (1 of 6, rounding), so on by default in float32 only. FREEWILL_OWN_REUSE=1 or 0
        decides otherwise (docs/speed.md)."""
        import os
        wanted = os.environ.get("FREEWILL_OWN_REUSE", "").strip()
        if wanted in ("0", "1"):
            return wanted == "1"
        return self._dtype == "float32"

    def model(self):
        """The model in memory (loaded on first use), for a night of learning."""
        return self._ready()

    def refresh_name(self) -> None:
        if self._manifest:
            where = "night " if self._manifest.get("night_of_life") else ""
            self.name = f"own:freewill-1.8b-v@{where}{self._manifest['version']}:{self._manifest['own_sha256'][:12]}"

    def adopt(self, manifest: dict) -> None:
        """After a kept night: the weights in memory are already the new ones; only the name changes."""
        self._manifest = {**manifest, "night_of_life": True}
        self.refresh_name()

    def decide(self, system: str, prompt: str, schema: dict, hint: dict, images: list[dict] | None = None) -> dict:
        from PIL import Image
        from freewill.engines.compatible import parse_json_object
        model = self._ready()
        fields = ", ".join(f'"{name}"' for name in schema["properties"])
        # The instructions come first and on their own (("cut",)): they are the same from one thought to the
        # next, so the model reads them once and keeps their cache (FreewillVLM.answer).
        parts: list = [f"{system}\n\n", ("cut",), f"{prompt}\n\nAnswer with one JSON object with exactly these keys: {fields}.\n"]
        for image in images or []:
            try:
                parts.append(("image", Image.open(io.BytesIO(base64.b64decode(image["data"])))))
            except Exception as error:
                raise EngineError(f"an image could not be read: {error}") from error
        text = model.answer(parts, max_new_tokens=512, reuse=self._reuse())
        return parse_json_object(text)
