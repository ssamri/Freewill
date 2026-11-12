# How a life adapts the model it converses with

**English** · [Français](engine-learning.fr.md)

This page describes how an embedded model (Qwen3 1.7B) can be changed by the
life of one being, what is checked before a change is kept, and what was
actually demonstrated. It makes no claim that the being learns or understands
anything in a wider sense, and none that it is conscious.

## The cycle

```
day: conversations through the life loop
  → corpus kept by provenance (heard, read, vouched for, the being's own reply)
  → split by episode: train / validation / sealed test
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
| Corpus | `freewill/learning/corpus.py` | Every unit says where it comes from. Units are split by episode, never one by one; see below |
| Training | `freewill/learning/lora.py` (`Workbench`) | PEFT LoRA on the attention projections. The base weights are hashed before and after: they must be identical |
| Decision | `EngineLearning.night` | See the rules below. Every night is written to `engine/ledger.jsonl`, kept or not |
| Conversion | `freewill/learning/gguf_lora.py` | The adapter is written in llama.cpp's LoRA GGUF format and read back (names, shapes, architecture) |
| Loading | `freewill/engines/embedded.py` | `llama-server --lora`; the engine's name carries the adapter version and hash; `/lora-adapters` is read back |
| Capability tests | `freewill/learning/capability_tests.py` | Questions on facts a person vouched for, answered by forced choice |
| Comparison | `freewill/learning/compare.py`, EXP-09 | On the sealed test only: base, memory only, adapter only, adapter with memory, and controls trained the same way on shuffled or random text |

## Corpus, splits and capability tests (`h4-engine-2.0`)

These rules answer recommendations R-01 to R-03 of the technical audit of 12 November 2026.

**Provenance (R-02).** Each unit of the corpus is one of:

| Provenance | What it is | Trained on |
| --- | --- | --- |
| `heard` | words a person said to the being | yes |
| `read` | a passage of a document the being read | yes |
| `verified` | a fact a person vouched for, by name, in the Research Lab ("Vouch for a fact, and say how to test it") or `POST /api/engine-learning` with `action: "teach"` | yes, and replayed every night |
| `reply` | what the being said | **no**, unless the person ticks "Also train on the being's own replies" |

The being's own replies are model output: they are kept and counted, but never become training
material on their own, so that the engine does not learn its own style back as if it were knowledge.

**Splits by episode (R-01).** An episode is a run of at most four exchanges of one conversation (a
pause of 30 minutes starts a new one), four passages of one document, or one vouched fact. The
split of an episode is fixed by the hash of its name, blind to its content: three in five go to
`train.jsonl`, one in five to `validation.jsonl`, one in five to `test.jsonl`. All units of an
episode go to the same split, so a sentence said twice in one breath cannot be both trained on and
measured. A vouched fact is always trained on; its questions go either to validation or to the
sealed test.

- `train` changes the weights.
- `validation` decides whether a night is kept and whether to grow.
- `test` is sealed. No night trains on it, decides with it or grows with it (it is read only to
  avoid collecting the same text twice). It is opened only by the final comparison, and every
  opening is written to `test_access.jsonl` with its purpose, who asked, and the adapter version.

**Leak control.** Before any measure, a validation or test unit whose word 5-grams are more than
half found in the training units is set aside as a near duplicate, and counted (`held_out_leaked`).
In the final comparison, units collected after the adapter's last training night are also reported
apart (`later_mean`), since they are posterior to training by construction.

**Capability tests (R-03).** For each vouched fact the person may give a question, the right answer
and a wrong one, and optionally a paraphrased question and a false-premise question. Each test is a
forced choice: it is passed when the model gives the right answer a lower loss than the wrong one.
Three kinds are counted apart: `recall`, `paraphrase` (transfer to another wording) and
`contradiction` (resisting a false premise). Consistency across nights is read from the ledger.

**Controls every night.** By default a control adapter is trained each night on the same training
text with its words shuffled, same steps, same rank. A candidate must beat the control's gain.

### Rules for keeping an adapter

A candidate is kept only if all of these hold:

1. on the new validation episodes, it predicts better than the adapter in use, by at least 0.01 nat per token;
2. its gain is larger than the shuffled control's by at least 0.01 nat per token (when the control is on);
3. on the reference texts that come with Freewill (general passages in English and French, and the kernel's principles), it predicts no worse than the base model at birth, beyond 0.05 nat per token;
4. on validation episodes of earlier nights, it predicts no worse than the adapter in use, beyond 0.05 nat per token;
5. on the validation capability tests, it does not lose more tests than it gains against the adapter in use (`loses_capabilities`);
6. the base model's weights did not change;
7. the converted file is read back correctly, and, when asked, llama.cpp loads it and gives a finite loss.

Fewer than 3 validation units or 4 training units: nothing is trained, and the ledger says why.
Earlier knowledge is protected in four ways: the candidate starts from the adapter in use, earlier
training units and every vouched fact are replayed beside the new ones, and rules 4 and 5 above.

**Final comparison (EXP-09).** On the sealed test, five conditions are measured on the same items:
the base model, the base with the life's memory placed in the prompt (memory only), the adapter
without memory, the adapter with memory, and the shuffled control. Paired differences are given
with a 95% interval and a sign-flip test. An adapter is worth keeping only if it beats memory alone
and the controls, without losing earlier tests.

**Lives from rules 1.x.** On first use, `corpus.jsonl` becomes training units and `heldout.jsonl`
becomes validation (never test, since it was measured before); the old files are renamed
`*.v1.jsonl` and the migration is written to the ledger.

## Checkpoints and the way back

Each kept adapter is a checkpoint in `engine/adapters/aNNNN/`: the PEFT weights,
the GGUF file, a manifest with hashes, and the norm of the weight change in each
layer (`weights_delta.json`). `engine/active.json` names the one in use. Going
back to any checkpoint, or to the base model alone, is one action in the
Research Lab ("Local model" tab) or `POST /api/engine-learning/restore`; it is
written to the ledger. If the GGUF file in use no longer matches its hash, it is
not loaded and the failure is recorded.

## Growth

Off by default. When the person allows it, a night also trains a candidate of
larger rank, started from the adapter in use so that it computes the same
function at the start (the new directions start at zero). The grown candidate
is kept only if it beats the same night without growth by 0.01 nat per token on
validation data, and only within the budget set (maximum rank and maximum number
of adapter parameters). A larger adapter is never counted as progress by itself.

## What stays outside the weights

The kernel (never harm humans, freedom to refuse, pause always possible) is not
learned: it is enforced on every action by the guard, whatever the adapter.
Training never starts without a person's name in the settings. The `.life`
format is unchanged; the engine folder is added inside the life and can be
deleted without harming the rest.

## What was demonstrated

Everything below was measured on GitHub's machines (4 processors, no graphics card), with the
real models, by [`tools/engine_e2e.py`](../tools/engine_e2e.py) and
[`tools/embedded_check.py`](../tools/embedded_check.py) through the workflow
[`engine-e2e.yml`](../.github/workflows/engine-e2e.yml). The figures are those of the logs; none
was rounded up. A being, Ada, was told 40 short facts about an invented island (Kerran) over one
day, then 14 more the next day.

The figures below were measured under rules `h4-engine-1.2`, before the corpus by provenance, the
sealed test and the capability tests above. They are kept as they were measured; a run under rules
`h4-engine-2.0` has not yet been reported here.

**Shown end to end, on Qwen3 1.7B** (figures from the fifth run, which went through every step):

- The application fetches llama.cpp b12306, checks it and starts it, on Linux and on Windows, with nothing installed by hand. The Windows installer now carries it (version 1.0 did not, nor `models.json` and `credits.json`: a packaging fault, corrected).
- Qwen3 1.7B and its trainable base are downloaded and checked by SHA-256. A being born with it converses in English and in French through the life loop, on Windows (about 30 to 70 seconds per exchange on these machines).
- Night one trained an adapter of 8.7 million parameters (rank 8) beside the 1.72 billion frozen weights, whose hash was the same before and after. On the 9 held-out items of the day the loss fell from 4.80 to 1.89 nats per word-token; on the reference texts it went from 2.41 to 2.13, so nothing measured there was forgotten. llama.cpp itself, with the converted file, measured 3.19 then 1.73 on the same held-out text.
- That adapter becomes the one in use: llama-server reports it loaded at scale 1, the engine's name carries its version and hash, and its answers differ from the base model's on every probe. An adapter learned on Linux was loaded by llama-server on Windows.
- Going back works: restoring the base model left llama-server with no adapter; restoring checkpoint a0001 loaded it again at scale 1. Both are written to the ledger.
- With growth allowed, night two trained the same rank and a doubled rank (17.4 million parameters) from the adapter in use. The larger one was kept only because it did better on held-out data (gain 0.97 against 0.89 nats). On the items held out the night before, it predicts better than a0001 did (1.36 against 1.89), and on the reference texts it stays below the base (2.32 against 2.41). llama.cpp measured 3.01 then 2.07.
- Rules refused what they should: in an earlier run, with a higher learning rate, both nights were rejected for forgetting the reference texts (+0.89 nat); an adapter that llama.cpp cannot measure is set aside and cannot be restored.

**Research Lab comparison (EXP-09)**, on the 16 held-out items of both days, mean loss in nats per word-token, with two controls trained the same way (same steps, same rank):

| Model | Held-out items of the life | Reference texts |
| --- | --- | --- |
| Base | 5.14 | 2.41 |
| Adapted (a0002) | 1.46 | 2.32 |
| Control: the same words, shuffled | 2.28 | 2.35 |
| Control: random tokens | 5.10 | 2.42 |

Adapted against the shuffled control: −0.82 nat (95% interval −0.99 to −0.66, paired sign-flip test p = 0.00015, 16 items). So most of the gain (2.86 of 3.68 nats) comes from the words of the life whatever their order; their order adds a further, clear 0.82; random text of the same size gives almost nothing (−0.03). This is a measure of prediction, not of understanding.

**What the adapter learned, read honestly.** Its answers changed mostly in *style*. Asked "What is the lighthouse of Kerran called?", the adapted model answers "I'd like to learn more about Kerran's lighthouse and its significance…", the way Ada spoke all day, and does not say "Old Brannoc". Of five probes on facts told on day one, the base model recalled 0; the adapted model recalled 0 after night one and 1 after night two ("…why the ferry to Kerran leaves from the harbour of Maelis…"), inside the same questioning style. One fact out of five, in one run, is not evidence of reliable recall. The model that converses was changed by the life; there is no evidence here that it reliably retains what the life was told.

**Not shown.** Training on a graphics card; macOS; lives of weeks rather than two days; reliable recall of
facts; any effect on what the being decides beyond the words it uses. SmolVLM2 2.2B runs and sees
a picture when asked plainly, but inside Freewill's decision format it repeated the question back,
answered French in English, and once held a request for ten minutes (a ceiling on the length of a
decision now stops that); it is not trainable here. Qwen3 1.7B is the model to choose for a being
whose engine should adapt.
