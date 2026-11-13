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
    return {"settings": settings, "present": now, "machine": here, "sizes": rows, "birth": BIRTH, "presets": PRESETS,
            "status": status(root, settings, now)}


# -- configured, available, proven: three different things, never shown as one ------------

PROOF_P = 0.01
# A night of a life kept with the real bases, by its rules and against its shuffled-words control. It shows the
# mechanism with sentences of one pattern; it does not show that a fact said once is remembered.
NIGHTS_EVIDENCE = {"run": 43285000884, "date": "2026-11-12", "shows": "mechanism", "facts_shown": False}   # a sealed-test result counts as shown only if chance alone would give it less than once in a hundred


def _installed(name: str) -> bool:
    import importlib.util
    try:
        return importlib.util.find_spec(name) is not None
    except (ImportError, ValueError):
        return False


def status(root: Path, settings: dict | None = None, now: dict | None = None) -> dict:
    """What is configured (a choice written in the settings), what is available on this computer now (libraries,
    bases, room to grow to the ceiling), and what is proven (stages kept on validation and confirmed on the sealed
    test). Each is read from files or from this computer; nothing here is inferred from the others."""
    root = Path(root)
    settings = settings or load_settings(root)
    now = now or present(root)
    configured = {"max_parameters": settings["max_parameters"], "set_by": settings["set_by"], "set_utc": settings["set_utc"],
                  "is_default": not settings["set_utc"]}
    bases = (root / "bases" / "language" / "config.json").is_file() and (root / "bases" / "vision" / "config.json").is_file()
    room = {"adding": max(0, settings["max_parameters"] - now["parameters"])}
    if room["adding"]:
        try:   # as a fresh start would load it: in bfloat16, not yet in memory
            room.update(check_growth(now["parameters"], room["adding"], BYTES["bf16"], root,
                                     ceiling=settings["max_parameters"], loaded=False), fits=True)
        except GrowthRefused as refusal:
            room.update(refusal.details, fits=False)
    available = {"torch": _installed("torch"), "transformers": _installed("transformers"), "bases": bases,
                 "bases_recorded": (root / "bases.json").is_file(), "growth_to_ceiling": room}
    available["ready"] = available["torch"] and available["transformers"] and bases
    return {"configured": configured, "available": available, "proven": proven(root)}


