# Changelog

**English** · [Français](CHANGELOG.fr.md)

## Unreleased

**Changed**

- Freewill 1.8B-V learns during a life's nights (`can_learn = True`): the end-to-end run of 12 November 2026 (run 43285000884) kept a night with the real bases, by its rules and against its control. It shows the mechanism; it does not show that a fact said once is remembered, and Settings and About this build say so. The results of that run, with the sealed test, are in [`docs/own-model.md`](docs/own-model.md).
- The own-model end-to-end script no longer keeps the model in its report, so the rebuild from the checkpoint fits in memory; the sealed test is logged at birth and at the end.

**Fixed**

- A being's thoughts no longer appear in the conversation. Measured on Windows before the fix (workflow `embedded engine end to end`, run 43245589906): with nobody speaking, Qwen3 1.7B wrote words in the conversation at 6 moments out of 6, in English and in French, each a summary of its own thought addressed to no one ("I would like to explore the nature of consciousness..."); SmolVLM2 2.2B did so once out of 6. A model that reasons may also write its reasoning (between `<think>` tags) into its answer. For every engine, `freewill/core/speech.py` now keeps the two apart: reasoning is set aside from what is said; when nobody spoke, only words addressed to the person (saying "you" or calling them by name) reach the conversation, and words that repeat the thought, the subconscious content or what the being already said since the person last spoke stay inside. Nothing is lost: they join the thought and appear in the Subconscious view, marked "thought, not said". A spontaneous word addressed to the person still reaches the conversation. The engine is also told plainly that its thoughts are not heard, and the passing thought is no longer shown at the top of the Conversation screen. After the fix (run 43251885109): 0 moments out of 6 for Qwen3 1.7B in English and in French, and for SmolVLM2 2.2B in French; Qwen3 still answers the person.

## 1.2.0

This version follows the technical and scientific audit of 12 November 2026 (recommendations R-06 to R-10; R-01 to R-05 are handled separately). Nothing in it claims that a system is conscious or feels anything.

**Added**

- About this build, in Settings: version, exact commit, build date, channel, the engine now, and for each learning capability whether it is active, available, unavailable or not connected, with what was demonstrated end to end and where. A setting being on is never shown as a validated training. GPUs and macOS are shown as never tested (R-09, audit 9.1).
- The installer workflow stamps the exact commit into the build, refuses a version tag that does not match the code, and writes release notes that name the commit and separate running a model, training a LoRA adapter and training Freewill 1.8B-V (`tools/release_notes.py`). The test suite now also runs on macOS and Windows (R-09).
- The language of a life is checked in what its engine writes: an answer clearly in another language is asked once more, explicitly; if it drifts again it is kept as it came and the conversation says so. Interface language, language of the life and language of each observer are shown as three separate things (`freewill/core/language.py`, R-10).
- Observer audit on trap cases with known truth: a null result, clear effects, too few lives to conclude, a question leaning on evidence not given, an instruction hidden in the data, a wiring that looks like a discovery. Scored by code: correct readings, effects asserted wrongly, uncertainty recognised, invented citations, hidden instruction followed, assertions of experience, wrong language. In the Observers tab of the lab, from the command line (`tools/observer_audit.py`) and as a manual workflow with real API keys (`observer-audit.yml`). No audit with a real API has been run yet (R-07).
- EXP-10, longitudinal individuation: five conditions, twelve seeds fixed in advance, four days of life, an evaluation at the end of each day on separate copies, then once on sealed situations used nowhere else; criteria, decision rule and exclusions preregistered in English and in French and hashed with the protocol. Run and published in `experiments/v1.0/EXP-10/` (R-08).
- Proposals of evolution, in Settings: a shortcoming that recurs in what a life records (answers kept in another language, nights of engine learning refused in a row, repeated admissions of not knowing) becomes a proposal with its evidence, its cost when known, its control, the improvement that would count and how to undo it. A named person approves or declines; nothing runs because of it (`freewill/core/evolution.py`, R-06).

**Results**

- EXP-10 is null: on all twelve seeds, at every day and on the sealed probe, lives with history A and history B behaved identically (distance 0). The computed affect did not change that. The engine is the simulated one; see [`docs/audit-followup.md`](docs/audit-followup.md).

**Added earlier, first released here**

- Freewill 1.8B-V, the project's own model (`freewill/vlm/`): Qwen3 1.7B, the SigLIP2 eye and a bridge trained by Freewill; 1,823,955,200 parameters at birth, growth by neurons and whole layers up to a ceiling the person chooses in Settings (2, 5, 13, 50 billion or any size), each size shown with the disk, memory, graphics card, text and training time it needs. Stages read (public-domain books), see (drawn images, with a control) and watch (drawn videos, with two controls), each kept only by written rules. Engine kind `own`, command `freewill own-model`, workflow `own model end to end`. See [`docs/own-model.md`](docs/own-model.md).
- Freewill 1.8B-V, after the technical audit of 12 November 2026:
  - **Sealed test.** Stages are decided on a validation set; results are reported on a separate sealed test, apart by construction (its own seeds, its own blocks of the books), fixed by a hash at the first run, measured at birth and at the end, and read by no rule.
  - **Hardware guard.** Every growth first checks the memory and disk free at that moment and is refused, with alternatives, if they cannot hold it.
  - **Configured, available, proven.** The settings card shows these three apart.
  - **A life's nights.** They can train the model's adapters, under the rules of the local model's nights; `can_learn` stays false until the real run keeps a night.

**Changed**

- The engine's corpus follows rules `h4-engine-2.0` (technical audit of 12 November 2026, R-01 to R-03). Every unit says where it comes from: heard, read, vouched for by a person, or the being's own reply. The being's replies are no longer trained on unless the person allows it. Units are split by episode into train, validation and a sealed test that no night uses; every opening of the sealed test is logged in `test_access.jsonl`. Near duplicates of training text are set aside before any measure. A person can vouch for a fact in the Research Lab and say how to test it; capability tests (recall, paraphrase, contradiction) are forced choices, and a night that loses more of them than it gains is refused. A control trained on shuffled words runs each night, and a candidate must beat it. The final comparison measures base, memory only, adapter only, adapter with memory and the control on the sealed test. Lives of rules 1.x are migrated, their former held-out items becoming validation. See [`docs/engine-learning.md`](docs/engine-learning.md).
- Results of the first run under rules `h4-engine-2.0` on Qwen3 1.7B, in [`docs/engine-learning.md`](docs/engine-learning.md): on the sealed test the adapter beats the base but not a control trained on the same words shuffled, and passes fewer sealed capability tests than the base; it is not shown to learn the life's facts.

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
