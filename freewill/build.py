"""Which code is running, and what each part of it can really do today.

The version alone does not say which code a person runs: a release is built
from one commit, and the main branch moves on. The packaging workflow writes
`build.json` beside this file with the exact commit it built; from a source
checkout the commit is read from git. Nothing here guesses: what cannot be
known is reported as unknown.

The status of each capability distinguishes four states, so that a setting
that is merely configured is never shown as a validated training:
  active      it is running for the life that is awake;
  available   it can be switched on with what is installed on this computer;
  unavailable something it needs is missing here (a package, a model, a file);
  not_connected  the code exists but is not wired to a life's nights yet.
Each one also says what has been demonstrated end to end, and where.
"""

from __future__ import annotations

import importlib.util
import json
import subprocess
from pathlib import Path

from freewill import __version__

_HERE = Path(__file__).resolve().parent
_cached: dict | None = None

# What has been shown end to end, and by what. Facts about the code and its CI, not about a given computer.
EVIDENCE = {
    "engine_lora": "ci_cpu_e2e",          # .github/workflows/engine-e2e.yml: Qwen3 1.7B, LoRA trained on CPU, loaded by llama.cpp
    "own_model": "ci_small_and_real_e2e",  # .github/workflows/own-model-e2e.yml: stages on a miniature, then on the real bases
    "own_model_nights": "none",            # OwnModelEngine.can_learn is False: a life's nights do not train it
    "auxiliary_learner": "unit_tests",     # the small trainable module of H4, EXP-06
    "gpu": "none",                         # no run on a GPU has been published
    "macos": "none",                       # no build or run on macOS has been published
}


def _git(*args: str) -> str | None:
    try:
        out = subprocess.run(["git", "-C", str(_HERE.parent), *args], capture_output=True, text=True, timeout=5)
    except (OSError, subprocess.SubprocessError):
        return None
    return out.stdout.strip() if out.returncode == 0 and out.stdout.strip() else None


def info() -> dict:
    """Version, commit, build date and channel of the running code."""
    global _cached
    if _cached is not None:
        return dict(_cached)
    found = {"version": __version__, "commit": None, "built_utc": None, "channel": "source", "dirty": None,
             "tag": None}
    stamp = _HERE / "build.json"
    if stamp.exists():
        try:
            data = json.loads(stamp.read_text(encoding="utf-8"))
            found.update({k: data.get(k) for k in ("commit", "built_utc", "channel", "tag")})
            found["dirty"] = False
        except (OSError, ValueError):
            pass
    if not found["commit"]:
        found["commit"] = _git("rev-parse", "HEAD")
        if found["commit"]:
            found["dirty"] = bool(_git("status", "--porcelain", "--untracked-files=no"))
            found["tag"] = _git("describe", "--tags", "--exact-match", "HEAD")
    found["short"] = found["commit"][:10] if found["commit"] else None
    # A version that does not match its tag is said, not hidden.
    found["tag_matches"] = None if not found["tag"] else found["tag"] == f"v{__version__}"
    _cached = found
    return dict(found)


def _has(module: str) -> bool:
    try:
        return importlib.util.find_spec(module) is not None
    except (ImportError, ValueError):
        return False


def capabilities(runner=None, models_store=None) -> list[dict]:
    """The real state of each learning capability, for the life that is awake (if any)."""
    engine = runner.engine if runner else None
    identity = runner.life.identity.get("engine", {}) if runner else {}
    lora_packages = all(_has(m) for m in ("torch", "peft", "transformers"))
    own_packages = all(_has(m) for m in ("torch", "transformers"))
    rows = []

    # The engine a life converses with, adapted by LoRA (Qwen3 1.7B embedded).
    state, reason = "unavailable", "needs_lora_packages"
    if engine is not None and getattr(engine, "can_learn", False):
        adapter = (getattr(engine, "adapter", None) or {}).get("version")
        if lora_packages:
            state, reason = ("active", "adapter_loaded") if adapter else ("available", "no_adapter_yet")
        else:
            state, reason = "unavailable", "needs_lora_packages"
    elif identity.get("kind") not in (None, "embedded"):
        state, reason = "unavailable", "engine_cannot_learn"
    elif lora_packages:
        state, reason = "available", "choose_trainable_model"
    rows.append({"id": "engine_lora", "state": state, "reason": reason, "evidence": EVIDENCE["engine_lora"]})

    # Freewill 1.8B-V: it converses, it is trained by stages, but not during the nights of a life.
    own_running = identity.get("kind") == "own"
    rows.append({"id": "own_model", "state": ("active" if own_running else "available") if own_packages else "unavailable",
                 "reason": "running" if own_running else ("installed" if own_packages else "needs_own_model_packages"),
                 "evidence": EVIDENCE["own_model"]})
    rows.append({"id": "own_model_nights", "state": "not_connected", "reason": "can_learn_false",
                 "evidence": EVIDENCE["own_model_nights"]})

    # The small trainable module of H4 (research setting "learner").
    learner = bool(getattr(runner.being.research, "learner", False)) if runner else False
    rows.append({"id": "auxiliary_learner", "state": "active" if learner else ("available" if _has("torch") else "unavailable"),
                 "reason": "research_setting_on" if learner else ("research_setting_off" if _has("torch") else "needs_torch"),
                 "evidence": EVIDENCE["auxiliary_learner"]})

    # Remote engines: they converse, their weights are never changed by a life.
    remote = identity.get("kind") in ("anthropic", "openai", "xai", "compatible", "local")
    rows.append({"id": "remote_engine", "state": "active" if remote else "available", "reason": "weights_never_change",
                 "evidence": "not_applicable"})
    return rows


def about(runner=None, models_store=None) -> dict:
    """What the interface shows under “About this build”."""
    engine = None
    if runner is not None:
        identity = runner.life.identity.get("engine", {})
        engine = {"kind": identity.get("kind"), "model": identity.get("model"), "name": runner.engine.name,
                  "can_learn": bool(getattr(runner.engine, "can_learn", False)),
                  "adapter": (getattr(runner.engine, "adapter", None) or {}).get("version")}
    return {"build": info(), "engine": engine, "capabilities": capabilities(runner, models_store),
            "untested": [k for k in ("gpu", "macos") if EVIDENCE[k] == "none"]}
