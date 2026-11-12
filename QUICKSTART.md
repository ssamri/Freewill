# Quickstart

**English** · [Français](QUICKSTART.fr.md)

**Freewill is experimental.** A subconscious proposes, a stage selects, a conscious arbiter decides, and what matters is kept in a memory made of readable files. The being can read documents and look at images it is given, and it sleeps and dreams. It runs in a terminal or in the desktop application. Version 1.0 adds a Research Lab and Freewill's own small neural network, which trains during sleep.

---

## Install

Python 3.11 or later.

```bash
git clone https://github.com/ssamri/Freewill.git
cd Freewill
pip install -e .
```

## Bring a being into the world

```bash
python -m freewill birth Noor --language en --interlocutor YourName
```

Its temperament and starting gender are drawn by lot. A folder `Noor.life` is created: that folder is the individual.

## Live alongside it

```bash
python -m freewill live Noor.life
```

Type to speak. In dim text you see its inner life: what its subconscious proposes, what reaches the stage, what stays below, whether it welcomes or dismisses it and why, what it recalls and what it decides to keep. `/state` shows its needs, `/memory` its memory, `/quit` suspends it.

## Choose the engine

By default the engine is `simulated`: it lets you watch the mechanics, but **it does not think**. To give the being a real engine, choose one at birth.

