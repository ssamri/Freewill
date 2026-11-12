"""H4: low-rank adapters (LoRA) trained beside a frozen base model, on what a life lived.

This is the route by which the model a being converses with can be changed by
its experiences: the base weights stay frozen, and a small set of added
weights is trained, evaluated, and either kept or thrown away
(freewill/learning/engine.py decides). The base must be stored in the
Transformers format (a folder with `config.json` and the weights): the GGUF
files that the embedded engine runs are for inference only. An accepted
adapter is converted to GGUF (gguf_lora.py) and loaded by llama.cpp.

The workbench loads the base once and holds several adapters on it at the
same time: the one in use, the candidate of the night, a grown candidate,
and controls. Every loss it reports is a mean negative log-likelihood per
token, on token sequences given to it; it never decides anything itself.

Needs PyTorch, Transformers and PEFT (the `lora` extra).
"""

from __future__ import annotations

import hashlib
import json
import math
import random
import time
from pathlib import Path

BLOCK = 128
MIN_GAIN = 0.001
RULES_VERSION = "h4-lora-0.2"
TARGETS = ("q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj")


class LoraError(Exception):
    pass


def _libraries():
    try:
        import torch
        from peft import LoraConfig, PeftModel, get_peft_model
        from transformers import AutoModelForCausalLM, AutoTokenizer
    except ImportError as error:
        raise LoraError(f"training libraries missing: {error.name}") from error
    return torch, LoraConfig, PeftModel, get_peft_model, AutoModelForCausalLM, AutoTokenizer


def _hash(tensors: list) -> str:
    sha = hashlib.sha256()
    for tensor in tensors:
        sha.update(tensor.detach().cpu().contiguous().view(-1).view(dtype=_byte_dtype()).numpy())
    return sha.hexdigest()


def _byte_dtype():
    import torch
    return torch.uint8


def device_name(torch) -> str:
    if torch.cuda.is_available():
        return "cuda"
    if getattr(torch.backends, "mps", None) is not None and torch.backends.mps.is_available():
        return "mps"
    return "cpu"


