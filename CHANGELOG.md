# Changelog

**English** · [Français](CHANGELOG.fr.md)

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
