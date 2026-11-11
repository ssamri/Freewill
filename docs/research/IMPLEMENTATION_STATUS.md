# Freewill V1.0: implementation status

[Français](IMPLEMENTATION_STATUS.fr.md)

This page says what exists in the code, what was tested, what was measured and what is missing. It is written so that nothing has to be taken on trust: every line points to files, to tests that anyone can run, and to results that anyone can recompute.

Two rules govern it. A result is reported as it came out, including when it shows nothing. And nothing here says, or implies, that a system is conscious or feels anything: the figures bear on mechanisms and, at most, on functions.

The states used are: **done and verified** (tested, and the tests pass), **done, not tested** (written, never run for real here), **partial**, **blocked**, **not started**.

## 1. Workstreams

| Workstream | State | Files | Tests run | Evidence | Risks | Next step |
|---|---|---|---|---|---|---|
| Research settings (26 switches, 7 bounded numbers) | done and verified | `freewill/core/research.py`, `freewill/core/loop.py` | `tests/test_research.py`, `tests/test_modules.py` | defaults reproduce the earlier loop; every change is written to the event log | a switch added later must keep its default neutral | none |
| Evidence: contracts, append-only journal, snapshot hashes | done and verified | `freewill/research/schemas.py`, `evidence.py` | `tests/test_research.py` | journal survives a crash; hashes follow the state | timestamps of the wall clock remain in life files (not in results) | none |
| Deterministic statistics | done and verified | `freewill/research/stats.py` | `tests/test_research.py` | no interval under 5 units, no test under 6 | six units give wide intervals | more seeds |
| Metric register H1 to H10 | done and verified | `freewill/research/metrics.py` | both test files | every metric is computed or says why not | most metrics are of level "mechanism" or "descriptive" | functional tasks |
| Protocols and campaigns on isolated copies | done and verified | `freewill/research/experiments.py` | both test files | six protocols run; results hashes identical across runs | simulated engine only | real engines |
| Observers A, B, C (and more) | done and verified with stand-in transport | `freewill/research/observers.py` | `tests/test_research.py` | isolation, budgets, citation checks | **no call to a real model was made here** | try with a real key |
| Reports (Markdown, PDF, reproduction pack) | done and verified | `freewill/research/reports.py` | `tests/test_research.py` | twelve real reports in `experiments/v1.0/` | PDF is text only | figures |
| H7 computed affect | done and verified | `freewill/core/affect/` | `tests/test_affect.py` | EXP-01, EXP-02 | coefficients not calibrated | calibration |
| H8 metacognition | done and verified | `freewill/core/metacognition.py` | `tests/test_modules.py` | EXP-03 | tested against a large, built-in change only | finer changes |
| H9 sleep in phases | done and verified | `freewill/core/loop.py` (`_sleep`) | `tests/test_modules.py` | EXP-04 | retention is a computed strength, not a recall task | retention and transfer tasks |
| H10 agency in a virtual world | done and verified | `freewill/core/agency.py`, `freewill/research/environments.py` | `tests/test_modules.py` | EXP-07 | a five-by-five grid; a naive baseline | richer worlds |
| H4 small trainable module | done and verified | `freewill/learning/adapter.py` | `tests/test_modules.py` | EXP-06 | 25 to 100 weights; effect on behaviour small | larger features |
| H4 Freewill's own network (trains, grows) | done and verified on CPU | `freewill/learning/own_model.py` | `tests/test_modules.py` (run with PyTorch 2.15, skipped without it) | `experiments/v1.0/own_model_run.json` | does not speak for the being; growth by depth only; not run on GPU | let it take part in thinking; width growth |
| H4 adapters for large models (LoRA) | **partial**: training done and verified on a toy base model only | `freewill/learning/lora.py` | `test_lora_trains_only_the_adapter_and_keeps_nothing_that_does_not_help` (run with PEFT 0.21, skipped without it) | base weights hashed identical before and after; rejected training leaves no file | never run on a real language model, a real tokenizer or a GPU; the adapter cannot yet be loaded by the embedded engine; no button in the interface | run on a real base; convert and load the adapter |
| Interface: lab, learning page, research settings, gauges | done and verified by hand and by screenshots | `freewill/ui/lab.js`, `i18n-lab.js`, `app.js`, `app.css` | catalogue tests in `tests/test_modules.py` | screenshots in both languages | no automated browser test in the suite | add one |
| Two languages, never mixed; English by default | done and verified | `freewill/ui/i18n*.js`, `freewill/research/texts.py` | `test_english_is_the_default_and_the_two_catalogues_never_mix`, `test_lab_answers_come_in_one_language` | same keys, no untranslated sentence, no words of the other language | texts produced by an engine follow the life's language, not the interface's | none |
| Service: `/api/lab/*`, `/api/research` | done and verified | `freewill/server/lab_api.py`, `app.py`, `runner.py` | `test_the_service_guards_the_lab_and_the_research_settings` | token required, approval required | none known | none |
| Packaged desktop application with the lab | done, not tested | `packaging/` | none | the PyInstaller build was not run for this version | a missing data file would only show at build time | build on each system |

## 2. The ten hypotheses

"In the code" says whether the mechanism runs in the life loop. "Measured" says whether a campaign produced figures about it. Neither is a verdict: a verdict on a hypothesis is given by a person, under their name, in the lab.

