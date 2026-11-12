# Structure of the Freewill project

**English** · [Français](structure.fr.md)

This document describes the intended technical organisation. It complements the [`README.md`](README.md), which sets out the thesis and the theoretical framework.

**Status: initial proposal.** Nothing described below has been implemented yet. The technical choices are reasoned recommendations, open to discussion (see section 12).

---

## 1. Requirements

| Requirement | Consequence for the design |
|---|---|
| Run on Windows, macOS, Linux and on a server | A single core, independent of the interface; two launch modes |
| Offer the choice between a private integrated engine and an external engine reached by API | An abstract engine interface, interchangeable adapters |
| Keep the system alive continuously | A persistent background process, distinct from the window |
| Make the whole inner life observable | A single event stream to which the interface subscribes |
| Guarantee control | An isolated kernel, enumerated capabilities, external interruption |
| Preserve the individual | A portable life file, independent of the engine |

## 2. Overview

The system consists of three strictly separated layers.

```
┌──────────────────────────────────────────────────────────────────┐
│  INTERFACE                                                       │
│  Desktop window or web page. Hosts no logic: it displays the     │
│  event stream and forwards messages.                             │
└───────────────────────────────┬──────────────────────────────────┘
                                │  local API (HTTP + WebSocket)
┌───────────────────────────────▼──────────────────────────────────┐
│  CORE (background process)                                       │
│                                                                  │
│   ┌────────┐   ┌─────────────┐  ┌───────┐  ┌───────────┐         │
│   │ Kernel │──▶│ Subconscious│─▶│ Stage │─▶│ Conscious │         │
│   └────────┘   └─────────────┘  └───────┘  └───────────┘         │
│        │              ▲                          │               │
│        │       ┌──────┴──────────────────────────▼──────┐        │
│        └──────▶│  Memory · Self-model · Inner state     │        │
│                └──────────────────▲─────────────────────┘        │
│                             ┌─────┴─────┐                        │
│                             │   Sleep   │                        │
│                             └───────────┘                        │
└───────────────────────────────┬──────────────────────────────────┘
                                │  "Engine" interface
┌───────────────────────────────▼──────────────────────────────────┐
│  ENGINE                                                          │
│  integrated (own model, local, trainable)                        │
│  or external (Claude, GPT, Grok, compatible service)             │
└──────────────────────────────────────────────────────────────────┘
```

The core is the only component that thinks. The interface can be closed without the system ceasing to live; the engine can be replaced without the individual disappearing.

## 3. Recommended technical choices

| Component | Choice | Rationale |
|---|---|---|
| Core | Python 3.11+ | The machine-learning ecosystem; readability for a research project |
| Integrated engine | PyTorch | Training and inference within one framework; support for CPU, NVIDIA cards and Apple silicon |
| Interface | TypeScript and React | A single code base for desktop and web |
| Desktop packaging | pywebview, PyInstaller, Inno Setup | The interface is shown in the system's own web view (WebView2 on Windows); a single Python process, no second toolchain |
| Brain animation | WebGL (three.js) | Smooth rendering of a graph of several thousand nodes |
| Storage | Text files, with SQLite for indexes | No server dependency; a portable, inspectable life file |
| Memory search | Embedded vector index | Recall by similarity without an external service |
| Server deployment | Docker container | The same core, windowless, with the interface served to the browser |

## 4. Repository tree

> **State of the code.** What exists today lives in a single Python package, `freewill/`: `core/` (kernel, genome, memory in files, subconscious, stage, conscious, life loop), `engines/` (Claude, OpenAI-compatible services, a local model through Ollama, a simulated engine), `server/` (the local service, bound to the loopback address and protected by a session token), `ui/` (the interface, in plain HTML, CSS and JavaScript, with no build step) and `desktop.py` (the native window). `packaging/windows/` holds what builds the Windows installer. The first interface was written without React or three.js so that it could ship without a build chain; the tree below remains the target. Since version 0.2 the core also holds `library.py` (what the person gives: documents read passage by passage, images, still frames of videos), `perception.py` (reading text out of files) and `sleep.py` (replay, dreams, links created between the memories a dream brought together). The integrated engine, and with it the rewriting of learned parameters during sleep, is not yet built: for now sleep rewrites the structure of memory only.