class Workbench:
    """One frozen base, several named adapters on it."""

    def __init__(self, base_dir: Path, *, device: str | None = None, encode=None, seed: int = 0) -> None:
        torch, _LoraConfig, _PeftModel, _get, AutoModelForCausalLM, AutoTokenizer = _libraries()
        self.torch = torch
        self.base_dir = Path(base_dir)
        if not (self.base_dir / "config.json").exists():
            raise LoraError("the base model must be a folder in the Transformers format; a GGUF file cannot be trained")
        self.device = device or device_name(torch)
        torch.manual_seed(seed)
        dtype = torch.float32 if self.device == "cpu" else torch.bfloat16
        self.dtype = str(dtype).replace("torch.", "")
        self.base = AutoModelForCausalLM.from_pretrained(self.base_dir, local_files_only=True, torch_dtype=dtype)
        self.base.to(self.device)
        self.base.requires_grad_(False)
        self.config = json.loads((self.base_dir / "config.json").read_text(encoding="utf-8"))
        self.tokenizer = None
        if encode is None:
            self.tokenizer = AutoTokenizer.from_pretrained(self.base_dir, local_files_only=True)
            encode = lambda text: self.tokenizer(text, add_special_tokens=False)["input_ids"]  # noqa: E731
        self.encode = encode
        self.base_parameters = sum(p.numel() for p in self.base.parameters())
        self._frozen = list(self.base.parameters())
        self.model = None  # the PEFT wrapper, made with the first adapter
        self.ranks: dict[str, dict] = {}

    # -- text --------------------------------------------------------------------------

    def render(self, item: dict) -> str:
        """An item of a corpus as the model sees it: a conversation in the model's own chat format, or text."""
        if item.get("messages"):
            if self.tokenizer is not None and getattr(self.tokenizer, "chat_template", None):
                try:
                    return self.tokenizer.apply_chat_template(item["messages"], tokenize=False, enable_thinking=False)
                except TypeError:
                    return self.tokenizer.apply_chat_template(item["messages"], tokenize=False)
            return "\n".join(f"{m['role']}: {m['content']}" for m in item["messages"]) + "\n"
        return str(item.get("text") or "")

    def tokens(self, items: list[dict], max_len: int = 256) -> list[list[int]]:
        """Token ids of each item. For a conversation in the model's chat format, only the words of the
        messages count in the loss (training and measures alike): the tokens of the format itself
        (<|im_start|>, roles, an empty <think></think>) are predicted but not scored. Without this, an
        adapter "gains" mostly by learning the format, which says nothing about what a life lived."""
        out = []
        for item in items:
            rendered = self.render(item)
            seq = self._masked(item, rendered)
            if seq is None:
                seq = Seq(self.encode(rendered))
            seq = seq.cut(max_len)
            if len(seq) >= 2 and seq.scored() >= 1:
                out.append(seq)
        return out

    def _masked(self, item: dict, rendered: str):
        if not item.get("messages") or self.tokenizer is None or not getattr(self.tokenizer, "is_fast", False):
            return None
        spans, start = [], 0
        for message in item["messages"]:
            content = str(message.get("content") or "")
            at = rendered.find(content, start) if content else -1
            if at < 0:
                return None  # the template changed the text: score everything rather than guess
            if message.get("scored", True):  # a question asked of the model is context, not a target
                spans.append((at, at + len(content)))
            start = at + len(content)
        encoded = self.tokenizer(rendered, add_special_tokens=False, return_offsets_mapping=True)
        ids, offsets = encoded["input_ids"], encoded["offset_mapping"]
        keep = [any(a < e and b > s for s, e in spans) for a, b in offsets]
        return Seq(ids, [i if k else -100 for i, k in zip(ids, keep)])

    def base_hash(self) -> str:
        return _hash(self._frozen)

    # -- adapters ------------------------------------------------------------------------

    def _lora_config(self, rank: int, alpha: float):
        _t, LoraConfig, *_rest = _libraries()
        present = {name.rsplit(".", 1)[-1] for name, _m in self.base.named_modules()}
        targets = [t for t in TARGETS if t in present] or None  # None: PEFT's own choice for other architectures
        return LoraConfig(r=int(rank), lora_alpha=float(alpha), lora_dropout=0.0, bias="none",
                          target_modules=targets, task_type="CAUSAL_LM")

    def fresh(self, name: str, rank: int, alpha: float | None = None, seed: int = 0) -> None:
        """A new adapter: A drawn at random, B at zero, so that at birth it changes nothing."""
        _t, _c, _p, get_peft_model, *_r = _libraries()
        self.torch.manual_seed(seed)
        config = self._lora_config(rank, alpha or 2 * rank)
        if self.model is None:
            self.model = get_peft_model(self.base, config, adapter_name=name)
        else:
            self.model.add_adapter(name, config)
        self.ranks[name] = {"rank": int(rank), "alpha": float(alpha or 2 * rank)}

    def load(self, name: str, folder: Path) -> None:
        _t, _c, PeftModel, *_r = _libraries()
        folder = Path(folder)
        config = json.loads((folder / "adapter_config.json").read_text(encoding="utf-8"))
        if self.model is None:
            self.model = PeftModel.from_pretrained(self.base, folder, adapter_name=name, is_trainable=True)
        else:
            self.model.load_adapter(folder, adapter_name=name, is_trainable=True)
        self.ranks[name] = {"rank": int(config["r"]), "alpha": float(config["lora_alpha"])}

    def copy(self, source: str, name: str, *, rank: int | None = None) -> None:
        """A copy of an adapter, possibly with a larger rank. Growth preserves the function exactly:
        the old A and B are copied into the first rows and columns, the new rows of A are drawn at
        random and the new columns of B are zero, and alpha grows with the rank so the scale is unchanged."""
        old = self.ranks[source]
        rank = int(rank or old["rank"])
        if rank < old["rank"]:
            raise LoraError("an adapter is never shrunk here")
        self.fresh(name, rank, old["alpha"] * rank / old["rank"])
        params = dict(self.model.named_parameters())
        with self.torch.no_grad():
            for key, value in params.items():
                if f".lora_A.{name}." in key:
                    src = params[key.replace(f".lora_A.{name}.", f".lora_A.{source}.")]
                    value[: src.shape[0]].copy_(src)
                elif f".lora_B.{name}." in key:
                    src = params[key.replace(f".lora_B.{name}.", f".lora_B.{source}.")]
                    value.zero_()
                    value[:, : src.shape[1]].copy_(src)

    def delete(self, name: str) -> None:
        if self.model is not None and name in self.ranks:
            self.model.delete_adapter(name)
            self.ranks.pop(name)

    def parameters(self, name: str) -> int:
        return sum(p.numel() for key, p in self.model.named_parameters() if f".{name}." in key and "lora_" in key)

    def adapter_hash(self, name: str) -> str:
        return _hash([p for key, p in sorted(self.model.named_parameters()) if f".{name}." in key and "lora_" in key])

    def delta_norms(self, name: str) -> dict:
        """How much each adapted matrix of the base is changed: the Frobenius norm of scale·B·A, computed
        without forming it. This is the record of each change of weights, layer by layer."""
        scale = self.ranks[name]["alpha"] / self.ranks[name]["rank"]
        params = dict(self.model.named_parameters())
        rows, total = [], 0.0
        with self.torch.no_grad():
            for key, a in sorted(params.items()):
                if f".lora_A.{name}." not in key:
                    continue
                b = params[key.replace(".lora_A.", ".lora_B.")]
                a64, b64 = a.double().cpu(), b.double().cpu()
                value = float(scale * self.torch.sqrt(self.torch.clamp(
                    self.torch.trace((a64 @ a64.T) @ (b64.T @ b64)), min=0)))
                module = key.split(".lora_A.")[0].split("model.", 1)[-1]
                rows.append({"module": module, "frobenius": round(value, 8)})
                total += value * value
        return {"modules": rows, "total_frobenius": round(math.sqrt(total), 8), "scale": scale}

    def save(self, name: str, folder: Path) -> None:
        folder = Path(folder)
        folder.mkdir(parents=True, exist_ok=True)
        self.model.save_pretrained(folder, selected_adapters=[name])
        nested = folder / name  # PEFT writes non-default adapters into a subfolder
        if nested.is_dir():
            for path in nested.iterdir():
                path.replace(folder / path.name)
            nested.rmdir()

    # -- training and measuring ------------------------------------------------------------

    def _use(self, name: str | None):
        if name is None:
            return self.model.disable_adapter() if self.model is not None else _Null()
        self.model.set_adapter(name)
        return _Null()

    def losses(self, name: str | None, sequences: list[list[int]]) -> list[dict]:
        """Mean negative log-likelihood per token of each sequence, under adapter `name` (None: the base alone)."""
        torch = self.torch
        model = self.model if self.model is not None else self.base
        model.eval()
        out = []
        with torch.no_grad(), self._use(name):
            for ids in sequences:
                tensor = torch.tensor([ids], dtype=torch.long, device=self.device)
                labels = torch.tensor([_labels(ids)], dtype=torch.long, device=self.device)
                loss = model(input_ids=tensor, labels=labels).loss
                out.append({"nll": float(loss), "tokens": _scored(ids)})
        return out

    def train(self, name: str, sequences: list[list[int]], *, steps: int, lr: float = 3e-4, seed: int = 0,
              accumulate: int = 2, cancel=None) -> dict:
        torch = self.torch
        if not sequences:
            raise LoraError("nothing to train on")
        self.model.set_adapter(name)
        trainable = []
        for key, p in self.model.named_parameters():
            mine = "lora_" in key and f".{name}." in key
            p.requires_grad_(mine)
            if mine:
                trainable.append(p)
        optimiser = torch.optim.AdamW(trainable, lr=lr, weight_decay=0.0)
        rng = random.Random(seed)
        self.model.train()
        started, losses = time.monotonic(), []
        for step in range(int(steps)):
            if cancel is not None and cancel.is_set():
                raise LoraError("cancelled")
            optimiser.zero_grad()
            total = 0.0
            for _ in range(accumulate):
                ids = sequences[rng.randrange(len(sequences))]
                tensor = torch.tensor([ids], dtype=torch.long, device=self.device)
                labels = torch.tensor([_labels(ids)], dtype=torch.long, device=self.device)
                loss = self.model(input_ids=tensor, labels=labels).loss / accumulate
                loss.backward()
                total += float(loss.detach())
            optimiser.step()
            losses.append(round(total, 6))
        for p in trainable:
            p.requires_grad_(False)
        self.model.eval()
        return {"steps": int(steps), "train_loss_first": losses[0] if losses else None,
                "train_loss_last": losses[-1] if losses else None,
                "seconds": round(time.monotonic() - started, 2), "lr": lr, "accumulate": accumulate}


