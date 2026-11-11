"""Claude, through the official Anthropic SDK.

Install with `pip install "freewill[anthropic]"`. Credentials are resolved by
the SDK from the environment (ANTHROPIC_API_KEY, or a profile created by
`ant auth login`); they are never written to the life file.
"""

from __future__ import annotations

import json

from freewill.engines.base import EngineError, EngineRefusal

DEFAULT_MODEL = "claude-opus-5-5"
# The loop asks for one short decision at a time, many times an hour.
DEFAULT_EFFORT = "low"
# Models for which the API can re-run a declined request on another model.
_SERVER_SIDE_FALLBACK = {
    "claude-fable-5-2", "claude-fable-5-1", "claude-opus-5-5", "claude-opus-5", "claude-sonnet-5-5",
}


class AnthropicEngine:
    can_learn = False

    def __init__(self, model: str | None = None, effort: str | None = None) -> None:
        try:
            import anthropic
        except ImportError as error:
            raise EngineError(
                'the Anthropic SDK is not installed; run: pip install "freewill[anthropic]"'
            ) from error
        self._anthropic = anthropic
        self.model = model or DEFAULT_MODEL
        self.effort = effort or DEFAULT_EFFORT
        self.name = f"anthropic:{self.model}"
        from freewill.keys import get_key
        key = get_key("anthropic")
        # With no stored key, the SDK resolves credentials from the environment itself.
        self._client = anthropic.Anthropic(api_key=key) if key else anthropic.Anthropic()

    def decide(self, system: str, prompt: str, schema: dict, hint: dict) -> dict:
        anthropic = self._anthropic
        request: dict = {
            "model": self.model,
            "max_tokens": 16000,
            "system": system,
            "messages": [{"role": "user", "content": prompt}],
            "output_config": {
                "effort": self.effort,
                "format": {"type": "json_schema", "schema": schema},
            },
        }
        try:
            if self.model in _SERVER_SIDE_FALLBACK:
                response = self._client.beta.messages.create(
                    betas=["server-side-fallback-2026-07-01"], fallbacks="default", **request
                )
            else:
                response = self._client.messages.create(**request)
        except anthropic.RateLimitError as error:
            raise EngineError(f"rate limited: {error.message}", retryable=True) from error
        except anthropic.APIStatusError as error:
            raise EngineError(
                f"API error {error.status_code}: {error.message}", retryable=error.status_code >= 500
            ) from error
        except anthropic.APIConnectionError as error:
            raise EngineError("could not reach the Anthropic API", retryable=True) from error

        if response.stop_reason == "refusal":
            raise EngineRefusal("the model declined to respond")
        if response.stop_reason == "max_tokens":
            raise EngineError("the response was cut off before it was complete")
        text = next((block.text for block in response.content if block.type == "text"), None)
        if text is None:
            raise EngineError("the response contained no text")
        try:
            return json.loads(text)
        except json.JSONDecodeError as error:
            raise EngineError("the response was not valid JSON") from error
