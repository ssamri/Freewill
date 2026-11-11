"""Learning from a life: what would change the parameters of a local model, and whether this machine can do it.

Four things are kept apart, because they are not the same: a memory store that
is read back (what Freewill does today), adapters trained beside a frozen
base, changes to the base weights, and growth in the number of parameters.
Nothing here pretends. Where training cannot run, the answer is "not
available", with the reason; no counter rises on its own, and a manifest
records only what was really done.
"""

from __future__ import annotations

import importlib.util
import os
import shutil
from pathlib import Path

from freewill import models
from freewill.research.schemas import new, new_id, utc_now

LEARNING_VERSION = "1.0"
MIN_FREE_MEMORY_GB = 12
METHODS = ("lora",)  # the closed list of operations an orchestrator outside the kernel may run


def _memory_gb() -> float | None:
    try:
        return round(os.sysconf("SC_PAGE_SIZE") * os.sysconf("SC_AVPHYS_PAGES") / 1e9, 1)
    except (ValueError, OSError, AttributeError):
        return None


def capabilities(models_dir: Path | None = None) -> dict:
    """What this machine could do, found by looking, not assumed."""
    torch = importlib.util.find_spec("torch") is not None
    peft = importlib.util.find_spec("peft") is not None
    gpu = None
    if torch:
        try:
            import torch as _torch
            gpu = _torch.cuda.get_device_name(0) if _torch.cuda.is_available() else None
        except Exception:
            gpu = None
    memory = _memory_gb()
    folder = Path(models_dir or Path.home())
    while not folder.exists() and folder != folder.parent:
        folder = folder.parent
    disk = round(shutil.disk_usage(folder).free / 1e9, 1)
    reasons = []
    if not (torch and peft):
        reasons.append("no_torch")
    reasons.append("gguf_only")  # the catalogue ships inference files only; a trainable base is not provided yet
    if memory is not None and memory < MIN_FREE_MEMORY_GB:
        reasons.append("low_memory")
    return {"torch": torch, "peft": peft, "gpu": gpu, "free_memory_gb": memory, "free_disk_gb": disk,
            "min_free_memory_gb": MIN_FREE_MEMORY_GB, "inference": True, "training_available": False,
            "growth_available": False, "reasons": reasons, "learning_version": LEARNING_VERSION}


def model_versions(store: "models.ModelStore") -> list[dict]:
    """The local models as they are: frozen inference files. None has adapters; none is trainable in this format."""
    out = []
    for entry in models.catalogue():
        if store.installed(entry):
            out.append(new("ModelVersion", model_version=f"{entry['id']}-base", base_model_id=entry["id"],
                           base_parameters=entry.get("parameters"), format="gguf", sha256=entry.get("sha256"),
                           licence=entry.get("licence"), adapters=[], trainable=False))
    return out


def manifest_for(model: dict) -> dict:
    """The growth manifest of a model that was never trained: every count of added parameters is zero."""
    return new("GrowthManifest", model_version=model["model_version"], base_model_id=model["base_model_id"],
               base_parameters=model["base_parameters"], trainable_adapter_parameters=0,
               added_module_parameters=0, active_parameters=model["base_parameters"], training_method="none",
               checkpoint_before=model["sha256"], checkpoint_after=model["sha256"], heldout_evaluation_id=None,
               decision="not_trained", note="No training was run. Structural growth is not available.")


def request_job(life_id: str, method: str, *, approved_by_human: bool, models_dir: Path | None = None) -> dict:
    """Ask for a learning job. It is recorded and refused with its reasons unless everything needed is there."""
    if method not in METHODS:
        raise ValueError(f"unknown learning method: {method!r}")
    found = capabilities(models_dir)
    reasons = list(found["reasons"]) + ([] if approved_by_human else ["not_approved"])
    return new("LearningJob", job_id=new_id("job"), life_id=life_id, method=method,
               status="refused" if reasons else "queued", reason=", ".join(reasons) or None,
               approved_by_human=bool(approved_by_human), budget={"max_minutes": 0}, created_utc=utc_now())
