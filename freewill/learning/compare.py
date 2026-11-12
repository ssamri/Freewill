"""Measuring what an adapter changes: the base model, the adapted model, and two controls.

Used by the nightly cycle (to check the converted adapter through llama.cpp,
the runtime the being converses with) and by the Research Lab (EXP-09).

The conditions compared, on the same held-out items of the life, item by item:

    base               the model as it was at birth, no adapter
    adapted            the adapter this life accepted and converses with
    control_shuffled   an adapter trained with the same settings and budget on the same
                       items, with the words of each item shuffled: same vocabulary,
                       no content. If it does as well as `adapted`, the gain is not
                       about what was lived.
    control_random     an adapter of the same rank whose change of weights has the same
                       size as the adapted one, in random directions: any change of that
                       size, without learning.

Losses are mean negative log-likelihood per token (nats). Lower is better.
The unit of the paired statistics is the held-out item.
"""

from __future__ import annotations

import json
import random
import re
import subprocess
import sys
import tempfile
from pathlib import Path

from freewill.learning.engine import EngineLearning, item_text, reference_items
from freewill.research.stats import paired


class CompareError(Exception):
    pass


# -- through llama.cpp -----------------------------------------------------------------------

_PPL = re.compile(r"Final estimate: PPL = ([0-9.]+)")


def runtime_loss(model_gguf: Path, text: str, adapter_gguf: Path | None = None, *, ctx: int = 128,
                 threads: int | None = None) -> dict:
    """Perplexity computed by llama.cpp's own llama-perplexity on `text`. llama.cpp scores the second
    half of each window of `ctx` tokens only; the figure is comparable between conditions, not with PyTorch's."""
    from freewill import runtime
    program = runtime.find("llama-perplexity")
    if program is None:
        raise CompareError("llama-perplexity is not part of the runtime on this computer")
    import os
    with tempfile.NamedTemporaryFile("w", suffix=".txt", delete=False, encoding="utf-8") as handle:
        handle.write(text)
        path = handle.name
    command = [str(program), "-m", str(model_gguf), "-f", path, "-c", str(ctx), "-b", str(ctx),
               "-t", str(threads or max(1, (os.cpu_count() or 2) - 1))]
    if adapter_gguf is not None:
        command += ["--lora", str(adapter_gguf)]
    flags = subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0
    try:
        done = subprocess.run(command, capture_output=True, text=True, timeout=3600, creationflags=flags,
                              cwd=str(program.parent))
    finally:
        os.unlink(path)
    log = (done.stdout or "") + (done.stderr or "")
    match = _PPL.search(log)
    if done.returncode != 0 or not match:
        raise CompareError("llama-perplexity failed: " + log[-600:].strip())
    import math
    ppl = float(match.group(1))
    loaded = adapter_gguf is None or bool(re.search(r"lora|adapter", log, re.IGNORECASE))  # see runtime_check
    return {"ppl": ppl, "nll": round(math.log(ppl), 6), "ctx": ctx, "adapter_loaded": loaded}


def runtime_check(model_gguf: Path):
    """The function the nightly cycle calls on a converted adapter, before making it the one in use."""
    def check(adapter_gguf: Path, texts: list[str]) -> dict:
        text = "\n\n".join(texts)
        error = None
        for ctx in (128, 64, 32):  # llama-perplexity needs at least two windows of text
            try:
                base = runtime_loss(model_gguf, text, ctx=ctx)
                adapted = runtime_loss(model_gguf, text, adapter_gguf, ctx=ctx)
                break
            except CompareError as failure:
                error = failure
        else:
            return {"ran": False, "reason": str(error)[:400]}
        difference = round(adapted["nll"] - base["nll"], 6)
        # Proof that llama.cpp applied the adapter: the log names it, or the loss it computes changed.
        # (b12306 does not always name it at the default log level; the change in loss is the stronger proof.)
        loaded = bool(adapted["adapter_loaded"]) or abs(difference) > 1e-6
        return {"ran": True, "base_nll": base["nll"], "adapted_nll": adapted["nll"], "difference": difference,
                "adapter_loaded": loaded, "adapter_named_in_log": adapted["adapter_loaded"], "ctx": ctx,
                "note": "llama.cpp perplexity on the held-out text; second half of each window"}
    return check


# -- the comparison ---------------------------------------------------------------------------

def _shuffled(item: dict, seed: int) -> dict:
    rng = random.Random(seed)
    if item.get("messages"):
        messages = []
        for m in item["messages"]:
            words = m["content"].split()
            rng.shuffle(words)
            messages.append({"role": m["role"], "content": " ".join(words)})
        return {"messages": messages}
    words = str(item.get("text") or "").split()
    rng.shuffle(words)
    return {"text": " ".join(words)}