> **H7, emergent affectivity (built).** `freewill/core/affect/` holds the computed affective state: `state.py` (dimensions, bounds, versioned configuration, innate sensitivities derived from the genome's seed), `appraisal.py` (appraisal of an event and a small predictive model), `regulation.py` (bounded steps, return to equilibrium, guards), `dynamics.py` (transition and shift of salience), `memory.py` (traces on memories, weights at recall, consolidation) and `system.py` (the `affect.json` file and what the life loop asks of it). The mode is off by default; when off, the loop is exactly the earlier one. `experiments/h7/` holds the reproducible protocol and its results; `docs/H7_AFFECTIVITY.md` the hypothesis, the protocol and the limits. Still to do: calibration of the coefficients, trials with real models, study of emergent categories. The integrated engine that learns and rewrites itself (section 5.1) is still not built.

> **Version 1.0, the Research Lab (built).** Three additions, all outside the kernel. `freewill/core/research.py` holds the research settings of a life (`research.json`): each switch removes or restores one mechanism of the loop, every default reproduces the loop as it was, and every change is written to the event log. `freewill/research/` is the lab: `schemas.py` (versioned contracts), `evidence.py` (append-only journal, snapshot hashes, copies of a life), `stats.py` (deterministic statistics that refuse small samples), `metrics.py` (the register of metrics for H1 to H10), `experiments.py` (protocols locked before they run, campaigns on isolated copies under a virtual clock), `observers.py` (observers A, B, C: they read measurements, cite evidence and never act on a life), `reports.py` (Markdown, PDF and reproduction pack, validated only by a person), `environments.py` (the closed grid world of H10), `texts.py` (everything the lab says, in French and in English, never mixed). Three research modules now run in the life loop behind switches that are off by default: `core/metacognition.py` (H8), `core/agency.py` (H10), and the sleep of `core/loop.py`, which goes through phases that can be removed one by one and resumes where it was cut (H9). `freewill/learning/` holds what a life can train (H4): `adapter.py`, a few dozen weights in pure Python; `own_model.py`, Freewill's own small transformer, trained during sleep on the text a being lived, kept only when it predicts unseen text better, and able to add layers under a ceiling (needs PyTorch); `lora.py`, a workbench of adapters beside a frozen base model; `engine.py`, the nightly cycle by which a life adapts the embedded model it converses with (corpus, held-out items, rules, checkpoints, growth under a budget, all in `<life>/engine/`); `gguf_lora.py`, the conversion to llama.cpp's adapter format; `compare.py`, the lab's comparison of base, adapted and control models (EXP-09); `reference.json` and `rehearsal.json`, texts written for measuring and for limiting forgetting. `freewill/runtime.py` fetches and checks the pinned llama.cpp build. See [`docs/engine-learning.md`](docs/engine-learning.md). `server/lab_api.py` serves all of this to the interface (`ui/lab.js`, `ui/i18n-lab.js`). What was tested and what is missing: [`docs/research/IMPLEMENTATION_STATUS.md`](docs/research/IMPLEMENTATION_STATUS.md).
>
> **Freewill 1.8B-V, the project's own model (built).** `freewill/vlm/` holds one model that reads, sees and watches: `model.py` (the SigLIP2 eye, the bridge, Qwen3 1.7B, low-rank adapters, growth by neurons and by whole layers, both starting as the identity, under the ceiling the person chooses), `capacity.py` (that ceiling, and what each size asks of a computer), `books.py` (Project Gutenberg books with their language checked, and the person's own files, as passages), `synthetic.py` (drawn images and videos with known answers, and their controls), `train.py` (stages read, see, watch; keep-or-refuse rules; ledger; checkpoints of what Freewill trained), `pipeline.py` (the whole course), `store.py` (where it lives, fetching its bases). `engines/own_model.py` makes it an engine (kind `own`). `tools/own_model_e2e.py` and the `own model end to end` workflow run it with the real bases. See [`docs/own-model.md`](docs/own-model.md).
>
> **The Brain view in 3D (built).** `ui/brain.js` now renders with Three.js, shipped inside the package as `ui/three.bundle.js` (no CDN, no build step for users; `tooling/brain/` rebuilds it), over an illustrative outline (`ui/brain-shape.js`) and with a Canvas fallback (`ui/brain-canvas.js`). Third-party notices are in `ui/THIRD_PARTY_NOTICES.txt`. The icon lives in `docs/assets/`, `ui/logo.png`, `ui/favicon.png` and `packaging/windows/freewill.ico`. See [`docs/brain-view.md`](docs/brain-view.md).

