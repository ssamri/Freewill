"""Access keys for external engines.

Keys live in the operating system's credential store (Windows Credential
Manager, macOS Keychain, Secret Service) when the `keyring` package is
installed, and otherwise only in environment variables. They are never
written to a life file.
"""

from __future__ import annotations

import os

SERVICE = "Freewill"
ENV = {
    "anthropic": "ANTHROPIC_API_KEY",
    "openai": "OPENAI_API_KEY",
    "xai": "XAI_API_KEY",
    "compatible": "FREEWILL_API_KEY",
}


def _keyring():
    try:
        import keyring
        return keyring
    except Exception:  # not installed, or no usable backend
        return None


def get_key(kind: str) -> str | None:
    """The key for an engine kind: credential store first, then the environment."""
    keyring = _keyring()
    if keyring is not None:
        try:
            stored = keyring.get_password(SERVICE, kind)
            if stored:
                return stored
        except Exception:
            pass
    variable = ENV.get(kind)
    return os.environ.get(variable) if variable else None


def set_key(kind: str, key: str) -> bool:
    """Store a key in the credential store. Returns False if none is available."""
    keyring = _keyring()
    if keyring is None:
        return False
    try:
        keyring.set_password(SERVICE, kind, key)
        return True
    except Exception:
        return False


def has_key(kind: str) -> bool:
    return bool(get_key(kind))