| | In the code | Measured by | What the campaign showed, in one line |
|---|---|---|---|
| H1 continuity | yes | descriptive metrics in every campaign | counts of own activity; no task yet measures whether it is useful |
| H2 stage and arbitration | yes | descriptive metrics in every campaign | same remark |
| H3 needs | yes | `h3.need_share` | a mechanism-level count |
| H4 plasticity | **partly** | EXP-06, own-network run | the module learned a built-in rule; the network's loss on unseen text fell and its size grew; the engine that thinks is unchanged |
| H5 individuation | yes | EXP-01 | **no divergence beyond that of a twin life** |
| H6 open questions | yes | descriptive metrics | counts only |
| H7 computed affect | yes | EXP-01, EXP-02 | **no behavioural divergence beyond that of a twin life** |
| H8 metacognition | yes | EXP-03 | a large masked change raised the alert in 5 lives of 6 (1 of 6 under placebo) |
| H9 consolidation | yes | EXP-04 | replay raised computed retention by 0.006, interval including zero |
| H10 agency | yes | EXP-07 | attribution accuracy 0.93 with the self-model, 0.65 without, in a tiny world |

## 3. Real results

Six campaigns, each with six seeds, simulated engine, code commit `679328f`. Reports, results and reproduction packs are in [`experiments/v1.0/`](../../experiments/v1.0/). The reports are drafts: none has been validated for publication by a person.

| Protocol | Primary outcome | Result (difference from the reference, 95% interval, paired test) | `results_sha256` |
|---|---|---|---|
| EXP-01 individuation | behavioural distance on unseen sentences, minus that of a twin | history A: +0.0009 [−0.0068, +0.0085], p = 0.75. History B: the same. **Null.** | `d2103f6a23b9…` |
| EXP-02 ablation of affect | same | full H7: +0.0009 [−0.0034, +0.0060], p = 1.0. **Null.** Spoken emotions only: −0.0068 [−0.0111, −0.0034], that is, closer to the reference than its own twin | `733c67362655…` |
| EXP-03 masked metacognition | alert raised (0 or 1) | placebo 0.17, perturbed 0.83; difference +0.67 [+0.33, +1.00], p = 0.125. Brier score late in the probe: +0.12 with revision, +0.27 without | `1b8f881db3ec…` |
| EXP-04 consolidation | computed strength of earlier memories after ten days | no sleep 0.813; rest only −0.015 [−0.019, −0.011]; replay only +0.006 [−0.001, +0.013]; full sleep +0.006 [−0.001, +0.013] | `da2109fe9ec1…` |
| EXP-06 neural adaptation | share of own contents dismissed | memory only 0.413; module −0.025 [−0.058, 0.000], p = 0.5; growth allowed: never triggered, same figures | `58b71ef82ddd…` |
| EXP-07 agency | attribution accuracy | without self-model 0.65; with +0.28 [+0.19, +0.37], p = 0.031; noisy senses −0.30 [−0.35, −0.22] | `23b323c653c3…` |

How to read them:

- EXP-01 and EXP-02 are negative results. With the simulated engine, two lives given different histories behave no more differently on new sentences than two lives given the same one. They are reported as they are.
- EXP-03, EXP-04, EXP-06 and EXP-07 test mechanisms on cases built to be easy: a massive change, a rule that strengthens by construction, a fixed rule to learn, a tiny world. A positive figure there shows that the wiring works. It is not a discovery.
- p = 0.031 is the smallest value a paired sign-flip test can give with six units. Many comparisons were made and none was corrected for.
- In EXP-04, rest alone lowers the computed retention slightly compared with no sleep, because in the "no sleep" condition the moment that replaces the sleep is an ordinary moment that recalls, and recall strengthens.

**Freewill's own network.** One run on a processor (4 threads, no GPU, PyTorch 2.15), trained on this repository's documentation cut into ten "nights" of 100 steps: loss on never-seen text went from 5.55 nats per byte (a uniform guess) to 2.08; parameters went from 957,696 to 3,182,016 (2 to 7 layers), each added layer leaving predictions unchanged at the moment it was added; every night took between 4 and 15 seconds. Full record: [`experiments/v1.0/own_model_run.json`](../../experiments/v1.0/own_model_run.json). One run, one seed; the text is documentation, not a life; what the network writes is not yet language.

## 4. What is incomplete

Stated plainly, so that no one assumes otherwise.

- **The engine that thinks for a being is never trained by its life.** Embedded models are frozen GGUF files. H4 is therefore "partly implemented".
- **Adapters for large models (LoRA) are only half there.** The training is written and passes on a tiny base model with random weights: only adapter weights change, and a training that does not help leaves nothing behind. It has never been run on a real language model, because base models could not be downloaded in the environment where this version was built. The embedded engine cannot load such an adapter yet, and the interface has no button for it.
- **Freewill's own network does not take part in thinking.** It learns and grows; the being still decides with its engine. It grows in depth only. Billions of parameters are out of reach on a processor: the ceiling is a setting, and the default is five million.
- **No GPU training or benchmark was run.**
- **No call to a remote model was made** in building or testing this version. Observers with models and real engines are exercised only through stand-in transports.
- **EXP-05 (transfer between engines) and EXP-08 (human raters)** are specifications only; the lab refuses to run them.
- **Observers** have no scheduler (they analyse when asked), no tools, and no qualitative case studies.
- **Functional tasks are missing** for H1, H2, H3 and H6: their metrics count activity and say nothing of its worth.
- **The packaged application** was not rebuilt and tried for this version.
- **Reports** have no figures.

## 5. Reproducing

```
pip install -e ".[dev]"            # add ".[learn]" for PyTorch, ".[lora]" for PEFT and Transformers
python -m pytest -q                 # 127 tests; those that need PyTorch or PEFT are skipped without them
python -m freewill.research run EXP-07 --yes --dir ./lab
python tools/own_model_benchmark.py out.json --nights 10 --steps 100 --ceiling 6000000
```

The first command of the last two recomputes the `results_sha256` given above when run on the same code version. The own-network run is seeded but not guaranteed identical across machines and PyTorch versions.