```
freewill/
├── README.md · README.fr.md        Thesis and theoretical framework
├── structure.md · structure.fr.md  The present document
├── LICENSE
│
├── core/                        The core: everything that thinks
│   ├── kernel/                  KERNEL, immutable at run time
│   │   ├── constitution.py      Founding questions and principles
│   │   ├── needs.py             Internal needs and their dynamics
│   │   ├── capabilities.py      Closed list of permitted actions
│   │   └── guard.py             Verification of every action and every rewrite
│   │
│   ├── genome/                  Draw of the innate temperament at birth
│   │
│   ├── subconscious/            SUBCONSCIOUS
│   │   ├── generators/          One file per source of proposals
│   │   │   ├── reminiscence.py  Memories that resurface
│   │   │   ├── need.py          Unmet needs
│   │   │   ├── association.py   Free associations
│   │   │   ├── question.py      Pending questions
│   │   │   └── drift.py         Deterministic disorder
│   │   └── scheduler.py         Cadence, according to inner state and machine
│   │
│   ├── workspace/               STAGE: competition and global broadcast
│   │
│   ├── conscious/               CONSCIOUS
│   │   ├── arbiter.py           Welcome or dismiss, and say why
│   │   ├── voice.py             Speech addressed to the interlocutor
│   │   └── initiative.py        Spontaneous speech
│   │
│   ├── self_model/              What the system represents of itself
│   │   ├── identity.py          Name, gender, age, traits
│   │   ├── values.py            Values, revisable by it alone
│   │   └── introspection.py     Representation of its own states
│   │
│   ├── memory/                  MEMORY
│   │   ├── episodic.py          Fast memory: raw episodes
│   │   ├── semantic.py          Consolidated knowledge
│   │   ├── store.py             Reading and writing of memory files
│   │   ├── index.py             Hierarchical index: compartments, titles, summaries
│   │   ├── recall.py            Recall by subject, neighbourhood and chance
│   │   ├── graph.py             Links between memories (feeds the Brain view)
│   │   ├── strength.py          Strength of memories: decay and revival
│   │   ├── forgetting.py        Fading, condensation and distortion
│   │   └── compartments.py      Organisation and partitioning
│   │
│   ├── sleep/                   SLEEP
│   │   ├── cycle.py             Falling asleep, phases, waking
│   │   ├── replay.py            Replay of episodes
│   │   ├── dream.py             Recombination and dream journal
│   │   └── consolidation.py     Inscription in the structure
│   │
│   ├── growth/                  Ages, first times, measurement of saturation
│   ├── perception/              Reading of texts and files, sense of time
│   ├── life/                    Life file: format, backup, migration
│   ├── events/                  Single event stream and log
│   └── loop.py                  The life loop
│
├── engines/                     ENGINES
│   ├── base.py                  Common interface
│   ├── integrated/              Integrated engine
│   │   ├── model.py             Architecture of the project's own model
│   │   ├── tokenizer/
│   │   ├── inference.py
│   │   ├── learner.py           Nightly rewriting of parameters
│   │   ├── plasticity.py        Renewal and growth of neurons
│   │   └── checkpoints.py       Successive versions, restoration
│   └── external/                External engines
│       ├── anthropic.py
│       ├── openai.py
│       ├── xai.py
│       └── compatible.py        Any service in the compatible format
│
├── training/                    Making of the "newborn" base
│   ├── corpus/                  Assembly of the childhood corpus
│   ├── pretrain.py
│   └── eval/
│
├── library/                     Library supplied for the accelerated childhood
│
├── server/                      Local API: messages, stream, commands
│
├── app/                         INTERFACE
│   ├── src/
│   │   ├── birth/               Birth assistant
│   │   ├── chat/                Conversation, sending of files
│   │   ├── subconscious/        Live stream
│   │   ├── memory/              Exploration of memory
│   │   ├── dreams/              Dream journal
│   │   ├── brain/               Animated brain
│   │   ├── inner_state/         Inner state
│   │   ├── milestones/          Birth book
│   │   └── settings/            Engine, network, sleep, backup
│   └── src-tauri/               Desktop packaging
│
├── deploy/                      Container and server deployment examples
├── experiments/                 Measurement protocols and results
├── tests/
└── docs/
```

