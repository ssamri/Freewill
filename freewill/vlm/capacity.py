"""How large Freewill's own model may grow, chosen by the person, and what each size asks of a computer.

The ceiling is no longer fixed in the code: the person chooses the largest
number of parameters the model may reach (2 billion, 5, 50, or any other
number), in the settings or with `freewill own-model settings`. Growth is
refused above that number, and refused below what the model already has.

For any size, `requirements()` says what it would take, in four parts:
storing it (disk), running it (memory, processor or graphics card),
training what grows (memory with the base frozen, and with everything
trained), and the text and computation needed for the new parameters to be
worth more than their count. These are estimates from simple formulas, all
written below with their assumptions; they are not measurements, except the
model's present size, which is counted from its tensors.

This module needs neither PyTorch nor Transformers, so the interface can
answer even on a computer where the model is not installed.
"""

from __future__ import annotations

import json
import math
import os
import time
from pathlib import Path

DEFAULT_MAX = 2_000_000_000
BIRTH = 1_823_955_200            # counted from the tensors of the assembled model (docs/own-model.md)
PRESETS = [2_000_000_000, 5_000_000_000, 13_000_000_000, 50_000_000_000]

# Assumptions, stated once. Effective speeds are a fraction of the advertised peak.
BYTES = {"bf16": 2.0, "int8": 1.0, "q4": 0.56}
TRAIN_BYTES_PER_TRAINED = 16.0   # fp32 weight + gradient + two Adam moments
ACTIVATION_SHARE = 0.20          # activations and caches, as a share of the weights' memory
TOKENS_PER_PARAMETER = 20        # text needed per newly trained parameter (compute-optimal rule of thumb)
TOKENS_PER_BOOK = 120_000        # an average novel
DEVICES = [  # id, memory in GB, effective trillions of operations per second when training
    ("cpu8", None, 0.2),     # a processor with 8 cores
    ("gpu12", 12, 25.0),     # a graphics card with 12 GB (e.g. RTX 4070)
    ("gpu24", 24, 65.0),     # a graphics card with 24 GB (e.g. RTX 4090)
    ("h100", 80, 400.0),     # a data-centre GPU with 80 GB (e.g. H100)
]


def settings_path(root: Path) -> Path:
    return Path(root) / "settings.json"


