"""How fast a local engine runs on this computer: the processor's real cores, and drafting.

Two ideas here come from reading colibri (https://github.com/JustVugg/colibri, Apache 2.0, by
Vincenzo Fornaro). No code was taken from it: llama.cpp already implements both, and this module
only decides how to ask for them.

- Threads. On a processor with simultaneous multithreading, two logical cores share one physical
  core's arithmetic units, so one thread per physical core can be faster. Measured (docs/speed.md):
  not on Windows, so the default stays every logical core but one; FREEWILL_THREADS=physical asks.
- Drafting by looking back ("prompt lookup", an n-gram draft). The engine guesses the next few
  tokens by finding the text it has just written earlier in the prompt or the answer, then checks
  all the guesses in one pass of the model. With greedy decoding the text is the same token for
  token; only the time changes, and only when guesses are accepted. Freewill's answers repeat the
  prompt often (names, quoted words, JSON keys), which is where this could pay. Measured
  (docs/speed.md): it did not, on Qwen3 1.7B on a processor, so it is off by default.

Overrides, for measurements and for a person who wants to try: FREEWILL_THREADS (a number,
"logical" or "physical") and FREEWILL_DRAFT ("off", "ngram" or "ngram-mod").
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path


def logical_cores() -> int:
    return max(1, os.cpu_count() or 1)


def physical_cores() -> int | None:
    """The number of physical cores, or None when this system does not say."""
    try:
        if sys.platform.startswith("linux"):
            return _linux_physical()
        if sys.platform == "darwin":
            out = subprocess.run(["sysctl", "-n", "hw.physicalcpu"], capture_output=True, text=True, timeout=5)
            return int(out.stdout.strip()) if out.returncode == 0 and out.stdout.strip().isdigit() else None
        if sys.platform == "win32":
            return _windows_physical()
    except Exception:   # whatever goes wrong here, the answer is "this system does not say"
        return None
    return None


def _linux_physical() -> int | None:
    cores = set()
    for cpu in Path("/sys/devices/system/cpu").glob("cpu[0-9]*"):
        topology = cpu / "topology"
        try:
            package = (topology / "physical_package_id").read_text().strip()
            core = (topology / "core_id").read_text().strip()
        except OSError:
            continue
        cores.add((package, core))
    if cores:
        return len(cores)
    seen, package = set(), "0"   # some containers hide sysfs: fall back to /proc/cpuinfo
    try:
        for line in Path("/proc/cpuinfo").read_text().splitlines():
            key, _, value = line.partition(":")
            key, value = key.strip(), value.strip()
            if key == "physical id":
                package = value
            elif key == "core id":
                seen.add((package, value))
    except OSError:
        return None
    return len(seen) or None


def _windows_physical() -> int | None:
    import ctypes
    from ctypes import wintypes

    # GetLogicalProcessorInformationEx(RelationProcessorCore): one record per physical core.
    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    function = kernel32.GetLogicalProcessorInformationEx
    function.argtypes = [ctypes.c_int, ctypes.c_void_p, ctypes.POINTER(wintypes.DWORD)]
    function.restype = wintypes.BOOL
    size = wintypes.DWORD(0)
    function(0, None, ctypes.byref(size))  # RelationProcessorCore = 0; first call asks for the size
    if size.value == 0:
        return None
    buffer = ctypes.create_string_buffer(size.value)
    if not function(0, buffer, ctypes.byref(size)):
        return None
    count, offset = 0, 0
    while offset < size.value:
        # SYSTEM_LOGICAL_PROCESSOR_INFORMATION_EX: Relationship (DWORD), Size (DWORD), ...
        relationship = int.from_bytes(buffer.raw[offset:offset + 4], "little")
        record = int.from_bytes(buffer.raw[offset + 4:offset + 8], "little")
        if record == 0:
            break
        count += relationship == 0
        offset += record
    return count or None


def threads() -> int:
    """How many threads llama-server computes with. Default: every logical core but one, as before. The
    physical cores were measured too (docs/speed.md): about 5 % faster on Linux, about 4 % slower on Windows,
    where generating text lost more than reading the prompt gained. FREEWILL_THREADS=physical asks for them."""
    wanted = os.environ.get("FREEWILL_THREADS", "").strip().lower()
    if wanted.isdigit() and int(wanted) > 0:
        return int(wanted)
    logical = logical_cores()
    if wanted == "logical":
        return logical
    if wanted == "physical":
        return physical_cores() or logical
    return max(1, logical - 1)


DRAFTS = ("off", "ngram", "ngram-mod")


def draft(default: str) -> str:
    wanted = os.environ.get("FREEWILL_DRAFT", "").strip().lower()
    return wanted if wanted in DRAFTS else default


def draft_arguments(kind: str) -> list[str]:
    """llama-server (b12306) arguments for a kind of draft. "ngram" looks back in the prompt and the
    answer for the last few tokens (llama.cpp's ngram-simple) and offers what followed them as
    drafted tokens; "ngram-mod" is llama.cpp's other n-gram drafter. llama.cpp's own sizes are kept."""
    if kind == "ngram":
        return ["--spec-type", "ngram-simple"]
    if kind == "ngram-mod":
        return ["--spec-type", "ngram-mod"]
    return []


# -- Freewill's own model (PyTorch) -------------------------------------------------------------

FLOAT32_RAM_GB = 12  # 1.82 B parameters at 4 bytes is 7.3 GB, plus the cache and the program: room for both


def native_bfloat16() -> bool | None:
    """Whether this processor computes in bfloat16 itself (AVX512-BF16 or AMX). Without it, PyTorch converts
    every bfloat16 weight on the fly. Measured on two GitHub runners (AMD EPYC, 4 threads, docs/speed.md):
    a 96-token answer took 2.3 to 3.5 times longer than in float32, reading the instructions 4.5 to 7 times.
    None when PyTorch cannot say."""
    try:
        import torch
        cpu = torch._C._cpu
        return bool(cpu._is_avx512_bf16_supported() or cpu._is_amx_tile_supported())
    except Exception:
        return None


def own_model_dtype(wanted: str | None = None) -> str:
    """The precision Freewill 1.8B-V runs in. "auto" (the default): float32 when the processor has no bfloat16
    of its own and the memory holds it, bfloat16 otherwise (half the memory)."""
    wanted = (os.environ.get("FREEWILL_OWN_DTYPE") or wanted or "auto").strip().lower()
    if wanted in ("float32", "bfloat16"):
        return wanted
    from freewill.vlm.capacity import machine
    ram = machine().get("ram_gb") or 0
    if native_bfloat16() is True or ram < FLOAT32_RAM_GB:
        return "bfloat16"
    return "float32"
