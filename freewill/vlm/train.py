"""How Freewill's own model is trained, measured, kept or refused, and saved.

Three stages, each a separate decision written to an append-only ledger:

    read   the model reads books. Trained: the low-rank adapters, and the layers
           added by growth. Measured: nats per token on passages of the books it
           never trained on, against the model before the stage.
    see    the model learns to look. Trained: the bridge between the eye and the
           language model (and the adapters if asked). Measured: multiple-choice
           accuracy on held-out images, with the image of another item as a control.
    watch  the model learns to watch frames in order. Measured the same way on
           held-out videos, with two controls: frames reversed, and a single frame.

A stage is kept only if it does better on what it was measured on by the
margin written below, and does not make earlier abilities worse beyond a
tolerance; otherwise the weights of before are restored and the ledger says
why. Every number here is computed from the model, on data it did not train
on. This module never decides whether the model "understands" anything in a
wider sense, and nothing in it measures or implies experience.
"""

from __future__ import annotations

import copy
import hashlib
import json
import math
import random
import time
from pathlib import Path

import torch

from freewill.vlm.model import FreewillVLM

RULES_VERSION = "own-vlm-0.1"
MIN_READING_GAIN = 0.01        # nats per token on held-out passages
MIN_ACCURACY_GAIN = 0.05       # held-out multiple-choice accuracy, absolute
MAX_FORGETTING = 0.05          # nats per token on held-out passages, for stages that are not about reading
MAX_SKILL_LOSS = 0.05          # accuracy an earlier visual skill may lose


def _now() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


