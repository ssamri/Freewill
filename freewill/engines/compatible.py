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
    can_see = True  # if the model behind it can; otherwise the images are withdrawn, see decide()

    def __init__(self, base_url: str, model: str, key_env: str | None, kind: str = "compatible") -> None:
        self.kind = kind
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

    def decide(self, system: str, prompt: str, schema: dict, hint: dict,
               images: list[dict] | None = None) -> dict:
        try:
            return self._ask(system, prompt, schema, images)
        except EngineError as error:
            # A model that cannot take images answers with a client error. The being
            # still hears the message: ask again without them, and say so.
            if not images or error.retryable or not getattr(error, "client_error", False):
                raise
            note = ("\n\n(The images could not be shown to you: the model you think with "
                    "does not accept images. Say so if it matters.)")
            return self._ask(system, prompt + note, schema, None)

    def _headers(self) -> dict:
        headers = {"Content-Type": "application/json"}
        if self.key_env:
            from freewill.keys import get_key
            key = get_key(self.kind) or os.environ.get(self.key_env)
            if not key:
                raise EngineError(f"no access key for this engine: add one in the settings, "
                                  f"or set the {self.key_env} environment variable")
            headers["Authorization"] = f"Bearer {key}"
        return headers

    def _response_format(self, schema: dict) -> dict:
        return {"type": "json_object"}

    def _extra_body(self) -> dict:
        return {}

    def _ask(self, system: str, prompt: str, schema: dict, images: list[dict] | None) -> dict:
        fields = ", ".join(f'"{name}"' for name in schema["properties"])
        text = f"{prompt}\n\nAnswer with one JSON object with exactly these keys: {fields}."
        content: str | list = text
        if images:
            content = [{"type": "text", "text": text}] + [
                {"type": "image_url",
                 "image_url": {"url": f"data:{image['media_type']};base64,{image['data']}"}}
                for image in images
            ]
        body = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": content},
            ],
            "response_format": self._response_format(schema),
        }
        body.update(self._extra_body())
        headers = self._headers()

        request = urllib.request.Request(
            f"{self.base_url}/chat/completions",
            data=json.dumps(body).encode("utf-8"), headers=headers, method="POST",
        )
        try:
            with (getattr(self, "_opener", None) or urllib.request.build_opener()).open(request, timeout=600) as response:
                payload = json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as error:
            detail = error.read().decode("utf-8", "replace")[:300]
            failure = EngineError(
                f"HTTP {error.code} from {self.base_url}: {detail}",
                retryable=error.code == 429 or error.code >= 500,
            )
            failure.client_error = error.code in (400, 415, 422)
            raise failure from error
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
