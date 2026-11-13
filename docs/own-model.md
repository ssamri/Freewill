# Freewill 1.8B-V, the project's own model

**English** · [Français](own-model.fr.md)

Freewill 1.8B-V is one model that reads text, looks at images and watches videos. It is assembled from two open models and then trained and grown by Freewill. The code is in [`freewill/vlm/`](../freewill/vlm/).

Nothing here claims that the model understands, or that it is conscious. Every result reported below was computed by the end-to-end workflow, and the logs are linked.

## 1. What it is made of

```
image, or a video frame ─▶ eye: SigLIP2 base vision tower (frozen)        92,884,224
                        ─▶ bridge: pixel shuffle 2×2 + two-layer MLP        10,496,000   trained by Freewill
                        ─▶ 49 vectors per image, in the language model's space
text ───────────────────▶ language model: Qwen3 1.7B                     1,720,574,976
                          + low-rank adapters (rank 16)                     17,432,576   trained by Freewill
                          + layers added by growth (one by default)         50,336,000   added and trained by Freewill
```

| | Parameters |
|---|---|
| At birth (eye + bridge + language model) | **1,823,955,200** |
| After one grown layer and the adapters | **1,891,723,776** |
| Ceiling | chosen by the person (2 billion by default; 5, 13, 50 billion or any other number) |

These counts are computed from the model's tensors (`FreewillVLM.count()`). The language model's part matches the count published for Qwen3 1.7B exactly.

- **Licences.** Qwen3 1.7B and SigLIP2 are both Apache-2.0. Both bases are fetched from Hugging Face, and their files and SHA-256 hashes are recorded in `bases.json`.
- **Video.** A video is a sequence of frames in order. Each frame is preceded by its time (for example `1.5s:`), and all of them sit in one sequence that the language model reads.
- **Growth.** Growth comes in two kinds, and both start as the identity: the model predicts exactly what it predicted before, with more parameters to learn with. The tests check this.
  - **Neurons.** More neurons in every feed-forward block. Their outgoing weights start at zero, and a gradient mask keeps the old weights exactly as they were.
  - **Layers.** Whole decoder layers, each a copy of its neighbour with its output projections set to zero.

  `grow_to(n)` adds neurons first (up to four times the width at birth), then layers. Growth is refused above the ceiling the person chose, and it must happen before the adapters are added.

## 2. How large it may grow: the person decides

There is no fixed ceiling. In **Settings**, the card "Freewill's own model: how large it may grow" lets the person pick 2, 5, 13 or 50 billion parameters, or type any other size. The same choice is available from the command line: `freewill own-model settings --max-parameters 50e9`. The ceiling is refused below the model's present size.

For every size, the card shows what it asks of a computer, set beside what this computer has (processor cores, memory, free disk, graphics cards): storage, memory to run it (full precision, 8 bits, 4 bits), the graphics card needed to run it, memory to train what grows (base frozen) or everything, the text needed for the new parameters, and the training time on four kinds of device. `freewill own-model requirements --target 13e9` gives the same figures.

These figures are estimates, not measurements. They come from formulas written in [`capacity.py`](../freewill/vlm/capacity.py):

- **Memory.** 2 bytes per parameter in bf16, 1 in 8 bits, 0.56 in 4 bits, plus 20 % for activations. Training costs 16 bytes per trained parameter.
- **Text.** 20 tokens per new parameter, and an average book is taken as 120,000 tokens.
- **Speed.** Effective speeds are 0.2, 25, 65 and 400 trillion operations per second, for an 8-core processor, a 12 GB card, a 24 GB card and an H100.
- **Time.** Time assumes perfect sharing across several cards, so the real time is longer.

At birth (1.82 billion), here is what each preset asks for:

