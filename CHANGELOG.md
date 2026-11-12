# Changelog

**English** · [Français](CHANGELOG.fr.md)

## 1.1.1

**Fixed**

- A being read a document two or three pages at a time and rarely went on: one moment of reading now takes as many passages as the engine can hold, and a book in hand pulls towards the next pages until the end (the being can still put it down).
- A pasted message longer than 8,000 characters was silently cut; it is now kept whole in the library and read like a document.

## 1.1.0

The embedded engine can be adapted by a life. Nothing in this version claims that the model learns facts, understands, or is conscious.

**Added**

- llama.cpp b12306, pinned by size and SHA-256 for Windows, Linux and macOS, fetched and checked by the application (`freewill/runtime.py`) and carried by the Windows installer.
- Qwen3 1.7B in the catalogue (Apache-2.0), its GGUF file and its trainable base pinned to a Hugging Face revision and checked by SHA-256.
- The nightly engine cycle (`freewill/learning/engine.py`, rules `h4-engine-1.2`): what was heard and answered, one item in four held out, a LoRA adapter trained beside the frozen base, kept only if it predicts held-out items better and does not forget reference texts or earlier nights, converted to GGUF, checked by llama.cpp, loaded by llama-server. Checkpoints with their weight changes, restoration, growth of the adapter under a budget. Off until a person turns it on with their name.
- The Research Lab compares the base model, the adapted model and two control adapters (EXP-09); a card "The engine this life converses with" in the "Local model" tab of the lab, in English and in French.
- End-to-end workflow on real models (`engine-e2e.yml`). Results, including what was not shown: [`docs/engine-learning.md`](docs/engine-learning.md).

**Fixed**

- The Windows installer of 1.0 shipped without `models.json`, `credits.json` and llama.cpp.
- A decision asked of an embedded model now has a ceiling on its length (SmolVLM2 once held a request for ten minutes).
- Changing engine in Settings showed the word "null" where an optional field was absent.
- When the list of embedded models could not be read, the picker stayed on "…" and the server dropped the request; the cause is now shown, with a button to try again.

## 1.0.0

The Research Lab, and the first things a life can train. Nothing in this version claims that a system is conscious or feels anything.

**Added**

- Research settings for each life: 26 switches and 7 bounded numbers, each removing or restoring one mechanism of the life loop. Every default reproduces the earlier loop; every change is written to the event log; none reaches the kernel.
- The Research Lab: versioned contracts, an append-only evidence journal, snapshot hashes, deterministic statistics that refuse small samples, a register of metrics for H1 to H10, protocols locked and hashed before they run, campaigns on isolated copies of a life under a virtual clock, observers A, B and C that read and never act, reports in Markdown and PDF with a reproduction pack, validated only by a person.
- H8, metacognition: the being predicts its own decisions, compares, and raises an alert when the way it decides has changed, without access to the cause.
- H9, sleep in phases: rest, replay, dream, consolidation, waking. Each can be removed. A sleep cut short resumes at the phase it had reached.
- H10, agency: one act per moment in a closed grid world, predicted, observed and attributed to itself or to the world. No new action in the kernel.
- H4, plasticity: a small trainable module (pure Python); Freewill's own neural network, trained during sleep on the text a being lived, kept only when it predicts unseen text better, able to add layers under a ceiling, with a way back to the previous weights (needs PyTorch); adapters beside a frozen base model (LoRA), verified on a toy base only.
- Six runnable protocols (EXP-01, 02, 03, 04, 06, 07) and their real results in `experiments/v1.0/`.
- In the application: the Research Lab, a "Learning" page, the research settings, gauges in the top bar, export of traces.
- English is the default language of the interface; French is chosen in the settings. A test fails if the two catalogues differ in keys, share an untranslated sentence or contain words of the other language.
- `docs/research/IMPLEMENTATION_STATUS.md`: what exists, what was tested, what is missing.
- The Brain view in 3D: memories and their saved links inside an illustrative brain outline, a core of translucent petals, an activity and inspection panel fed by the event log, and controls (rotate, motion, freeze view, reset). Three.js is shipped inside the package; there is a fallback without WebGL. See `docs/brain-view.md`.
- A new icon for the application, the installer and the interface.

**Changed**

- Memories are dated by the being's own clock, so that time in an experiment is the experiment's time.
- The file that lists a life's library is written atomically, and so are memory files and their indexes.
- Recall events carry the strength and state already saved; the service reports the current mode (thinking, sleeping, waiting, paused, hourly limit, retrying).
- `QUICKSTART.md` is now in English only; the French text is in `QUICKSTART.fr.md`.

**Known limits**

- The engine that thinks for a being is never trained by its life.
- Freewill's own network does not take part in thinking and grows in depth only.
- Campaigns ran on the simulated engine only. No remote model was called and no GPU was used in building or testing this version.
- EXP-05 and EXP-08 are specifications only.

## 0.3.0

H7: a computed affective state, off by default, with its protocol and results.

## 0.2.0

Library (documents, images, still frames of videos), sleep and dreams, the desktop application.