def _random_like(bench, source: str, name: str, seed: int) -> None:
    """An adapter of the same rank as `source`, random, rescaled so its change of weights has the same total size."""
    import torch
    bench.copy(source, name)
    generator = torch.Generator().manual_seed(seed)
    with torch.no_grad():
        for key, value in bench.model.named_parameters():
            if f".{name}." in key and "lora_" in key:
                value.copy_(torch.randn(value.shape, generator=generator).to(value.dtype) * float(value.std() or 0.01))
    target = bench.delta_norms(source)["total_frobenius"]
    found = bench.delta_norms(name)["total_frobenius"]
    if found > 0:
        factor = (target / found) ** 0.5  # both A and B are scaled, so the product is scaled by the factor squared
        with torch.no_grad():
            for key, value in bench.model.named_parameters():
                if f".{name}." in key and "lora_" in key:
                    value.mul_(factor)


def compare(life_path: Path, model: dict, store, *, workbench=None, runtime_model: Path | None = None,
            behaviour_probe=None, seed: int = 0, purpose: str = "final test (EXP-09)", who: str = "") -> dict:
    """The final test: base, adapted and two controls on the life's sealed test episodes, and the capability
    tests under four conditions (with and without the being's memories). Reading the sealed test is logged."""
    from freewill.learning import capability_tests as caps
    from freewill.learning import corpus as lived
    learning = EngineLearning(life_path)
    active = learning.active(model["id"])
    if active is None:
        raise CompareError("this life converses with the base model alone: there is no adapter to compare")
    settings = learning.settings
    own = settings.learn_from_own_replies
    train_rows = [r for r in learning._split_rows("train") if lived.trainable(r, own_replies=own)]
    sealed = learning.open_test(purpose, who, active["version"])
    measurable = [r for r in sealed["units"] if lived.trainable(r, own_replies=own)]
    held, leaked = lived.without_leaks(measurable, train_rows)
    tests = sealed["tests"]
    if len(held) < 6 and not tests:
        raise CompareError(f"the sealed test needs at least 6 episodes' units or some vouched tests; this life has {len(held)}")
    if workbench is None:
        from freewill.learning.lora import Workbench
        workbench = Workbench(store.base_dir(model), seed=seed)
    bench = workbench
    held_seq = bench.tokens([EngineLearning.training_item(r) for r in held], settings.max_len)
    reference = reference_items()
    ref_seq = bench.tokens(reference, settings.max_len)
    manifest = json.loads((Path(active["folder"]) / "manifest.json").read_text(encoding="utf-8"))
    trained_until = manifest.get("trained_until") or manifest.get("created")
    later = [i for i, r in enumerate(held) if trained_until and str(r.get("collected") or "") > trained_until]

    bench.load("adapted", active["folder"])
    rank = bench.ranks["adapted"]["rank"]
    # Control 1: same settings, same training units, words shuffled; trained for as many steps as all nights together.
    nights = [r for r in learning.ledger() if r["kind"] == "night" and r.get("decision") == "accepted"]
    steps = sum(r["candidates"][r.get("chosen", "candidate")]["training"]["steps"] for r in nights) or settings.steps
    bench.delete("control_shuffled")
    bench.fresh("control_shuffled", rank, bench.ranks["adapted"]["alpha"], seed=seed)
    used = [r for r in train_rows if r["night"] is not None] or train_rows
    shuffled = bench.tokens([_shuffled(EngineLearning.training_item(r), seed + i) for i, r in enumerate(used)], settings.max_len)
    training = bench.train("control_shuffled", shuffled, steps=steps, lr=settings.lr, seed=seed)
    # Control 2: random directions, same size of change.
    bench.delete("control_random")
    _random_like(bench, "adapted", "control_random", seed)

    conditions = {"base": None, "adapted": "adapted", "control_shuffled": "control_shuffled", "control_random": "control_random"}
    per_item, reference_scores, sizes = {}, {}, {}
    from freewill.learning.lora import mean_nll
    for label, name in conditions.items():
        rows = bench.losses(name, held_seq) if held_seq else []
        per_item[label] = [round(r["nll"], 6) for r in rows]
        reference_scores[label] = mean_nll(bench.losses(name, ref_seq))
        sizes[label] = 0 if name is None else bench.delta_norms(name)["total_frobenius"]
    mean = lambda v: round(sum(v) / len(v), 6) if v else None  # noqa: E731
    table = {label: {"life_held_out_mean": mean(v), "reference_mean": reference_scores[label],
                     "later_mean": mean([v[i] for i in later]) if later else None,
                     "delta_frobenius": sizes[label], "n_items": len(v)} for label, v in per_item.items()}
    comparisons = []
    if len(held_seq) >= 6:
        for label in ("adapted", "control_shuffled", "control_random"):
            comparisons.append({"metric": "life_held_out_nll", "condition": label, "reference": "base",
                                **paired(per_item["base"], per_item[label])})
        for label in ("control_shuffled", "control_random"):
            comparisons.append({"metric": "life_held_out_nll", "condition": "adapted", "reference": label,
                                **paired(per_item[label], per_item["adapted"])})

    # Capabilities, under four conditions: memory alone, adapter alone, both; and the base and controls without memory.
    capability = None
    if tests:
        runs = {"base": (None, False), "memory_only": (None, True), "adapter_only": ("adapted", False),
                "adapter_and_memory": ("adapted", True), "control_shuffled": ("control_shuffled", False)}
        rows = {label: caps.measure(bench, name, tests, max_len=settings.max_len, life_path=life_path, with_memory=memory)
                for label, (name, memory) in runs.items()}
        margins = {label: [r["margin"] for r in found if r.get("measured")] for label, found in rows.items()}
        capability = {"tests": len(tests), "conditions": {label: caps.summary(found) for label, found in rows.items()},
                      "rows": rows, "consistency_across_nights": caps.consistency(learning.ledger()),
                      "comparisons": [{"metric": "capability_margin", "condition": a, "reference": b, **paired(margins[b], margins[a])}
                                      for a, b in (("adapter_only", "base"), ("adapter_and_memory", "memory_only"),
                                                   ("adapter_only", "control_shuffled"), ("memory_only", "base"))
                                      if len(margins[a]) == len(margins[b]) >= 2]}

    runtime = None
    if runtime_model is not None and held:
        runtime = runtime_check(runtime_model)(Path(active["gguf"]), [bench.render(EngineLearning.training_item(r)) for r in held])
    behaviour = behaviour_probe(sealed["units"]) if behaviour_probe else None
    for name in ("adapted", "control_shuffled", "control_random"):
        bench.delete(name)
    return {"version": active["version"], "adapter_sha256": manifest["adapter_sha256"], "gguf_sha256": active["sha256"],
            "base_model_id": model["id"], "conditions": table, "per_item": per_item, "comparisons": comparisons,
            "capabilities": capability, "units": "sealed test unit of the life", "control_training": training,
            "runtime_check": runtime, "behaviour": behaviour, "held_out_sha256": [r["sha256"] for r in held],
            "sealed_test": {"units": len(held), "leaked_set_aside": len(leaked), "collected_after_training": len(later),
                            "tests": len(tests), "readings": len(learning._rows("test_access.jsonl"))},
            "notes": ["losses are nats per token; lower predicts the sealed test text better",
                      "the sealed test was never read by any night: not to train, not to decide, not to grow",
                      "control_shuffled keeps the vocabulary of the lived units and destroys their content",
                      "control_random is a change of the same size as the adapted one, in random directions",
                      "a capability test passes when the right answer is more probable than the wrong one",
                      "a lower loss is not understanding; it says the model predicts this text better"]}