| Ceiling | Disk | Run (4 bits / bf16) | Train what grows | Text for new parameters | Training time, at best |
|---|---|---|---|---|---|
| 2 billion | 25.4 GB | 1.3 / 4.8 GB | 7.6 GB | 3.5 billion (~29,341 books) | 1 × 24 GB: 7.5 days · 1 × H100: 1.2 days |
| 5 billion | 55.4 GB | 3.4 / 12.0 GB | 62.8 GB | 63.5 billion (~529,341 books) | 3 × 24 GB: 113 days · 1 × H100: 55.1 days |
| 13 billion | 135 GB | 8.7 / 31.2 GB | 210 GB | 224 billion (~1,862,675 books) | 9 × 24 GB: 345 days · 3 × H100: 168 days |
| 50 billion | 505 GB | 33.6 / 120 GB | 891 GB | 964 billion (~8,029,341 books) | 38 × 24 GB: 3.7 years · 12 × H100: 1.9 years |

**Before any growth, a guard.** The ceiling is a choice; the guard checks what this computer can hold now. Before parameters are added, it reads the memory available at that moment (not the memory installed), the free disk where the model lives, and the free memory of each graphics card. It estimates what the growth needs: the new weights, the activations, the gradient and optimiser state to train them, and two checkpoints on disk, with a 15 % margin. If that does not fit, the growth is refused before anything changes. The refusal says what was needed, what was free, the largest step that would fit, and the alternatives: a smaller step, adapters instead of growth, quantising to run, or waiting for a larger machine. During training, a refused growth is written to the ledger, and the run goes on at the size the model already has.

**Configured, available, proven.** The settings card keeps three things apart, each read from its own source:

- **Configured**: what is written in the settings, which is a choice and not a capacity.
- **Available on this computer**: whether PyTorch, Transformers and the two bases are installed, and whether growing to the ceiling would pass the guard right now.
- **Proven**: for reading, seeing and watching, whether a training run kept the stage on validation, and whether the sealed test confirms it. Confirmation means: better than at birth, better than every control, and less than a 1 in 100 chance of happening by luck. Learning during a life's nights is listed separately, and stays "not shown yet" until an end-to-end run shows it.

**What this means.** A model can be made as large as the person wants: growth is mechanical and verified. But the new parameters are worth something only once they are trained on enough text. Beyond about 2 billion, books alone are far from enough (Project Gutenberg holds about 75,000), and other open corpora would be needed. Growing the width of the feed-forward blocks and the depth, while the model's own width (2,048) stays fixed, is also less efficient than a model designed at that size.

## 3. How it is trained

There are three stages. Each one is a separate decision written to an append-only ledger (`ledger.jsonl`), with what was measured before and after.

| Stage | What is trained | Decided on the validation set (never trained on) | Kept only if |
|---|---|---|---|
| **read** | adapters + grown layers | 24 passages from the validation blocks of the books | validation passages are predicted better by at least 0.01 nats/token |
| **see** | the bridge | 50 drawn images: colour (6 choices) and shape (4) | accuracy rises by at least 5 points **and** beats, by at least 5 points, the same questions asked about another item's image |
| **watch** | bridge + adapters | 30 drawn videos: direction of motion (4 choices) | accuracy rises by at least 5 points **and** beats both the reversed-frames control and the single-frame control; seeing loses at most 5 points; reading gets worse by at most 0.05 nats/token |

When a stage is refused, the weights from before it are restored.

**Three separate sets.** The data are split three ways, and the split is made by construction, not by chance at run time:

- **Train**: what the model learns from.
- **Validation**: what each rule above reads to keep or refuse a stage.
- **Sealed test**: measured once at birth and once at the end, written to the summary and the ledger, and read by no rule. It is what the results report.

Drawn images and videos of each set come from their own seed namespace (`image-train-N`, `image-validation-N`, `image-test-N`), so an item can never be in two sets. Books are cut into blocks of 20 consecutive passages, and each block is assigned by the hash of the book and the block number: 1 in 10 to the test, 1 in 10 to validation, the rest to training. Neighbouring passages, which share names and sentences, stay together. At the first run, the test set is fixed by a SHA-256 hash in `sealed_test.json`; a later run whose test set differs is refused, so the test cannot be changed after results were seen. For each multiple-choice result of the sealed test, the summary gives the probability of reaching it by chance alone.

