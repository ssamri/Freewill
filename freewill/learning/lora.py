"""H4: low-rank adapters (LoRA) trained beside a frozen base model, on the text of a life.

This is the route by which a large language model can be changed by what a
being lived: the base weights stay frozen and a small set of added weights is
trained. It works on a base model stored on this computer in the Transformers
format (a folder with `config.json` and weights). It does not work on the GGUF
files the embedded engine runs: those are for inference only.

State of this code, said plainly: it has been run end to end on a tiny base
model with random weights, to check that only adapter weights change, that the
training is judged on held-out text and that a rejected training leaves nothing
behind. It has never been run on a real language model, on a GPU, or with a
real tokenizer; and loading the resulting adapter into the embedded engine is
not written. Needs PyTorch, Transformers and PEFT.
"""

from __future__ import annotations

import hashlib
import json
import time
from pathlib import Path

BLOCK = 128
MIN_GAIN = 0.001
RULES_VERSION = "h4-lora-0.1"


class LoraError(Exception):
    pass


def _hash(tensors: list) -> str:
    sha = hashlib.sha256()
    for tensor in tensors:
        sha.update(tensor.detach().cpu().float().numpy().tobytes())
    return sha.hexdigest()


def _passages(ids: list[int], torch):
    size = BLOCK + 1
    rows = [ids[i:i + size] for i in range(0, len(ids) - size + 1, size)]
    if len(rows) < 10:
        raise LoraError("too little text to train on and to hold some out")
    data = torch.tensor(rows, dtype=torch.long)
    held = torch.arange(len(rows)) % 10 == 9  # one passage in ten is never trained on
    return data[~held], data[held]


def train(base_dir: Path, corpus: Path, out_dir: Path, *, approved_by_human: bool, steps: int = 100, rank: int = 8,
          seed: int = 0, encode=None) -> dict:
    """Train an adapter. Returns the manifest of what was really done. Nothing is kept if it does not help.

    `encode` turns text into token ids; by default the base model's own tokenizer is used.
    """
    if approved_by_human is not True:
        raise LoraError("a training needs the explicit approval of a person")
    try:
        import torch
        from peft import LoraConfig, get_peft_model
        from transformers import AutoModelForCausalLM
    except ImportError as error:
        raise LoraError(f"training libraries missing: {error.name}") from error
    base_dir, out_dir = Path(base_dir), Path(out_dir)
    if not (base_dir / "config.json").exists():
        raise LoraError("the base model must be a folder in the Transformers format; a GGUF file cannot be trained")
    if encode is None:
        from transformers import AutoTokenizer
        tokenizer = AutoTokenizer.from_pretrained(base_dir, local_files_only=True)
        encode = lambda text: tokenizer(text)["input_ids"]  # noqa: E731
    started = time.monotonic()
    torch.manual_seed(seed)
    base = AutoModelForCausalLM.from_pretrained(base_dir, local_files_only=True)
    frozen = list(base.parameters())  # the very tensors of the base: they are hashed again after training
    base_before = _hash(frozen)
    base_parameters = sum(p.numel() for p in base.parameters())
    train_set, held = _passages(encode(Path(corpus).read_text(encoding="utf-8")), torch)
    model = get_peft_model(base, LoraConfig(r=rank, lora_alpha=2 * rank, lora_dropout=0.0, task_type="CAUSAL_LM"))
    trainable = [p for p in model.parameters() if p.requires_grad]

    def loss_on(passages) -> float:
        model.eval()
        with torch.no_grad():
            return round(float(model(input_ids=passages, labels=passages).loss), 6)

    before = loss_on(held)
    optimiser = torch.optim.AdamW(trainable, lr=1e-3)
    model.train()
    for _ in range(int(steps)):
        batch = train_set[torch.randint(len(train_set), (min(8, len(train_set)),))]
        loss = model(input_ids=batch, labels=batch).loss
        optimiser.zero_grad()
        loss.backward()
        optimiser.step()
    after = loss_on(held)
    accepted = before - after >= MIN_GAIN
    base_after = _hash(frozen)
    manifest = {
        "rules": RULES_VERSION, "training_method": "lora", "decision": "accepted" if accepted else "rejected",
        "base_model": str(base_dir), "base_parameters": base_parameters, "base_weights_before": base_before,
        "base_weights_after": base_after, "base_weights_changed": base_before != base_after,
        "trainable_adapter_parameters": sum(p.numel() for p in trainable), "rank": rank, "steps": int(steps),
        "heldout_loss_before": before, "heldout_loss_after": after, "heldout_passages": int(len(held)),
        "seconds": round(time.monotonic() - started, 2), "device": "cpu", "approved_by_human": True,
        "adapter_sha256": None, "adapter_dir": None}
    if accepted:
        out_dir.mkdir(parents=True, exist_ok=True)
        model.save_pretrained(out_dir)
        manifest["adapter_sha256"] = _hash([p for n, p in sorted(model.named_parameters()) if "lora_" in n])
        manifest["adapter_dir"] = str(out_dir)
        (out_dir / "freewill_manifest.json").write_text(json.dumps(manifest, indent=1) + "\n", encoding="utf-8")
    return manifest