def behaviour_probe(engine, *, n_predict: int = 48):
    """Greedy answers of the conversing runtime to the held-out messages, with the adapter at scale 0 and 1,
    in one llama-server process: how often they differ, and how much each overlaps the reply the being
    really gave (word F1). A description of change, not a measure of quality."""
    def words(text):
        return [w for w in re.findall(r"\w+", text.lower())]

    def f1(a, b):
        a, b = words(a), words(b)
        if not a or not b:
            return 0.0
        common = sum(min(a.count(w), b.count(w)) for w in set(a))
        if not common:
            return 0.0
        p, r = common / len(a), common / len(b)
        return round(2 * p * r / (p + r), 4)

    def probe(held: list[dict]) -> dict:
        rows = []
        for item in held:
            if item.get("messages"):
                question, reply = item["messages"][0]["content"], item["messages"][-1]["content"]
            elif item.get("provenance") == "reply" and item.get("heard"):
                question, reply = item["heard"], item["text"]
            else:
                continue
            prompt = f"<|im_start|>user\n{question}<|im_end|>\n<|im_start|>assistant\n<think>\n\n</think>\n\n"
            base = engine.complete(prompt, n_predict=n_predict, lora_scale=0.0)
            adapted = engine.complete(prompt, n_predict=n_predict, lora_scale=1.0)
            rows.append({"differs": base.strip() != adapted.strip(), "f1_base": f1(base, reply),
                         "f1_adapted": f1(adapted, reply), "base": base[:300], "adapted": adapted[:300]})
        if not rows:
            return {"n": 0}
        return {"n": len(rows), "share_differs": round(sum(r["differs"] for r in rows) / len(rows), 4),
                "f1": paired([r["f1_base"] for r in rows], [r["f1_adapted"] for r in rows]), "rows": rows,
                "note": "word overlap with the reply the being gave; prompts in the Qwen chat format"}
    return probe


def item_preview(item: dict) -> str:
    return item_text(item)[:160]
