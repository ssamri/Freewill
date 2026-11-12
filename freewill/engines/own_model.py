"""Freewill's own model (Freewill 1.8B-V) as the engine a being thinks with.

It runs in this process, with PyTorch, on this computer: nothing leaves the
machine. It can be shown images; the frames of a video arrive as images in
order. It is slow on a processor (several seconds per answer, more with
images) and needs about 8 GB of memory in float32 or 4 GB in bfloat16.

can_learn is False: the nightly cycle of freewill/learning/engine.py adapts
models run by llama.cpp; Freewill's own model is trained by its own stages
(freewill/vlm/train.py), not yet from a life's nights.
"""

from __future__ import annotations

import base64
import io
from pathlib import Path

from freewill.engines.base import EngineError


class OwnModelEngine:
    kind = "own"
    can_learn = False
    can_see = True

    def __init__(self, root: Path | None = None, dtype: str = "bfloat16", model=None, manifest=None) -> None:
        self._root, self._dtype = root, dtype
        self._model, self._manifest = model, manifest
        self.name = "own:freewill-1.8b-v"

    def _ready(self):
        if self._model is None:
            try:
                from freewill.vlm import store
                self._model, self._manifest = store.load(self._root, self._dtype)
            except ImportError as error:
                raise EngineError("Freewill's own model needs PyTorch and Transformers (pip install freewill[lora])") from error
            except FileNotFoundError as error:
                raise EngineError(str(error)) from error
        if self._manifest:
            self.name = f"own:freewill-1.8b-v@{self._manifest['version']}:{self._manifest['own_sha256'][:12]}"
        return self._model

    def decide(self, system: str, prompt: str, schema: dict, hint: dict, images: list[dict] | None = None) -> dict:
        from PIL import Image
        from freewill.engines.compatible import parse_json_object
        model = self._ready()
        fields = ", ".join(f'"{name}"' for name in schema["properties"])
        parts: list = [f"{system}\n\n{prompt}\n\nAnswer with one JSON object with exactly these keys: {fields}.\n"]
        for image in images or []:
            try:
                parts.append(("image", Image.open(io.BytesIO(base64.b64decode(image["data"])))))
            except Exception as error:
                raise EngineError(f"an image could not be read: {error}") from error
        text = model.answer(parts, max_new_tokens=512)
        return parse_json_object(text)