class Seq(list):
    """Token ids, with the labels to score (-100: predicted but not scored). No labels: all are scored."""

    def __init__(self, ids, labels=None) -> None:
        super().__init__(ids)
        self.labels = list(labels) if labels is not None else None

    def cut(self, n: int) -> "Seq":
        return Seq(self[:n], self.labels[:n] if self.labels is not None else None)

    def scored(self) -> int:
        return _scored(self)


def _labels(ids) -> list[int]:
    labels = getattr(ids, "labels", None)
    return list(ids) if labels is None else labels


def _scored(ids) -> int:
    """Tokens that count in the loss: every one after the first that has a label."""
    return sum(1 for label in _labels(ids)[1:] if label != -100)


class _Null:
    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False


def mean_nll(rows: list[dict]) -> float | None:
    """Mean per token, over all tokens of all sequences."""
    tokens = sum(r["tokens"] for r in rows)
    return None if not tokens else round(sum(r["nll"] * r["tokens"] for r in rows) / tokens, 6)


# -- the earlier, single-shot entry point (kept for the toy-model test and the lab) ------------------------

def _passages(ids: list[int], torch):
    size = BLOCK + 1
    rows = [ids[i:i + size] for i in range(0, len(ids) - size + 1, size)]
    if len(rows) < 10:
        raise LoraError("too little text to train on and to hold some out")
    held = [i % 10 == 9 for i in range(len(rows))]  # one passage in ten is never trained on
    return [r for r, h in zip(rows, held) if not h], [r for r, h in zip(rows, held) if h]


