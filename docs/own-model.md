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

**What this means.** A model can be made as large as the person wants: growth is mechanical and verified. But the new parameters are worth something only once they are trained on enough text. Beyond about 2 billion, books alone are far from enough (Project Gutenberg holds about 75,000), and other open corpora would be needed. Growing the width of the feed-forward blocks and the depth, while the model's own width (2,048) stays fixed, is also less efficient than a model designed at that size.

## 3. How it is trained

There are three stages. Each one is a separate decision written to an append-only ledger (`ledger.jsonl`), with what was measured before and after.

| Stage | What is trained | Measured on (never trained on) | Kept only if |
|---|---|---|---|
| **read** | adapters + grown layers | 1 passage in 10 of the books, chosen by hash | held-out passages are predicted better by at least 0.01 nats/token |
| **see** | the bridge | 1 drawn image in 4: colour (6 choices) and shape (4) | accuracy rises by at least 5 points **and** beats, by at least 5 points, the same questions asked about another item's image |
| **watch** | bridge + adapters | 1 drawn video in 4: direction of motion (4 choices) | accuracy rises by at least 5 points **and** beats both the reversed-frames control and the single-frame control; seeing loses at most 5 points; reading gets worse by at most 0.05 nats/token |

When a stage is refused, the weights from before it are restored.

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
- **What it does not do yet.** It is not yet trained by a life's nights (`can_learn = False`), and llama.cpp does not run it, so it has no GGUF file.

## 5. Training from zero: what it would take

The same architecture can be built with random weights (`build(init="random")`). Here is an order-of-magnitude estimate. It is a calculation, not a measurement.

- **Data.** About 20 tokens per parameter means roughly 36 billion tokens. All of Project Gutenberg holds a few billion, so books alone are not enough.
- **Compute.** About 6 × 1.8·10⁹ × 3.6·10¹⁰ ≈ 4·10²⁰ operations. That is roughly 300 hours on one H100 GPU at a realistic efficiency, which means several hundred euros of rented GPU time, without counting the eye.
- **On a personal computer.** Months of computing on a high-end graphics card, and the optimiser's state for 1.8 billion parameters does not fit in 24 GB without special techniques.

That is why the chosen route starts from open pretrained bases.

## 6. Results

Pending: the `own model end to end` workflow on pull request 13 is running. Only the numbers from its logs will be written here.