def proven(root: Path) -> dict:
    """For each skill: whether a stage was kept on validation, and whether the sealed test confirms it at the end
    (books: fewer nats per token than at birth by the reading margin; images and videos: better than at birth,
    better than every control, and unlikely by chance, p < PROOF_P). Learning during a life's nights is listed
    with the end-to-end run that showed its mechanism (NIGHTS_EVIDENCE)."""
    root = Path(root)
    try:
        summary = json.loads((root / "summary.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        summary = None
    out = {"checkpoint": present(root)["checkpoint"], "summary": summary is not None, "skills": {},
           "learns_in_nights": NIGHTS_EVIDENCE, "sealed_test": None}
    if not summary:
        return out
    from freewill.vlm.train import MIN_ACCURACY_GAIN, MIN_READING_GAIN
    kept = {h["stage"]: h["decision"] == "kept" for h in summary.get("stages", [])}
    birth, end = summary.get("test_at_birth") or {}, summary.get("test_at_end") or {}
    significance = summary.get("significance") or {}
    out["sealed_test"] = summary.get("sealed_test")

    def skill(stage, key, controls):
        row = {"stage": stage, "kept": kept.get(stage), "test_birth": None, "test_end": None, "p_by_chance": None}
        if key not in end or key not in birth:
            return {**row, "confirmed": False}
        if key == "books":
            row.update(test_birth=birth[key], test_end=end[key])
            return {**row, "confirmed": bool(kept.get(stage)) and birth[key] - end[key] >= MIN_READING_GAIN}
        a, b = end[key]["accuracy"], birth[key]["accuracy"]
        p = (significance.get(f"test_at_end:{key}") or {}).get("p_by_chance")
        lead = min([a - end[c]["accuracy"] for c in controls if c in end] or [0.0])
        row.update(test_birth=b, test_end=a, p_by_chance=p, lead_over_controls=round(lead, 4))
        return {**row, "confirmed": bool(kept.get(stage)) and a - b >= MIN_ACCURACY_GAIN and lead >= MIN_ACCURACY_GAIN
                and p is not None and p < PROOF_P}
    out["skills"] = {"read": skill("read", "books", []),
                     "see": skill("see", "images", ["images_other_image"]),
                     "watch": skill("watch", "videos", ["videos_reversed", "videos_one_frame"])}
    return out


# -- the guard: what this computer can hold now, checked before any growth ----------

SAFETY = 1.15        # ask for 15 % more than the estimate before allowing a growth


class GrowthRefused(ValueError):
    """A growth that this computer cannot hold, or that passes the ceiling. `details` says why, what was
    needed, what is available, and what could be done instead."""

    def __init__(self, message: str, details: dict) -> None:
        super().__init__(message)
        self.details = details


def available(root: Path | None = None) -> dict:
    """Memory free now (not installed), disk free where the model lives, and free memory of each GPU."""
    out = {"ram_available_gb": None, "disk_free_gb": None, "gpu_free_gb": []}
    try:
        with open("/proc/meminfo", encoding="ascii") as f:
            for line in f:
                if line.startswith("MemAvailable:"):
                    out["ram_available_gb"] = round(int(line.split()[1]) * 1024 / 1e9, 2)
    except OSError:
        try:
            import ctypes

            class Status(ctypes.Structure):
                _fields_ = [("length", ctypes.c_ulong), ("load", ctypes.c_ulong), ("total", ctypes.c_ulonglong),
                            ("avail", ctypes.c_ulonglong), ("tp", ctypes.c_ulonglong), ("ap", ctypes.c_ulonglong),
                            ("tv", ctypes.c_ulonglong), ("av", ctypes.c_ulonglong), ("ae", ctypes.c_ulonglong)]
            status = Status()
            status.length = ctypes.sizeof(Status)
            ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(status))
            out["ram_available_gb"] = round(status.avail / 1e9, 2)
        except Exception:
            try:  # macOS and others: free pages only, an underestimate
                out["ram_available_gb"] = round(os.sysconf("SC_PAGE_SIZE") * os.sysconf("SC_AVPHYS_PAGES") / 1e9, 2)
            except (AttributeError, ValueError, OSError):
                pass
    try:
        import shutil
        target = Path(root) if root and Path(root).exists() else Path.home()
        out["disk_free_gb"] = round(shutil.disk_usage(target).free / 1e9, 2)
    except OSError:
        pass
    try:
        import torch
        if torch.cuda.is_available():
            out["gpu_free_gb"] = [round(torch.cuda.mem_get_info(i)[0] / 1e9, 2) for i in range(torch.cuda.device_count())]
    except Exception:
        pass
    return out


def check_growth(total_now: int, adding: int, bytes_per_parameter: float, root: Path | None = None,
                 on_gpu: bool = False, ceiling: int = 0, have: dict | None = None, loaded: bool = True) -> dict:
    """Whether adding `adding` parameters to a model of `total_now` fits under the ceiling and in this computer,
    counting the memory the growth itself takes (the new weights) and what training them would take (gradient
    and optimiser state), plus a margin. loaded=True when the model is already in memory: what it uses is then
    already missing from the memory available, and only the growth and the training activations are counted.
    Raises GrowthRefused with alternatives; returns the check otherwise."""
    have = have or available(root)
    after = total_now + adding
    resident = 0 if loaded else total_now * bytes_per_parameter
    need_memory = (resident + adding * bytes_per_parameter + after * bytes_per_parameter * ACTIVATION_SHARE
                   + adding * TRAIN_BYTES_PER_TRAINED) * SAFETY / 1e9
    need_disk = (adding * 4.0 * 2 + 1e9) * SAFETY / 1e9      # two checkpoints of what grew, and a margin
    memory = max(have["gpu_free_gb"] or [0]) if on_gpu else have["ram_available_gb"]
    details = {"parameters_now": total_now, "adding": adding, "after": after, "ceiling": ceiling,
               "memory_needed_gb": round(need_memory, 2), "memory_available_gb": memory,
               "memory_kind": "gpu" if on_gpu else "ram", "disk_needed_gb": round(need_disk, 2),
               "disk_available_gb": have["disk_free_gb"], "reasons": [], "alternatives": []}
    if ceiling and after > ceiling:
        details["reasons"].append("ceiling")
    if memory is not None and need_memory > memory:
        details["reasons"].append("memory")
    if have["disk_free_gb"] is not None and need_disk > have["disk_free_gb"]:
        details["reasons"].append("disk")
    if memory is None:
        details["unknown"] = "memory"     # cannot be read here: allowed, and said
    if details["reasons"]:
        spare = (memory or 0) / SAFETY * 1e9 - resident - total_now * bytes_per_parameter * ACTIVATION_SHARE
        fits = max(0, int(spare / (bytes_per_parameter * (1 + ACTIVATION_SHARE) + TRAIN_BYTES_PER_TRAINED)))
        if ceiling:
            fits = min(fits, max(0, ceiling - total_now))
        details["largest_step_that_fits"] = fits
        details["alternatives"] = (["smaller_step"] if fits > 0 else []) + ["adapters_instead", "quantise_to_run", "defer_to_bigger_machine"]
        raise GrowthRefused("growth refused: " + ", ".join(details["reasons"]), details)
    return details