def train(base_dir: Path, corpus: Path, out_dir: Path, *, approved_by_human: bool, steps: int = 100, rank: int = 8,
          seed: int = 0, encode=None) -> dict:
    """Train one adapter on a text file. Returns the manifest of what was really done. Nothing is kept if it does not help."""
    if approved_by_human is not True:
        raise LoraError("a training needs the explicit approval of a person")
    torch = _libraries()[0]
    started = time.monotonic()
    bench = Workbench(base_dir, encode=encode, seed=seed, device="cpu")
    train_set, held = _passages(list(bench.encode(Path(corpus).read_text(encoding="utf-8"))), torch)
    base_before = bench.base_hash()
    bench.fresh("candidate", rank, seed=seed)
    before = mean_nll(bench.losses("candidate", held))
    bench.train("candidate", train_set, steps=steps, lr=1e-3, seed=seed, accumulate=1)
    after = mean_nll(bench.losses("candidate", held))
    accepted = before - after >= MIN_GAIN
    base_after = bench.base_hash()
    manifest = {
        "rules": RULES_VERSION, "training_method": "lora", "decision": "accepted" if accepted else "rejected",
        "base_model": str(base_dir), "base_parameters": bench.base_parameters, "base_weights_before": base_before,
        "base_weights_after": base_after, "base_weights_changed": base_before != base_after,
        "trainable_adapter_parameters": bench.parameters("candidate"), "rank": rank, "steps": int(steps),
        "heldout_loss_before": before, "heldout_loss_after": after, "heldout_passages": len(held),
        "seconds": round(time.monotonic() - started, 2), "device": bench.device, "approved_by_human": True,
        "adapter_sha256": None, "adapter_dir": None}
    if accepted:
        out_dir = Path(out_dir)
        bench.save("candidate", out_dir)
        manifest["adapter_sha256"] = bench.adapter_hash("candidate")
        manifest["adapter_dir"] = str(out_dir)
        (out_dir / "freewill_manifest.json").write_text(json.dumps(manifest, indent=1) + "\n", encoding="utf-8")
    return manifest