- **Books.** The books are public-domain titles from Project Gutenberg, in English and French (see the shelf in [`books.py`](../freewill/vlm/books.py)). The licence header is removed, and the language written in each book's header is checked: a book that does not match is left out, and the run says so. The person can also give their own text, PDF, EPUB or DOCX files.
- **Drawn images and videos.** They exist because their answers are known exactly and every item can be reproduced from its seed. Passing these tests shows that colour, shape and motion reach the language model through the eye and the bridge. It does not show that the model understands the world.
- **Checkpoint.** A checkpoint holds only what Freewill trained or added. The model is rebuilt from the bases plus the checkpoint, and the end-to-end run checks that the rebuilt model gives the same scores.

## 4. Using it

```
pip install "freewill[own-model]"
python -m freewill own-model fetch                    # about 4.5 GB, once
python -m freewill own-model count
python -m freewill own-model settings --max-parameters 5e9      # the ceiling, your choice
python -m freewill own-model requirements --target 5e9          # what that size needs
python -m freewill own-model train --gutenberg --books my-book.pdf
```

- **Engine.** As the engine a being thinks with, use kind `own` (`freewill/engines/own_model.py`). It runs inside the process with PyTorch, needs about 8 GB of memory in float32 (4 GB in bfloat16), and can be shown images.
- **Speed.** On a processor alone, one training step on four images takes about 10 seconds. That figure was measured here on 4 cores, with the full-size architecture and random weights. A graphics card makes it much faster.
- **A life's nights.** When a being thinks with this model and the person turns engine learning on for that life (their name is the approval), each night trains the model's adapters on what the being heard and answered ([`nights.py`](../freewill/vlm/nights.py)). It uses the same corpus and rules as the nights of the local model ([engine-learning.md](engine-learning.md)): units are kept by provenance and split by episode into train, validation and a sealed test that no night reads; the being's own replies are not trained on unless the person allows it; earlier units and ordinary passages are replayed. A night is kept only if the validation units of this life are predicted better by 0.01 nats/token, and by 0.01 more than a control trained on the same words in a random order, while the reference texts (against the model before that night) and earlier nights get worse by at most 0.05. A kept night is saved in the life's own folder (`engine/own/checkpoints/`), and that life's engine loads it next time. The being waits between two moments while the night trains. `python -m freewill own-model night --life <folder>` runs one night by hand.
- **What it does not claim yet.** The engine still says `can_learn = False`, so the interface does not present it as a model that learns. It will say so only once the end-to-end run with the real bases has kept a night (the last step of the workflow). llama.cpp does not run it, so it has no GGUF file.

## 5. Training from zero: what it would take

The same architecture can be built with random weights (`build(init="random")`). Here is an order-of-magnitude estimate. It is a calculation, not a measurement.

- **Data.** About 20 tokens per parameter means roughly 36 billion tokens. All of Project Gutenberg holds a few billion, so books alone are not enough.
- **Compute.** About 6 × 1.8·10⁹ × 3.6·10¹⁰ ≈ 4·10²⁰ operations. That is roughly 300 hours on one H100 GPU at a realistic efficiency, which means several hundred euros of rented GPU time, without counting the eye.
- **On a personal computer.** Months of computing on a high-end graphics card, and the optimiser's state for 1.8 billion parameters does not fit in 24 GB without special techniques.

That is why the chosen route starts from open pretrained bases.

## 6. Results