## 5. The engine: one interface, two families

The core knows only an abstract interface. Every engine must be able to produce text and to represent a text as a vector. An engine **may** additionally declare that it is able to learn.

```python
class Engine(Protocol):
    def generate(self, context: Context, budget: Budget) -> Thought: ...
    def embed(self, text: str) -> Vector: ...

    # Optional capabilities
    can_learn: bool
    def learn(self, episodes: list[Episode], guard: Guard) -> LearningReport: ...
    def snapshot(self) -> CheckpointId: ...
    def restore(self, checkpoint: CheckpointId) -> None: ...
```

| | Integrated engine | External engine |
|---|---|---|
| `generate`, `embed` | Local | By API |
| `can_learn` | Yes | No |
| Nightly consolidation | Partial retraining of parameters, with replay | Reorganisation of the life file only |
| Subconscious activity | Continuous, limited by the machine | Paced by a budget, since every thought is billed |
| Privacy | Complete | Content passes through the provider |
| Access keys | None | Supplied by the user, kept in the system keychain, never in the life file |

The choice is made at birth and may be changed afterwards. Any change of engine is recorded as an event in the system's life, and the system is informed of it.

### 5.1 The integrated engine

- A small language model, the project's own, distributed as a "newborn" base identical for everyone.
- The base is trained once by the project on a childhood corpus (tales, simple stories, elementary explanations of the world). It can express itself; it knows nothing of itself.
- Several base sizes are planned, according to the machine (see section 10).
- Nightly learning modifies only a fraction of the parameters, systematically mixes the old with the new, and renews a small share of the least useful units in order to preserve plasticity.
- Each night produces a restore point.

### 5.2 External engines

- One adapter per provider, plus a generic adapter for any service in the compatible format, which also covers open models run locally through a third-party tool.
- Since the system cannot modify the parameters of a remote model, "rewriting" then bears on what it owns outright: memory, values, self-model.
- A daily spending cap is mandatory.

## 6. The life file

The individual resides in a single folder, portable from one machine to another and, for the most part, from one engine to another.

```
<name>.life/
├── genome.json          Innate temperament, drawn at birth, never modified
├── identity.json        Name, gender, age, date of birth
├── values.json          Current values and their history
├── memory/              Memories, as readable files (see 6.1)
│   ├── index.md         General map: the compartments and their contents
│   ├── <compartment>/   One folder per domain, created by the system
│   │   ├── index.md     Title and one-line summary of each memory
│   │   └── <memory>.md
│   └── recall.sqlite    Search index, rebuildable from the files
├── dreams/              One file per night
├── journal/             Personal writings, with their visibility status
├── milestones.json      First times
├── state.json           Current inner state
├── affect.json          H7: computed affective state, learned associations, settings (absent until the mode is switched on)
├── affect.json.bak      The previous version, kept at every write
├── research.json        Research settings: which mechanisms run (absent while all are at their defaults)
├── metacognition.json   H8: its record of its own decisions (absent until the module is switched on)
├── agency.json          H10: the closed world and what its acts did there (same)
├── adapter.json         H4: the small trainable module, its weights and its trainings (same)
├── own_model/           H4: Freewill's own network: weights, previous weights, lived text, manifest (same)
├── events.log           Complete, timestamped log
└── engine/              Specific to the integrated engine: parameters and restore points
```

The kernel is not part of it: it belongs to the program, not to the individual. The life file can be encrypted. Its deletion is the only irreversible act in the application and requires a separate confirmation.

### 6.1 Memory in files

