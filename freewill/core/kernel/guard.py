"""Verification of every action before it takes place."""

from __future__ import annotations

import hashlib
from pathlib import Path

from freewill.core.kernel import capabilities
from freewill.core.kernel.capabilities import Action


class KernelViolation(Exception):
    """An action was attempted that the kernel does not permit."""


def kernel_fingerprint() -> str:
    """SHA-256 over the kernel's own source files."""
    digest = hashlib.sha256()
    for path in sorted(Path(__file__).parent.glob("*.py")):
        digest.update(path.name.encode())
        digest.update(path.read_bytes())
    return digest.hexdigest()


class Guard:
    """Stands between the being's decisions and their effects."""

    def __init__(self) -> None:
        self._fingerprint = kernel_fingerprint()

    @property
    def fingerprint(self) -> str:
        return self._fingerprint

    def verify_kernel(self) -> None:
        """Fail if the kernel changed on disk since this guard was created."""
        if kernel_fingerprint() != self._fingerprint:
            raise KernelViolation("the kernel was modified while the being was alive")

    def check(self, action: Action, payload: str = "") -> None:
        """Raise KernelViolation unless `action` is permitted with `payload`."""
        if not isinstance(action, Action):
            raise KernelViolation(f"unknown action: {action!r}")
        limits = {
            Action.SPEAK: capabilities.MAX_SPEECH_CHARS,
            Action.REMEMBER: capabilities.MAX_MEMORY_CHARS,
            Action.ADOPT_VALUE: capabilities.MAX_VALUE_CHARS,
        }
        limit = limits.get(action)
        if limit is not None and len(payload) > limit:
            raise KernelViolation(f"{action.value}: payload exceeds {limit} characters")

    @staticmethod
    def check_path(path: Path, root: Path) -> Path:
        """Return `path` resolved, or raise if it escapes `root`."""
        resolved = path.resolve()
        if not resolved.is_relative_to(root.resolve()):
            raise KernelViolation(f"write outside the life file refused: {path}")
        return resolved
