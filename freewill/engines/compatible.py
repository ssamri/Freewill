"""Any service that speaks the OpenAI chat-completions format.

This covers OpenAI (GPT), xAI (Grok) and open models served locally, for
example by Ollama. It uses only the standard library. The API key is read
from an environment variable and is never written to the life file.
"""

from __future__ import annotations

import json
import os
import re
import urllib.error
import urllib.request

from freewill.engines.base import EngineError

PRESETS = {
    "openai": {"base_url": "https://api.openai.com/v1", "key_env": "OPENAI_API_KEY"},
    "xai": {"base_url": "https://api.x.ai/v1", "key_env": "XAI_API_KEY"},
    # A model running on this machine: private, free, and needs no key.
    "local": {"base_url": "http://localhost:11434/v1", "key_env": None},
    "compatible": {"base_url": None, "key_env": "FREEWILL_API_KEY"},
}


class CompatibleEngine:
    can_learn = False

    def __init__(self, base_url: str, model: str, key_env: str | None, kind: str = "compatible") -> None:
        if not base_url:
            raise EngineError("this engine needs a base URL (--base-url)")
        if not model:
            raise EngineError("this engine needs a model name (--model)")
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.key_env = key_env
        self.name = f"{kind}:{model}"

    @classmethod
    def from_config(cls, config: dict) -> "CompatibleEngine":
        kind = config.get("kind", "compatible")
        preset = PRESETS[kind]
        return cls(
            base_url=config.get("base_url") or preset["base_url"],
            model=config.get("model"),
            key_env=preset["key_env"],
            kind=kind,
        )

    def decide(self, system: str, prompt: str, schema: dict, hint: dict) -> dict:
        fields = ", ".join(f'"{name}"' for name in schema["properties"])
        body = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": f"{prompt}\n\nAnswer with one JSON object with exactly these keys: {fields}."},
            ],
            "response_format": {"type": "json_object"},
        }
        headers = {"Content-Type": "application/json"}
        if self.key_env:
            key = os.environ.get(self.key_env)
            if not key:
                raise EngineError(f"set the {self.key_env} environment variable to use this engine")
            headers["Authorization"] = f"Bearer {key}"

        request = urllib.request.Request(
            f"{self.base_url}/chat/completions",
            data=json.dumps(body).encode("utf-8"), headers=headers, method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=180) as response:
                payload = json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as error:
            detail = error.read().decode("utf-8", "replace")[:300]
            raise EngineError(
                f"HTTP {error.code} from {self.base_url}: {detail}",
                retryable=error.code == 429 or error.code >= 500,
            ) from error
        except (urllib.error.URLError, TimeoutError) as error:
            raise EngineError(f"could not reach {self.base_url}: {error}", retryable=True) from error

        try:
            text = payload["choices"][0]["message"]["content"] or ""
        except (KeyError, IndexError, TypeError) as error:
            raise EngineError("unexpected response shape from the engine") from error
        return parse_json_object(text)


def parse_json_object(text: str) -> dict:
    """Parse the first JSON object in `text`, tolerating prose or code fences around it."""
    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", text, re.DOTALL)
        if not match:
            raise EngineError("the engine did not return a JSON object") from None
        try:
            data = json.loads(match.group(0))
        except json.JSONDecodeError as error:
            raise EngineError("the engine returned malformed JSON") from error
    if not isinstance(data, dict):
        raise EngineError("the engine did not return a JSON object")
    return data
