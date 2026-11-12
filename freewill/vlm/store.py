"""Where Freewill's own model lives on this computer, and how its two open bases are fetched.

    <data>/own-model/
        bases/language/   Qwen3 1.7B in the Transformers format, at the pinned revision
        bases/vision/     SigLIP2 base (only the vision tower is used)
        bases.json        what was fetched: repositories, revisions resolved, files and their SHA-256
        checkpoints/vNNNN/  what Freewill trained or added (own.safetensors) and its manifest
        current.json      the checkpoint in use
        ledger.jsonl      every stage, kept or refused, with its measurements
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from freewill.vlm.model import load_spec

PATTERNS = ["*.json", "*.safetensors", "*.txt", "*.model", "LICENSE*"]


def home() -> Path:
    from freewill.paths import data_dir
    return data_dir() / "own-model"


def bases_ready(root: Path) -> bool:
    return (root / "bases" / "language" / "config.json").is_file() and (root / "bases" / "vision" / "config.json").is_file()


def fetch_bases(root: Path, spec: dict | None = None, log=print) -> dict:
    """Download both bases once (several gigabytes) and write bases.json. Network: huggingface.co only."""
    from huggingface_hub import HfApi, snapshot_download
    spec = spec or load_spec()
    record = {}
    for part in ("language", "vision"):
        repo, revision = spec[part]["repo"], spec[part]["revision"]
        resolved = HfApi().model_info(repo, revision=revision).sha
        target = root / "bases" / part
        log(f"fetching {repo}@{resolved}")
        snapshot_download(repo, revision=resolved, local_dir=str(target), allow_patterns=PATTERNS)
        files = {}
        for path in sorted(target.rglob("*")):
            if path.is_file() and ".cache" not in path.parts:
                digest = hashlib.sha256()
                with open(path, "rb") as f:
                    for block in iter(lambda: f.read(1 << 20), b""):
                        digest.update(block)
                files[str(path.relative_to(target))] = {"size": path.stat().st_size, "sha256": digest.hexdigest()}
        record[part] = {"repo": repo, "revision_asked": revision, "revision": resolved,
                        "licence": spec[part]["licence"], "files": files}
        if revision and resolved != revision:
            raise RuntimeError(f"{repo}: asked for {revision}, got {resolved}")
    (root / "bases.json").write_text(json.dumps(record, indent=1), encoding="utf-8")
    return record


def load(root: Path | None = None, dtype: str = "float32"):
    """The model as it is now: the bases, then the checkpoint in use (growth, adapters, trained weights)."""
    from freewill.vlm.model import build
    from freewill.vlm.train import current, restore
    root = Path(root or home())
    if not bases_ready(root):
        raise FileNotFoundError(f"the bases of Freewill's own model are not in {root / 'bases'} yet")
    from freewill.vlm import capacity
    model = build(root / "bases", dtype=dtype)
    model.spec["ceiling_parameters"] = capacity.load_settings(root)["max_parameters"]  # the person's choice
    folder = current(root)
    manifest = restore(model, folder) if folder else None
    return model, manifest
