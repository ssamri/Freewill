"""The common interface every engine implements."""

from __future__ import annotations

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

    def decide(self, system: str, prompt: str, schema: dict, hint: dict) -> dict:
        """Return a JSON object matching `schema`.

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
    if kind in ("openai", "xai", "local", "compatible"):
        from freewill.engines.compatible import CompatibleEngine
        return CompatibleEngine.from_config(config)
    raise EngineError(f"unknown engine kind: {kind!r}")