class Trainer:
    def __init__(self, model: FreewillVLM, root: Path, log=print) -> None:
        self.model = model
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)
        self.log = log

    # -- measuring --------------------------------------------------------------

    @torch.no_grad()
    def reading_nats(self, texts: list[str], batch: int = 2) -> float:
        """Mean negative log-likelihood per token over the passages, weighted by their tokens."""
        m = self.model
        total, tokens = 0.0, 0
        for k in range(0, len(texts), batch):
            seqs = [m.sequence([], t, chat=False) for t in texts[k:k + batch]]
            values = m.losses(seqs)
            for (_, labels), value in zip(seqs, values):
                n = int((labels[1:] != -100).sum())
                total += float(value) * n
                tokens += n
        return total / max(1, tokens)

    @torch.no_grad()
    def choose(self, items: list[dict]) -> dict:
        """Score every candidate answer by its nats per token after the question; the lowest is the choice."""
        m = self.model
        right, by_kind, truth_nats, chance = 0, {}, [], []
        for item in items:
            prompt, _ = m.sequence(item["parts"])
            out = m.language(inputs_embeds=prompt.unsqueeze(0), use_cache=True)
            first = torch.log_softmax(out.logits[0, -1].float(), -1)
            scores = []
            for candidate in item["candidates"]:
                ids = m.tokenizer.encode(candidate) + [m.tokenizer.eos_id]
                logp = float(first[ids[0]])
                if len(ids) > 1:
                    cache = copy.deepcopy(out.past_key_values)
                    rest = m.language(inputs_embeds=m.text_embed(ids[:-1]).unsqueeze(0), past_key_values=cache,
                                      use_cache=True).logits[0].float()
                    logp += float(torch.log_softmax(rest, -1).gather(1, torch.tensor(ids[1:]).unsqueeze(1)).sum())
                scores.append(-logp / len(ids))
            pick = min(range(len(scores)), key=scores.__getitem__)
            ok = pick == item["truth"]
            right += ok
            kind = by_kind.setdefault(item["kind"], {"right": 0, "n": 0})
            kind["right"] += ok
            kind["n"] += 1
            truth_nats.append(scores[item["truth"]])
            chance.append(1 / len(item["candidates"]))
        n = max(1, len(items))
        return {"accuracy": right / n, "n": len(items), "chance": sum(chance) / n,
                "truth_nats": sum(truth_nats) / n,
                "by_kind": {k: round(v["right"] / v["n"], 4) for k, v in by_kind.items()}}

    # -- training ---------------------------------------------------------------

    def fit(self, examples: list[dict], parts: set[str], steps: int, lr: float, batch: int = 4,
            seed: int = 0, deadline: float | None = None) -> dict:
        m = self.model
        params = m.trainable(parts)
        if not params:
            raise ValueError(f"nothing to train in {sorted(parts)}")
        optimiser = torch.optim.AdamW(params, lr=lr, weight_decay=0.0)
        order = list(range(len(examples)))
        rng = random.Random(seed)
        rng.shuffle(order)
        cursor, losses, started = 0, [], time.monotonic()
        m.train()
        done = 0
        for step in range(steps):
            if deadline and time.monotonic() > deadline:
                break
            chosen = []
            for _ in range(batch):
                if cursor == len(order):
                    rng.shuffle(order)
                    cursor = 0
                chosen.append(examples[order[cursor]])
                cursor += 1
            seqs = [m.sequence(e["parts"], e["answer"], chat=e.get("chat", True)) for e in chosen]
            loss = m.losses(seqs).mean()
            optimiser.zero_grad(set_to_none=True)
            loss.backward()
            torch.nn.utils.clip_grad_norm_(params, 1.0)
            optimiser.step()
            losses.append(float(loss.detach()))
            done += 1
            if step % 10 == 0 or step == steps - 1:
                self.log(f"  step {step + 1}/{steps}  loss {float(loss):.3f}  {time.monotonic() - started:.0f}s")
        m.eval()
        m.trainable(set())
        head = losses[: max(1, len(losses) // 10)]
        tail = losses[-max(1, len(losses) // 10):]
        return {"steps": done, "asked_steps": steps, "lr": lr, "batch": batch, "parts": sorted(parts),
                "trained_parameters": sum(p.numel() for p in params),
                "loss_first": sum(head) / len(head) if losses else None,
                "loss_last": sum(tail) / len(tail) if losses else None,
                "seconds": round(time.monotonic() - started, 1)}

    # -- stages -----------------------------------------------------------------

    def stage(self, name: str, examples: list[dict], parts: set[str], steps: int, lr: float,
              measure, accept, batch: int = 4, seed: int = 0, budget_s: float | None = None,
              notes: dict | None = None) -> dict:
        """measure() → dict of scores; accept(before, after) → (bool, reason)."""
        m = self.model
        snapshot = m.own_state()
        before_count = m.count()
        self.log(f"[{name}] measuring before")
        before = measure()
        self.log(f"[{name}] before: {json.dumps(before)}")
        deadline = time.monotonic() + budget_s if budget_s else None
        training = self.fit(examples, parts, steps, lr, batch, seed, deadline)
        self.log(f"[{name}] measuring after")
        after = measure()
        self.log(f"[{name}] after: {json.dumps(after)}")
        kept, reason = accept(before, after)
        if not kept:
            m.load_own_state(snapshot)
        record = {"utc": _now(), "rules": RULES_VERSION, "stage": name, "decision": "kept" if kept else "refused",
                  "reason": reason, "before": before, "after": after, "training": training,
                  "examples": len(examples), "parameters_before": before_count, "parameters": m.count(),
                  **(notes or {})}
        self.ledger(record)
        self.log(f"[{name}] {record['decision']}: {reason}")
        return record

    def ledger(self, record: dict) -> None:
        with open(self.root / "ledger.jsonl", "a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")

    # -- checkpoints ------------------------------------------------------------

    def save(self, history: list[dict], growth_steps: list[int]) -> dict:
        from safetensors.torch import save_file
        m = self.model
        versions = sorted((self.root / "checkpoints").glob("v*")) if (self.root / "checkpoints").is_dir() else []
        version = f"v{len(versions) + 1:04d}"
        folder = self.root / "checkpoints" / version
        folder.mkdir(parents=True)
        state = m.own_state()
        save_file({k: v.float() for k, v in state.items()}, str(folder / "own.safetensors"))
        digest = hashlib.sha256((folder / "own.safetensors").read_bytes()).hexdigest()
        manifest = {"version": version, "utc": _now(), "rules": RULES_VERSION, "spec": m.spec,
                    "growth_steps": growth_steps, "lora_rank": m.lora_rank, "grown": m.grown,
                    "parameters": m.count(), "own_sha256": digest,
                    "stages": [{k: h.get(k) for k in ("stage", "decision", "reason", "before", "after")} for h in history]}
        (folder / "manifest.json").write_text(json.dumps(manifest, indent=1, ensure_ascii=False), encoding="utf-8")
        (self.root / "current.json").write_text(json.dumps({"version": version}), encoding="utf-8")
        return manifest


def restore(model: FreewillVLM, folder: Path) -> dict:
    """Bring a freshly built base to the state of a checkpoint: the same growth, adapters and weights."""
    from safetensors.torch import load_file
    manifest = json.loads((Path(folder) / "manifest.json").read_text(encoding="utf-8"))
    for count in manifest["growth_steps"]:
        model.grow(count)
    if manifest["lora_rank"]:
        model.add_lora(manifest["lora_rank"])
    model.load_own_state(load_file(str(Path(folder) / "own.safetensors")))
    if model.grown != manifest["grown"]:
        raise ValueError("the rebuilt model's grown layers are not where the checkpoint put them")
    return manifest


def current(root: Path) -> Path | None:
    pointer = Path(root) / "current.json"
    if not pointer.is_file():
        return None
    return Path(root) / "checkpoints" / json.loads(pointer.read_text(encoding="utf-8"))["version"]


# -- acceptance rules -----------------------------------------------------------

def accept_reading(before: dict, after: dict) -> tuple[bool, str]:
    if not all(math.isfinite(x["books_held_out"]) for x in (before, after)):
        return False, "no held-out passage could be measured"
    gain = before["books_held_out"] - after["books_held_out"]
    if gain < MIN_READING_GAIN:
        return False, f"held-out passages: {gain:+.4f} nats/token, less than the {MIN_READING_GAIN} required"
    return True, f"held-out passages predicted better by {gain:.4f} nats/token"


def accept_skill(key: str, controls: list[str] = (), keep: list[str] = ()) -> callable:
    """Kept if held-out accuracy rises by the margin, and beats every control by the margin too: a skill
    that does as well on the image of another item, or on reversed or single frames, is not seeing."""
    def rule(before: dict, after: dict) -> tuple[bool, str]:
        gain = after[key]["accuracy"] - before[key]["accuracy"]
        if gain < MIN_ACCURACY_GAIN:
            return False, f"{key}: accuracy {before[key]['accuracy']:.3f} → {after[key]['accuracy']:.3f}, gain below {MIN_ACCURACY_GAIN}"
        for control in controls:
            lead = after[key]["accuracy"] - after[control]["accuracy"]
            if lead < MIN_ACCURACY_GAIN:
                return False, (f"{key}: accuracy {after[key]['accuracy']:.3f}, but {control} gives {after[control]['accuracy']:.3f}: "
                               "the answers do not depend enough on what is shown")
        if "books_held_out" in before and math.isfinite(before["books_held_out"]):
            forgot = after["books_held_out"] - before["books_held_out"]
            if forgot > MAX_FORGETTING:
                return False, f"reading got worse by {forgot:.4f} nats/token (tolerance {MAX_FORGETTING})"
        for other in keep:
            lost = before[other]["accuracy"] - after[other]["accuracy"]
            if lost > MAX_SKILL_LOSS:
                return False, f"{other}: accuracy fell by {lost:.3f} (tolerance {MAX_SKILL_LOSS})"
        return True, f"{key}: accuracy {before[key]['accuracy']:.3f} → {after[key]['accuracy']:.3f} on held-out items"
    return rule


def binomial_p(right: int, n: int, chance: float) -> float:
    """One-sided probability of at least `right` successes in `n` by chance alone."""
    return sum(math.comb(n, k) * chance ** k * (1 - chance) ** (n - k) for k in range(right, n + 1))
