"""The common interface every engine implements."""

from __future__ import annotations

from pathlib import Path
from typing import Protocol


class EngineError(Exception):
    """The engine could not produce a decision. `retryable` says whether to wait and try again."""

    def __init__(self, message: str, *, retryable: bool = False) -> None:
        super().__init__(message)
        self.retryable = retryable


class EngineRefusal(EngineError):
    """The underlying model declined to respond."""


class Engine(Protocol):
    name: str
    # Whether this engine can rewrite its own parameters during sleep.
    # External engines cannot: for them, consolidation bears on the life file only.
    can_learn: bool
    # Whether this engine can be shown images. Whether it really understands
    # them depends on the model behind it.
    can_see: bool
    reading_chars: int  # how many characters of a document one moment of reading can hold

    def decide(self, system: str, prompt: str, schema: dict, hint: dict,
               images: list[dict] | None = None) -> dict:
        """Return a JSON object matching `schema`.

        `images`, when given, are {media_type, data(base64)} items to look at
        along with the prompt.

        `hint` carries the same situation in structured form, for engines that
        do not read prose (the simulated engine).
        """
        ...


def make_engine(config: dict) -> Engine:
    """Build the engine described in a life file's identity."""
    kind = config.get("kind", "simulated")
    if kind == "simulated":
        from freewill.engines.simulated import SimulatedEngine
        return SimulatedEngine()
    if kind == "anthropic":
        from freewill.engines.anthropic_engine import AnthropicEngine
        return AnthropicEngine(model=config.get("model"), effort=config.get("effort"))
    if kind == "embedded":
        from freewill import models
        from freewill.engines.embedded import EmbeddedEngine
        from freewill.paths import data_dir
        model = models.find(str(config.get("model")))
        if model is None:
            raise EngineError(f"unknown embedded model: {config.get('model')!r}")
        store = models.ModelStore(Path(config.get("models_dir") or data_dir() / "models"))
        paths = store.paths(model)
        # The adapter this life learned and accepted, if any: given by whoever opens the life
        # (freewill.learning.engine.EngineLearning.active), never stored in the engine description.
        return EmbeddedEngine(model, paths["model"], paths["mmproj"], adapter=config.get("adapter"))
    if kind == "own":
        from freewill.engines.own_model import OwnModelEngine
        return OwnModelEngine(Path(config["dir"]) if config.get("dir") else None, config.get("dtype", "bfloat16"),
                              life=Path(config["life"]) if config.get("life") else None)
    if kind in ("openai", "xai", "local", "compatible"):
        from freewill.engines.compatible import CompatibleEngine
        return CompatibleEngine.from_config(config)
    raise EngineError(f"unknown engine kind: {kind!r}")