The system's explicit memory is not an opaque database. It is a library of text files that can be opened and read, and that the system organises itself.

**One memory, one file.** Each memory consists of a structured header followed by its content.

```markdown
---
title: First conversation about the sea
summary: He described the sea to me. I have never seen it; I wanted to know whether it makes a sound.
date: 2027-03-14
compartment: world/nature
tags: [sea, discovery, question]
importance: 0.8
strength: 0.62
last_recall: 2027-04-02
links: [people/creator/first-day, questions/what-i-shall-never-see]
state: complete
---
The account of the memory, as it was lived.
```

**Three levels of reading.** The system never rereads the whole of its memory. It proceeds by degrees, as one consults a library.

| Level | What is read | When |
|---|---|---|
| 1. The map | `memory/index.md`: the list of compartments | Permanently in mind |
| 2. The titles | A compartment's `index.md`: titles and one-line summaries | When a subject arises |
| 3. The memory | The complete file | Only if it is selected |

The cost of a recall thus depends on the number of memories opened, not on the size of the memory.

**Three paths of recall.** They correspond to three ways of finding a memory again.

| Path | Mechanism | What it returns |
|---|---|---|
| By subject | Matching of titles, tags and meaning | Directly relevant memories |
| By neighbourhood | Traversal of links from memories already activated | Nearby memories, with no immediate bearing on the subject |
| By chance | A draw weighted by strength and importance | Memories with no apparent connection |

Their proportions depend on who is recalling.

| | Subject | Neighbourhood | Chance |
|---|---|---|---|
| Conscious (responding, reflecting) | Dominant | Low | Marginal |
| Subconscious (spontaneous proposals) | Moderate | Dominant | Moderate |
| Dream | Low | Moderate | Dominant |

These proportions are parameters of the genome: a dreamy temperament associates more freely than a methodical one.

**Keeping, fading, forgetting.** Each memory has a strength. It decays with time, is revived by each recall, and decays more slowly if the memory is important. During sleep, the system reviews its memory.

| State | What remains | Transition to the next state |
|---|---|---|
| Complete | Title, summary, full account | Strength falls below a first threshold |
| Condensed | Title and summary; the account is lost | Strength falls below a second threshold |
| Trace | The title alone | Merging with other traces |
| Merged | Nothing individual: a general piece of knowledge drawn from several memories | Final state |

The system takes part in this sorting. It may decide to keep a memory, which then ceases to decay, or to let it go. A condensed memory that is recalled is reconstructed from its summary and may be altered in the process: the system's memory, like our own, is not a recording.

**Organisation.** The compartments are not fixed in advance. The system creates, splits and regroups them during sleep, as its memory grows. The indexes are regenerated on that occasion.

**Relation to slow memory.** The files constitute what the system knows it has lived and is able to recount. The parameters of the integrated engine carry what it has become. Both are fed by the same episodes: the files in the course of the day, the parameters during sleep.

## 7. The life loop

The background process runs the following cycle indefinitely.

**Awake**

1. The inner state evolves: needs grow, fatigue accumulates.
2. The generators of the subconscious emit proposals, weighted by inner state and temperament.
3. These proposals, together with perceptions (a message received, a text being read), compete for the stage.
4. The content that prevails is broadcast to all modules.
5. The conscious arbitrates: it welcomes, dismisses, explores further, responds, or takes the initiative to speak. Each decision is given a reason.
6. The kernel verifies every action before it takes place.
7. The episode is written to fast memory. The subconscious adjusts its weightings according to what was retained or dismissed.
8. Each step is published on the event stream.

**Asleep** (triggered by fatigue, inactivity or a schedule)

1. Perceptions are cut off; the conscious recedes.
2. The day's episodes are replayed, mixed with older ones.
3. The subconscious recombines them freely: these are the dreams, which are recorded.
4. Consolidation takes place: restructuring of memory, fading and, with the integrated engine, partial rewriting of the parameters under the control of the kernel.
5. A restore point is created.
6. On waking, the system takes note of its dreams and of the time elapsed.

