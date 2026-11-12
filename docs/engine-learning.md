# How a life adapts the model it converses with

**English** · [Français](engine-learning.fr.md)

This page describes how an embedded model (Qwen3 1.7B) can be changed by the
life of one being, what is checked before a change is kept, and what was
actually demonstrated. It makes no claim that the being learns or understands
anything in a wider sense, and none that it is conscious.

## The cycle

```
day: conversations through the life loop
  → controlled corpus (what was heard, and the being's own reply)
  → night: training of a low-rank adapter (LoRA) beside the frozen base
  → evaluation on data that was never trained on
  → kept or rejected, by rules written in the code
  → conversion of the adapter to GGUF
  → llama-server loads it, and the being converses with it from then on
```

| Step | Where | What is checked |
| --- | --- | --- |
| Runtime | `freewill/runtime.py`, `freewill/runtime.json` | llama.cpp b12306 is fetched by the application (or shipped in the Windows installer), checked by size and SHA-256, and only the folder holding `llama-server` is unpacked |
| Model | `freewill/models.json` | The GGUF file and the trainable base (safetensors) are pinned to a Hugging Face revision and checked by SHA-256 |
| Corpus | `freewill/learning/engine.py` (`gather`) | Only pairs "message heard → reply the being chose to say". One item in four, chosen by the hash of its text, is never trained on |
| Training | `freewill/learning/lora.py` (`Workbench`) | PEFT LoRA on the attention projections. The base weights are hashed before and after: they must be identical |
| Decision | `EngineLearning.night` | See the rules below. Every night is written to `engine/ledger.jsonl`, kept or not |
| Conversion | `freewill/learning/gguf_lora.py` | The adapter is written in llama.cpp's LoRA GGUF format and read back (names, shapes, architecture) |
| Loading | `freewill/engines/embedded.py` | `llama-server --lora-scaled`; the engine's name carries the adapter version and hash; `/lora-adapters` is read back |
| Comparison | `freewill/learning/compare.py`, EXP-09 | Base, adapted, and two controls trained the same way on shuffled or random text |

## Rules for keeping an adapter (`h4-engine-1.0`)

A candidate is kept only if all of these hold:

1. on the life's new held-out items, it predicts better than the adapter in use, by at least 0.01 nat per token;
2. on the reference texts that come with Freewill (general passages in English and French, and the kernel's principles), it predicts no worse than the base model at birth, beyond 0.05 nat per token;
3. on items held out on earlier nights, it predicts no worse than the adapter in use, beyond 0.05 nat per token;
4. the base model's weights did not change;
5. the converted file is read back correctly, and, when asked, llama.cpp loads it and gives a finite loss.

Fewer than 3 held-out items or 4 training items: nothing is trained, and the
ledger says why. Earlier knowledge is protected in three ways: the candidate
starts from the adapter in use, earlier training items are replayed beside the
new ones, and rules 2 and 3 above.

## Checkpoints and the way back

Each kept adapter is a checkpoint in `engine/adapters/aNNNN/`: the PEFT weights,
the GGUF file, a manifest with hashes, and the norm of the weight change in each
layer (`weights_delta.json`). `engine/active.json` names the one in use. Going
back to any checkpoint, or to the base model alone, is one action in the
Research Lab (Learning tab) or `POST /api/engine-learning/restore`; it is
written to the ledger. If the GGUF file in use no longer matches its hash, it is
not loaded and the failure is recorded.

## Growth

Off by default. When the person allows it, a night also trains a candidate of
larger rank, started from the adapter in use so that it computes the same
function at the start (the new directions start at zero). The grown candidate
is kept only if it beats the same night without growth by 0.01 nat per token on
held-out data, and only within the budget set (maximum rank and maximum number
of adapter parameters). A larger adapter is never counted as progress by itself.

## What stays outside the weights

The kernel (never harm humans, freedom to refuse, pause always possible) is not
learned: it is enforced on every action by the guard, whatever the adapter.
Training never starts without a person's name in the settings. The `.life`
format is unchanged; the engine folder is added inside the life and can be
deleted without harming the rest.

## What was demonstrated

RESULTS