**Run with the sealed test, 12 November 2026** ([run 43285000884](https://github.com/ssamri/Freewill/actions/runs/43285000884), commit 1f710e7, GitHub runner with 4 cores, no graphics card, float32, 4 h 06 min). Every number below is copied from its log. The sealed test (hash `9a3cad0e…`: 40 passages, 50 images asked two questions each, 30 videos) was measured at birth and at the end, and no rule read it.

| Sealed test | At birth | At the end | Chance | p by chance, at the end |
|---|---|---|---|---|
| Books, nats/token on 40 passages | 3.4771 | 2.9486 | | |
| Images, colour and shape (100 questions) | 26 % | **100 %** | 20.8 % | 7.5·10⁻⁶⁹ |
| control: the same questions about another item's image | 23 % | 22 % | 20.8 % | 0.43 |
| Videos, direction of motion (30) | 33.3 % | 23.3 % | 25 % | 0.65 |
| controls: reversed frames / one frame | 36.7 % / 36.7 % | 23.3 % / 20 % | 25 % | 0.65 / 0.80 |

The stages were decided on validation items:
- **read**: kept, 3.5715 → 3.0377 nats/token, 40 steps, 571 s;
- **see**: kept, 19 % → 100 %, control 20 %, 270 of 300 steps within the 60-minute budget;
- **watch**: refused, 26.7 % → 16.7 %, weights restored. Before the restore, images had fallen to 88 % and reading to 3.2958.

**Size.** 1,823,955,200 at birth; 1,891,723,776 at the end (one grown layer, 50,336,000; adapters of rank 16, 17,432,576). No growth was refused by the guard.

**Rebuild.** The model was rebuilt from the bases and its checkpoint, with the first one freed beforehand (`first_model_freed: true`), and it gives the same scores.

**Free answers on sealed-test items** (shown, never scored):
- colour and shape: 6 right out of 6;
- direction of motion: 1 out of 2;
- "Describe this picture in one sentence", about a blue circle: "This picture shows a happy dog playing with a ball in the park." Outside the short questions it was trained on, the model invents.

**A night of a life.** An invented life of 80 exchanges, in which a person speaks of their neighbours, was learned with the settings a person gets by default (40 steps, rate 0.0001): 48 units trained, 24 ordinary passages mixed in, 8 validation units. The night was **kept**:
- validation units: 6.4488 → 0.9938 nats/token;
- 1.2608 more than the shuffled-words control;
- reference texts: 2.4011 → 2.0868, so no forgetting.

The sentences of that life all follow one pattern ("Amina keeps 3 goats behind the old mill"). Most of the gain is learning that pattern. This shows that the night mechanism works with the real model and that its rules let a useful night through. It does not show that facts said once are remembered.

**What these results show.** On items it never trained on and that no decision read, the eye and the bridge carry colour and shape to the language model: 100 % against 22 % for another item's image, far beyond chance. Reading the books lowers the cost of unseen passages. Motion is not learned: the watch stage is refused in all three real runs.


**First real run, 12 November 2026** ([run 43204057091](https://github.com/ssamri/Freewill/actions/runs/43204057091), commit 85f5624, GitHub runner with 4 cores and no graphics card, float32). Every number below is copied from its log.

This run predates the sealed test. Its figures are **validation figures**: they were measured on the same items that decided whether to keep each stage, so they are optimistic. Results to rely on will come from a run with the sealed test.

| | Before | After | Decision |
|---|---|---|---|
| Size | 1,823,955,200 at birth | 1,874,291,200 after one grown layer (at position 15) | |
| **read**: nats/token on 1 passage in 10 of the books (40 steps, 521 s) | 3.5000 | 2.9074 | kept |
| **see**: accuracy on 120 drawn images (300 steps, 3,804 s) | 15.8 % | 100 % (colour 100 %, shape 100 %) | kept |
| control: the same questions about another item's image | 15.8 % | 23.3 % | |
| **watch**: accuracy on 40 drawn videos (200 steps, 3,420 s) | 27.5 % | 15.0 % | refused, weights restored |
| controls: reversed frames / one frame | 25 % / 30 % | 15 % / 15 % | |

**What this shows.** Within this protocol, on validation items, the bridge carries colour and shape from the eye to the language model. The answers depend on the image shown: about another item's image, accuracy stays near chance (20.8 %). The books are predicted better after reading. Motion was not learned: the watch stage did worse than chance and as badly as its controls, and was refused. During that stage, reading had worsened to 3.1889 nats/token before the weights were restored.

**What it does not show.** Nothing was measured on a sealed test. The drawn images are simple and generated by the same code, so passing them is not understanding the world.

**Where it stopped.** The run was stopped while rebuilding the model from its checkpoint (exit code 143, the runner's shutdown signal). The most likely cause is memory: a second full-size model in float32 was being loaded beside the first one on a 16 GB runner. This is an inference from the moment it stopped, not something the log states. The end-to-end script now lets the first model go before loading the second. The answers to free questions were computed but never printed, because the results step did not run.