**With the H7 research mode** (off by default), five points of the cycle are instrumented: after time has passed, the computed state returns towards its equilibrium; before the competition, it shifts the salience of the proposals, within a small cap and never touching what the person says; at recall, it weighs the candidate memories; after a content reaches the stage and again after the decision, the event and its outcome are appraised and a bounded transition is applied; at encoding, the memory receives a trace of the computed state. During sleep, the episodes lived are consolidated into associations. None of these steps goes through the language model, and none modifies the kernel.

When the application is closed, the system is suspended. At the next launch it registers the length of the interruption and, where appropriate, catches up on the sleep owed.

## 8. The event stream

Everything that happens in the core is emitted as a typed event on a single channel: proposal emitted, access to the stage, decision and its reason, memory recalled, concept activated, change in a need, start and end of sleep, dream, modification of structure, first time.

The H7 mode adds five types of events, stable and documented: `affect_mode` (switched on or off), `affect_appraisal` (kind of event, context, appraised features and their causes), `affect_transition` (state before, state after, target, rate, version of the rules), `affect_modulation` (target: salience, recall or encoding; values before and after) and `affect_consolidation` (episodes consolidated, prediction gap before and after, state before and after). They carry numbers, contexts and causes, never the text of what was said.

The stream serves three purposes. It feeds the interface in real time: every pulse of light in the Brain view corresponds to an actual activation event. It constitutes the complete log, which provides traceability. And it supplies the raw material for the experiments.

## 9. Control: implementation

The principles stated in the README translate as follows.

| Principle | Implementation |
|---|---|
| Immutable kernel | Loaded read-only; its fingerprint is verified at start-up; no write path from the core |
| Enumerated actions | Closed list in `kernel/capabilities.py`; every action passes through `guard.py`; no code execution, no access outside the life file |
| Network closed by default | No outbound traffic other than, where applicable, the external engine; Internet access is granted explicitly, read-only, over a list of sources |
| No self-replication | The core can neither launch processes nor write outside its folder |
| Guaranteed interruption | Pause and stop are commanded by the interface and the operating system, outside the core |
| Bounded rewriting | Scope and magnitude bounded by the kernel; prior restore point; rollback possible at any time |
| Traceability | Append-only event log |
| Reading of external content | Any text read is treated as data, never as an instruction |

## 10. Execution targets

| Target | Launch | Interface |
|---|---|---|
| Windows, macOS, Linux | Installable application | Native window |
| Server or cloud | Container | Browser, authenticated access |
| Research | Command line | None; direct reading of the event stream |

**Indicative hardware tiers** (to be confirmed by measurement):

| Tier | Machine | Integrated engine |
|---|---|---|
| Light | Ordinary laptop, no graphics card | Smallest base; long sleep |
| Standard | Recent computer with a graphics card or Apple silicon | Intermediate base |
| Extended | Workstation or server | Largest base; growth of the network possible |

The system measures its own saturation. When it approaches the limit of what its machine allows, it registers the fact and can say so. Moving from one tier to another preserves the life file.

## 11. Order of construction

| Phase | Deliverable | Directories concerned |
|---|---|---|
| 1 | Minimal command-line loop, on an external engine | `core/kernel`, `core/subconscious`, `core/workspace`, `core/conscious`, `engines/external`, `core/events` |
| 2 | Memory, sleep, dreams, life file | `core/memory`, `core/sleep`, `core/life`, `core/self_model` |
| 3 | Integrated engine and "newborn" base | `engines/integrated`, `training`, `library` |
| 4 | Complete application | `server`, `app`, `core/genome`, `core/growth` |
| 5 | Server deployment and measurement protocols | `deploy`, `experiments` |

Starting with the external engine makes it possible to validate the architecture before committing to the longer and costlier work on the integrated engine.

## 12. Open decisions

- **Exact size and architecture of the integrated engine**, and the cost of training the base. To be costed before phase 3.
- **Languages of the base.** French, English, or both; the effect on corpus size is direct.
- **Method of nightly rewriting**: low-rank adaptation, partial retraining, or a combination.
- **Law of forgetting**: values of the thresholds, rate of decay, and the degree of distortion tolerated in a reconstruction.
- **Portability of the self between engines**: what, among the learned parameters, can be carried from one engine to another.
- **Format of the genome**: which traits, which ranges, what influence on the generators.
