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
| Desktop packaging | Tauri | Lightweight executables for all three systems; the Python core is bundled as a sidecar process |
| Brain animation | WebGL (three.js) | Smooth rendering of a graph of several thousand nodes |
| Storage | SQLite and files | No server dependency; a portable, inspectable life file |
| Memory search | Embedded vector index | Recall by similarity without an external service |
| Server deployment | Docker container | The same core, windowless, with the interface served to the browser |

## 4. Repository tree

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
│   │   ├── graph.py             Concept graph (feeds the Brain view)
│   │   ├── forgetting.py        Fading and distortion
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
├── memory.sqlite        Episodes, knowledge, concept graph
├── dreams/              One file per night
├── journal/             Personal writings, with their visibility status
├── milestones.json      First times
├── state.json           Current inner state
├── events.log           Complete, timestamped log
└── engine/              Specific to the integrated engine: parameters and restore points
```

The kernel is not part of it: it belongs to the program, not to the individual. The life file can be encrypted. Its deletion is the only irreversible act in the application and requires a separate confirmation.

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

When the application is closed, the system is suspended. At the next launch it registers the length of the interruption and, where appropriate, catches up on the sleep owed.

## 8. The event stream

Everything that happens in the core is emitted as a typed event on a single channel: proposal emitted, access to the stage, decision and its reason, memory recalled, concept activated, change in a need, start and end of sleep, dream, modification of structure, first time.

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
- **Law of forgetting**: what fades, at what rate, and what becomes distorted.
- **Portability of the self between engines**: what, among the learned parameters, can be carried from one engine to another.
- **Tauri or Electron** for packaging, depending on how readily the Python core can be bundled on all three systems.
- **Format of the genome**: which traits, which ranges, what influence on the generators.