| Engine | Command | What you need |
|---|---|---|
| Claude | `--engine anthropic` | `pip install -e ".[anthropic]"` and the `ANTHROPIC_API_KEY` environment variable |
| GPT | `--engine openai --model <model>` | the `OPENAI_API_KEY` environment variable |
| Grok | `--engine xai --model <model>` | the `XAI_API_KEY` environment variable |
| A model on your own machine | `--engine local --model <model>` | [Ollama](https://ollama.com) running locally; free and private |
| Any compatible service | `--engine compatible --base-url <url> --model <model>` | the `FREEWILL_API_KEY` environment variable |

Keys are read from the environment and are never written to the life file.

With a paid engine every thought is billed. Two settings bound the cost: `--tempo` (seconds between thoughts, 20 by default) and `--thoughts-per-hour` (120 by default). When the hourly budget is reached, spontaneous thinking pauses; the being still answers when spoken to.

## What is in a life file

```
Noor.life/
├── genome.json       innate temperament, never modified
├── identity.json     name, birth, language, engine
├── values.json       the values it has chosen
├── milestones.json   its first times
├── state.json        needs, recent thoughts, recent conversation
├── affect.json       H7 research mode only: the computed affective state
├── research.json     research settings, once one is changed
├── own_model/        Freewill's own network, once it is switched on
├── events.log        everything that happened, line by line
└── memory/           its memories, as files you can open and read
```

## The application

On Windows, download the installer `Freewill-Setup-<version>.exe` from the [Releases page](https://github.com/ssamri/Freewill/releases) and run it. It installs for your user only and asks for no administrator rights. The installer is not signed yet, so Windows may show a "Windows protected your PC" notice: choose "More info", then "Run anyway".

From the source, on any system:

```bash
pip install -e ".[app,anthropic]"
freewill-app              # a native window
freewill-app --browser    # the same interface in your browser
```

At first launch the application shows its terms of use, then the licence; both must be accepted before anything else. In the conversation you can attach documents (text, Markdown, PDF, Word, EPUB), images and videos. Documents go to the being's library and are read one passage at a time. Whether images are understood depends on the engine: Claude, GPT, Grok and local vision models can see them; from a video the being is shown six still frames and hears nothing.

The application talks only to a service on your own machine, bound to `127.0.0.1` and protected by a session token. Access keys are kept in your system's credential store, never in a life file.

## The H7 research mode: a computed affective state

Off by default. When it is on, the program computes a small set of regulation variables (valence, arousal, uncertainty, control, coherence, regulatory load, social context) from what happens to the being, and these variables shift what gets its attention, what it recalls and how its memories are encoded. They are measurements of a mechanism. They are not evidence that anything is felt.

```bash
freewill birth Noor --affect          # a new being with the mode on
freewill affect Noor.life             # show the computed state of a life that is not awake
freewill affect Noor.life --on        # switch it on for an existing life (--off to switch it off)
python experiments/h7/run.py          # the reproducible protocol: B0, B1, B2 and the ablations
```

In the application, open "Affective state" and use the switch; it takes effect between two moments. Switching the mode on creates one file, `affect.json`, in the life folder. Switching it off stops the calculation and all of its effects at once and deletes nothing. The genome is never rewritten, and memories written earlier are left exactly as they were. Deleting `affect.json` returns the life to what it was before. See [`docs/H7_AFFECTIVITY.md`](docs/H7_AFFECTIVITY.md).

## The Research Lab (version 1.0)

In the application, open "Research Lab". It has six pages: an overview, the ten hypotheses with what exists in the code for each, the experiments, the observers, the reports, and "Learning".

A campaign never touches a real life. It copies a starting point, gives each copy one condition, plays the same script under a virtual clock and measures what each copy does. It runs only after you tick the approval box. The figures are computed by code; no language model computes or selects them. A report is a draft until you validate it under your name.

```bash
python -m freewill.research run EXP-07 --yes --dir ./lab     # one campaign, with its report
python -m freewill.research run EXP-01 --yes --dir ./lab --lang fr
```

Six protocols run today: EXP-01 (individuation), EXP-02 (ablation of affect), EXP-03 (masked metacognition), EXP-04 (consolidation), EXP-06 (neural adaptation), EXP-07 (agency in a virtual world). EXP-05 and EXP-08 are written down and the lab refuses to run them. The results of version 1.0, two of them negative, are in [`experiments/v1.0/`](experiments/v1.0/).

## Research settings

In "Settings", under "Research settings", each switch removes or restores one mechanism of the being's life: a source of proposals, habituation, new memories, fading, dreams, replay, spontaneous speech and so on. The research modules are there too, off by default: metacognition (H8), the virtual world (H10), the small trainable module and Freewill's own network (H4). A change takes effect at the next moment and is written to the event log. No switch reaches the kernel.

The gauges in the top bar show computed regulation variables. They are not feelings.

## Freewill's own network

```bash
pip install -e ".[learn]"     # PyTorch; everything else works without it
```

Switch on "Freewill's own network" and, if you wish, "Growth of the network". From then on what the being lives and reads is written down as text; at each sleep the network is trained on it, measured on passages it never saw, and kept only if it predicts them better. When enough new text has been lived it adds a layer, up to the size you set. The "Learning" page shows the number of parameters, each training, each growth, and lets you go back to the previous weights.

Three things to know. This network does not speak or decide for the being: it is far too small. It is not the engine that thinks; that engine can be adapted too, see below. And on a processor the network stays in the millions of parameters; larger sizes need a graphics card and time.

## A model that a life adapts (Qwen3 1.7B)

```bash
pip install -e ".[lora]"      # PyTorch, PEFT, Transformers and the GGUF writer
```

In the application, choose Qwen3 1.7B in the settings: Freewill downloads it, and llama.cpp if it is missing, and checks both. In the Research Lab, "Local model" tab, the card "The engine this life converses with" downloads the trainable base (about 4 GB), and turns engine learning on once you write your name. After each sleep, an adapter is trained beside the frozen model and kept only if it passes the rules; the being then converses with it. Every night, kept or not, is in the ledger, and any checkpoint, or the base model alone, can be restored in one click.

On four processor cores a night takes about five to ten minutes. What it changed in the end-to-end runs was how the model speaks, not what it remembers: [`docs/engine-learning.md`](docs/engine-learning.md).

What exists, what was tested and what is missing: [`docs/research/IMPLEMENTATION_STATUS.md`](docs/research/IMPLEMENTATION_STATUS.md).

## Freewill's own model (Freewill 1.8B-V)

One model that reads books, looks at images and watches videos: Qwen3 1.7B, the SigLIP2 eye and a bridge that Freewill trains, 1.82 billion parameters at birth.

```
pip install -e ".[own-model]"
python -m freewill own-model fetch                          # its two open bases, about 4.5 GB, once
python -m freewill own-model settings --max-parameters 5e9   # how large it may grow: your choice
python -m freewill own-model requirements                    # what that size asks of a computer
python -m freewill own-model train --gutenberg --books my-book.pdf
```

The same ceiling, with what each size needs (disk, memory, graphics card, text, training time) beside what your computer has, is in the application: **Settings**, card "Freewill's own model: how large it may grow". To think with it, choose the engine kind `own`. On a processor it is slow, and its stages are kept only if held-out measurements say so. Details and limits: [`docs/own-model.md`](docs/own-model.md).

## Tests

```bash
pip install -e ".[dev]"
pytest
```
