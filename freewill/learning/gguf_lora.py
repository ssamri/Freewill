"""Turn a LoRA adapter trained with PEFT into the GGUF adapter format that llama.cpp loads with --lora.

The layout follows llama.cpp's own convert_lora_to_gguf.py: one pair of
tensors per adapted matrix, named after the base tensor with `.lora_a` and
`.lora_b`, stored as trained (A is rank × inputs, B is outputs × rank), and
the scale given by `adapter.lora.alpha` divided by the rank. Only
architectures whose base tensors are stored without reordering are accepted
(Qwen2 and Qwen3): for Llama-family bases the converter permutes the query
and key matrices, and an adapter written without the same permutation would
be silently wrong.

Needs the `gguf` package (written by the llama.cpp project, MIT) and
`safetensors`; both come with the `lora` extra.
"""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

SUPPORTED = {"qwen3", "qwen2"}
_MODULES = {
    "self_attn.q_proj": "attn_q", "self_attn.k_proj": "attn_k", "self_attn.v_proj": "attn_v",
    "self_attn.o_proj": "attn_output", "mlp.gate_proj": "ffn_gate", "mlp.up_proj": "ffn_up",
    "mlp.down_proj": "ffn_down",
}
_NAME = re.compile(r"(?:^|\.)layers\.(\d+)\.(self_attn\.[qkvo]_proj|mlp\.(?:gate|up|down)_proj)\.lora_([AB])(?:\.[\w-]+)?\.weight$")


class GGUFError(Exception):
    pass


def sha256_file(path: Path) -> str:
    sha = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            sha.update(chunk)
    return sha.hexdigest()


def tensor_names(peft_names) -> dict[str, tuple[str, str]]:
    """PEFT tensor name -> (GGUF tensor name, 'a' or 'b'). Raises on anything it does not understand."""
    out = {}
    for name in peft_names:
        match = _NAME.search(name)
        if not match:
            raise GGUFError(f"an adapter tensor this converter does not know: {name}")
        layer, module, which = match.groups()
        out[name] = (f"blk.{int(layer)}.{_MODULES[module]}.weight.lora_{which.lower()}", which.lower())
    return out


def convert(adapter_dir: Path, out_path: Path, architecture: str) -> dict:
    """Write `out_path` from the PEFT adapter in `adapter_dir`. Returns what was written."""
    if architecture not in SUPPORTED:
        raise GGUFError(f"converting adapters for the {architecture!r} architecture is not supported")
    try:
        import gguf
        import numpy as np
        from safetensors.numpy import load_file
    except ImportError as error:
        raise GGUFError(f"missing library: {error.name}") from error
    adapter_dir = Path(adapter_dir)
    config = json.loads((adapter_dir / "adapter_config.json").read_text(encoding="utf-8"))
    if config.get("use_rslora") or config.get("use_dora"):
        raise GGUFError("rsLoRA and DoRA adapters are not converted")
    tensors = load_file(str(adapter_dir / "adapter_model.safetensors"))
    names = tensor_names(tensors)
    pairs: dict[str, dict] = {}
    for peft_name, (gguf_name, which) in names.items():
        pairs.setdefault(gguf_name.rsplit(".lora_", 1)[0], {})[which] = tensors[peft_name]
    rank = None
    for base, pair in pairs.items():
        if set(pair) != {"a", "b"}:
            raise GGUFError(f"{base}: one half of the pair is missing")
        a, b = pair["a"], pair["b"]
        if a.shape[0] != b.shape[1]:
            raise GGUFError(f"{base}: ranks of A {a.shape} and B {b.shape} differ")
        rank = rank or a.shape[0]
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    partial = out_path.with_name(out_path.name + ".part")
    writer = gguf.GGUFWriter(str(partial), architecture)
    writer.add_string("general.type", "adapter")
    writer.add_string("adapter.type", "lora")
    writer.add_float32("adapter.lora.alpha", float(config["lora_alpha"]))
    writer.add_string("general.name", "Freewill life adapter")
    for base in sorted(pairs, key=_order):
        for which in ("a", "b"):
            writer.add_tensor(f"{base}.lora_{which}", np.ascontiguousarray(pairs[base][which], dtype=np.float32))
    writer.write_header_to_file()
    writer.write_kv_data_to_file()
    writer.write_tensors_to_file()
    writer.close()
    partial.replace(out_path)
    found = check(out_path, architecture)
    return {"path": str(out_path), "sha256": sha256_file(out_path), "tensors": found["tensors"],
            "parameters": found["parameters"], "alpha": float(config["lora_alpha"]), "rank": int(rank or 0),
            "architecture": architecture}


def _order(name: str):
    layer = int(name.split(".")[1])
    return layer, name


def check(path: Path, architecture: str) -> dict:
    """Read a GGUF adapter back and verify what llama.cpp will check when loading it."""
    import gguf
    reader = gguf.GGUFReader(str(path))
    fields = {name: field for name, field in reader.fields.items()}

    def text(key):
        field = fields.get(key)
        return None if field is None else bytes(field.parts[field.data[0]]).decode("utf-8")

    if text("general.type") != "adapter" or text("adapter.type") != "lora":
        raise GGUFError("the file is not a LoRA adapter")
    if text("general.architecture") != architecture:
        raise GGUFError("the adapter was written for another architecture")
    shapes = {t.name: [int(x) for x in t.shape] for t in reader.tensors}
    for name, shape in shapes.items():
        if name.endswith(".lora_a"):
            other = shapes.get(name[:-1] + "b")
            # in GGUF order: A is [inputs, rank], B is [rank, outputs]
            if other is None or shape[1] != other[0]:
                raise GGUFError(f"{name}: no matching B, or ranks differ")
    return {"tensors": len(shapes), "parameters": int(sum(int(t.n_elements) for t in reader.tensors))}