def load_settings(root: Path) -> dict:
    try:
        data = json.loads(settings_path(root).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        data = {}
    return {"max_parameters": int(data.get("max_parameters") or DEFAULT_MAX),
            "set_by": data.get("set_by", ""), "set_utc": data.get("set_utc", "")}


def save_settings(root: Path, max_parameters: int, who: str = "", current: int | None = None) -> dict:
    """Write the person's ceiling. Refused below the model's present size, or below its size at birth."""
    value = int(max_parameters)
    floor = max(BIRTH, current or 0)
    if value < floor:
        raise ValueError(f"the ceiling cannot be below the model's present size ({floor:,} parameters)")
    Path(root).mkdir(parents=True, exist_ok=True)
    data = {"max_parameters": value, "set_by": who, "set_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}
    settings_path(root).write_text(json.dumps(data, indent=1), encoding="utf-8")
    return data


def machine() -> dict:
    """What this computer has, as far as can be read without extra packages."""
    out = {"cpu_cores": os.cpu_count(), "ram_gb": None, "disk_free_gb": None, "gpus": []}
    try:
        out["ram_gb"] = round(os.sysconf("SC_PAGE_SIZE") * os.sysconf("SC_PHYS_PAGES") / 1e9, 1)
    except (AttributeError, ValueError, OSError):
        try:  # Windows
            import ctypes

            class Status(ctypes.Structure):
                _fields_ = [("length", ctypes.c_ulong), ("load", ctypes.c_ulong), ("total", ctypes.c_ulonglong),
                            ("avail", ctypes.c_ulonglong), ("tp", ctypes.c_ulonglong), ("ap", ctypes.c_ulonglong),
                            ("tv", ctypes.c_ulonglong), ("av", ctypes.c_ulonglong), ("ae", ctypes.c_ulonglong)]
            status = Status()
            status.length = ctypes.sizeof(Status)
            ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(status))
            out["ram_gb"] = round(status.total / 1e9, 1)
        except Exception:
            pass
    try:
        import shutil
        out["disk_free_gb"] = round(shutil.disk_usage(Path.home()).free / 1e9, 1)
    except OSError:
        pass
    try:
        import torch
        if torch.cuda.is_available():
            out["gpus"] = [{"name": torch.cuda.get_device_name(i),
                            "memory_gb": round(torch.cuda.get_device_properties(i).total_memory / 1e9, 1)}
                           for i in range(torch.cuda.device_count())]
    except Exception:
        pass
    return out


def _gb(n_bytes: float) -> float:
    return round(n_bytes / 1e9, 1)


def requirements(target: int, current: int = BIRTH) -> dict:
    """What a model of `target` parameters asks of a computer, grown from one of `current`."""
    target = int(target)
    new = max(0, target - current)
    run = {k: _gb(target * b * (1 + ACTIVATION_SHARE)) for k, b in BYTES.items()}
    frozen = _gb(target * BYTES["bf16"] + new * TRAIN_BYTES_PER_TRAINED + target * BYTES["bf16"] * ACTIVATION_SHARE)
    full = _gb(target * TRAIN_BYTES_PER_TRAINED * (1 + ACTIVATION_SHARE))
    tokens = new * TOKENS_PER_PARAMETER
    operations = 6.0 * target * tokens
    times = []
    for name, memory, speed in DEVICES:
        seconds = operations / (speed * 1e12) if operations else 0.0
        units = 1 if memory is None else max(1, math.ceil(frozen / memory))
        times.append({"device": name, "count": units, "days": round(seconds / units / 86400, 1)})
    disk = _gb(target * BYTES["bf16"] + new * 4.0 * 2) + 20  # bases, two checkpoints of what grew, books and caches
    gpu_for_running = next((m for _, m, _ in DEVICES[1:] if m and run["q4"] <= m), None)
    return {
        "target": target, "current": current, "new_parameters": new,
        "disk_gb": round(disk, 1),
        "run_memory_gb": run,                               # bf16, 8-bit, 4-bit
        "run_on_processor_ram_gb": run["bf16"],
        "run_gpu": {"memory_gb": gpu_for_running or 80, "count": 1 if gpu_for_running else math.ceil(run["q4"] / 80)},
        "train_frozen_base_gb": frozen,                     # only what grew is trained
        "train_everything_gb": full,
        "tokens_needed": int(tokens), "books_needed": int(math.ceil(tokens / TOKENS_PER_BOOK)),
        "operations": operations, "training_time": times,
        "cpu_cores_advised": 8 if target <= 3e9 else 16,
        "assumptions": {"bytes_per_parameter": BYTES, "train_bytes_per_trained_parameter": TRAIN_BYTES_PER_TRAINED,
                        "activation_share": ACTIVATION_SHARE, "tokens_per_new_parameter": TOKENS_PER_PARAMETER,
                        "tokens_per_book": TOKENS_PER_BOOK,
                        "effective_tera_operations": {name: speed for name, _, speed in DEVICES}},
    }


def verdict(req: dict, here: dict) -> dict:
    """Whether this computer can store, run and train a model of that size, on each count."""
    ram, disk, gpus = here.get("ram_gb"), here.get("disk_free_gb"), here.get("gpus") or []
    vram = max((g["memory_gb"] for g in gpus), default=0)
    def ok(need, have):
        return None if have is None else have >= need
    return {"store": ok(req["disk_gb"], disk),
            "run": ok(req["run_memory_gb"]["q4"], max(ram or 0, vram)) if ram is not None or vram else None,
            "run_bf16": ok(req["run_memory_gb"]["bf16"], max(ram or 0, vram)) if ram is not None or vram else None,
            "train_frozen_base": ok(req["train_frozen_base_gb"], max(vram, ram or 0)) if ram is not None or vram else None}


def present(root: Path) -> dict:
    """The model's present size: from its checkpoint in use if there is one, else its size at birth."""
    try:
        version = json.loads((Path(root) / "current.json").read_text(encoding="utf-8"))["version"]
        manifest = json.loads((Path(root) / "checkpoints" / version / "manifest.json").read_text(encoding="utf-8"))
        return {"parameters": int(manifest["parameters"]["total"]), "checkpoint": version, "counted": True}
    except (OSError, ValueError, KeyError):
        return {"parameters": BIRTH, "checkpoint": None, "counted": False}


def public(root: Path, target: int | None = None) -> dict:
    """Everything the settings card shows: the ceiling, the present size, this computer, and what each
    preset and the chosen target ask for."""
    settings = load_settings(root)
    now = present(root)
    here = machine()
    sizes = sorted(set(PRESETS + [settings["max_parameters"]] + ([int(target)] if target else [])))
    rows = []
    for size in sizes:
        req = requirements(size, now["parameters"])
        rows.append({**req, "fits_here": verdict(req, here)})
    return {"settings": settings, "present": now, "machine": here, "sizes": rows, "birth": BIRTH, "presets": PRESETS}
