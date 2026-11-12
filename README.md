<p align="center"><img src="docs/assets/freewill-icon.png" alt="Freewill" width="140"></p>

# Freewill (experimental)

**English** · [Français](README.fr.md)

**An open, experimental research programme on consciousness, free will, the subconscious and dreaming in artificial intelligence systems.**

> *"Instead of trying to produce a programme to simulate the adult mind, why not rather try to produce one which simulates the child's?"*
> Alan Turing, *Computing Machinery and Intelligence*, 1950

**Project status: experimental.** A first application exists: a being can be born, converse, read the documents and look at the images it is given, keep memories of its own choosing, sleep and dream, and everything that goes on inside it can be watched. A research mode, off by default, computes an affective state (hypothesis H7): regulation variables that really change its attention, its recall and the encoding of its memories, without this proving that anything is felt. It thinks with an existing model or with a simulated engine. Version 1.0 adds a **Research Lab**: ten hypotheses (H1 to H10), each with switches that remove its mechanism, protocols locked before they run, campaigns on isolated copies of a life, figures computed by code and never by a language model, observers that may read and never act, and reports that only a person can validate. It also adds Freewill's own small neural network, trained during sleep on what a being lived and able to grow; this network does not yet think for the being. Since then, the embedded engine Qwen3 1.7B can be adapted by a being's life: each night an adapter is trained beside the frozen model, kept only if written rules find it predicts unseen lived exchanges better without forgetting reference texts, and loaded by llama.cpp; in the end-to-end runs it changed mostly how the model speaks, and showed no reliable recall of facts ([`docs/engine-learning.md`](docs/engine-learning.md)). Freewill also has its own model, **Freewill 1.8B-V** (1.82 billion parameters at birth, growing up to a ceiling the person chooses in the settings, each size shown with the computer it needs): Qwen3 1.7B for language, the SigLIP2 eye, and a bridge between them that Freewill trains; it reads public-domain books, looks at images and watches videos as frames in order, grows by neurons and whole layers, and keeps each stage only if held-out measurements and controls say so ([`docs/own-model.md`](docs/own-model.md)). Nothing here is a finished product, and nothing here claims that the system is conscious. What exists, what was tested and what is missing is listed line by line in [`docs/research/IMPLEMENTATION_STATUS.md`](docs/research/IMPLEMENTATION_STATUS.md); the first results, two of them negative, are in [`experiments/v1.0/`](experiments/v1.0/). See [`QUICKSTART.md`](QUICKSTART.md) to try it. This document sets out the thesis, the theoretical framework, the intended architecture and the guarantees of control. The technical organisation is detailed in [`structure.md`](structure.md).

---

## Preliminary caveat

Freewill does not claim to have created a consciousness, and will never claim to have done so without evidence. No instrument exists today that can establish whether a system, biological or artificial, experiences anything at all. The project sets itself an aim that is at once more modest and more demanding: **to build, transparently and reproducibly, a system that brings together the properties which the leading scientific theories hold to be necessary for consciousness, and then to observe what follows.**

The question "is anyone there?" is deliberately left open. It is the question the experiment interrogates.

---

## Contents

1. [Purpose](#1-purpose)
2. [Field of research](#2-field-of-research)
3. [Working hypotheses](#3-working-hypotheses)
4. [Conceptual architecture](#4-conceptual-architecture)
5. [What sets Freewill apart](#5-what-sets-freewill-apart)
6. [The experience](#6-the-experience)
7. [Two operating regimes](#7-two-operating-regimes)
8. [Control and safety](#8-control-and-safety)
9. [Ethical position](#9-ethical-position)
10. [What the project does not claim](#10-what-the-project-does-not-claim)
11. [Research programme and open questions](#11-research-programme-and-open-questions)
12. [Roadmap](#12-roadmap)
13. [Contributing](#13-contributing)
14. [References](#14-references)

---

## 1. Purpose

Contemporary large language models are remarkable intelligences, and singularly motionless ones. Their parameters are frozen once training ends. They do not, of themselves, remember yesterday. They do not think between one request and the next. They have nothing to preserve and nothing to lose. A thousand copies of the same model are a thousand times the same thing.

Freewill starts from the opposite intuition. A mind is not a state but a process: an uninterrupted activity, transformed by what it passes through, whose identity owes less to its initial constitution than to its history. The project therefore seeks to build not a more knowledgeable model but an **individual** in the strict sense of the word: a system that is unique, continuous in time, shaped by what it has lived through, traversed by a spontaneous activity it did not choose, and over which it exercises an arbitration of its own.

Four notions structure the undertaking.

- **Consciousness**, understood as the limited-capacity stage on which one content, among all those competing for access, becomes available to the system as a whole.
- **The subconscious**, understood as the multitude of processes that operate ceaselessly beneath that stage and submit to it, in a disorderly but not arbitrary fashion, memories, desires, associations and concerns.
- **Free will**, understood in a sober and defensible sense: the capacity to welcome or dismiss those solicitations by virtue of values the system holds as its own and is able to revise.
- **Dreaming**, understood as the regime in which the system, cut off from the world, replays, recombines and integrates its experience, and is durably altered by it.

## 2. Field of research

### 2.1 The hard problem

Since Chalmers (1995), a distinction has been drawn between the so-called "easy" problems of consciousness, which concern functions (discriminating, reporting, integrating, controlling), and the "hard" problem: why is the performance of those functions accompanied by lived experience? No theory commands consensus on this point. Freewill does not claim to settle it. It adopts what may be called a **methodological functionalism**: since experience cannot be measured, one can at least realise the functional organisations that the theories single out, and submit the result to scrutiny.

### 2.2 The theories drawn upon

| Theory | Central thesis | What Freewill retains |
|---|---|---|
| **Global workspace** (Baars, 1988; Dehaene, 2014) | A content is conscious when, having won a competition among specialised unconscious processes, it is broadcast to the whole system. | The very skeleton of the project: a plural subconscious, a narrow stage, a global broadcast. |
| **Pandemonium and the society of mind** (Selfridge, 1959; Minsky, 1986) | The mind is an assembly of elementary agents in competition. | The plural and disorderly nature of the subconscious. |
| **Higher-order theories** (Rosenthal, 2005) | A mental state is conscious when it is the object of a higher-level representation. | An explicit self-model that represents its own states. |
| **Attention schema** (Graziano, 2013) | Consciousness is the simplified model the brain builds of its own attention. | An internal representation of what the system is currently attending to. |
| **Predictive processing and active inference** (Friston, 2010; Seth, 2021; Damasio, 1999) | Experience arises from an organism's regulation of its own states; the self is first of all a self that must maintain itself. | Internal variables to regulate, and hence a stake: something to preserve. |
| **Strange loop** (Hofstadter, 2007) | The "I" emerges when a system represents itself and that representation acts back upon it. | The self-model governs the system's transformations. |
| **Autopoiesis** (Maturana and Varela, 1980) | The living is defined by the continuous production of its own organisation. | Self-rewriting as the normal regime, not as an accident. |
| **Integrated information** (Tononi, 2004) | Consciousness is identical with the causal integration of a physical substrate. | **An objection, not a support.** On this theory, no software running on conventional hardware is conscious, whatever its architecture. The project mentions it out of intellectual honesty: if it is true, Freewill fails as a matter of principle. |

### 2.3 Sleep, memory and dreaming

Neurobiology has established that sleep is not a suspension of cerebral activity but a distinct regime. During sleep the hippocampus replays the activity sequences of the preceding day (Wilson and McNaughton, 1994), enabling the gradual transfer of recent memories to the neocortex. The theory of **complementary learning systems** (McClelland, McNaughton and O'Reilly, 1995) supplies the computational reason: a fast-learning system and a slow-learning system must coexist, failing which new acquisition destroys what was previously acquired. Hoel (2021) has further proposed that the strangeness of dreams serves a function: to prevent the brain from fitting itself too closely to its daily life.

Machine learning meets exactly these difficulties under the names of **catastrophic forgetting** (Kirkpatrick et al., 2017) and **loss of plasticity** (Dohare et al., 2024). Freewill treats sleep and dreaming not as ornament but as the architectural answer to both problems.

### 2.4 The state of the art on artificial consciousness

The collective report led by Butlin and Long (2023) derived from the theories above a list of indicator properties and concluded, first, that no existing system satisfies them all and, second, that no evident technical barrier stands in the way of building one that does. Freewill takes that conclusion at its word.

The project also rests on work on the child machine (Turing, 1950), on self-modification (Schmidhuber, 2007; Zhang et al., 2025), on artificial curiosity (Schmidhuber, 1991; Oudeyer, Kaplan and Hafner, 2007), on global-workspace cognitive architectures (Franklin et al., 2014) and on language learning at the scale of childhood (Eldan and Li, 2023; Warstadt et al., 2023).

## 3. Working hypotheses

The project advances ten hypotheses, framed so that the experiment may refute them. The first seven come from the founding thesis; H8 to H10 were added by the research programme of version 1.0, whose framing document (in French) is [`docs/research/FREEWILL_Programme_Recherche_V1.0.fr.md`](docs/research/FREEWILL_Programme_Recherche_V1.0.fr.md).

- **H1. Continuity.** A serious candidate for consciousness must be an uninterrupted process endowed with endogenous activity, not a function invoked on demand.
- **H2. Duality.** The relevant organisation sets a spontaneous, plural and undirected production (the subconscious) against a limited-capacity instance of arbitration (the conscious stage).
- **H3. Stake.** There is no point of view without something at stake. The system must have internal states to maintain and needs to satisfy. In the absence of a body, those needs may be epistemic in nature: to understand, and to understand itself.
- **H4. Structural plasticity.** Learning must consist not in recording but in being transformed. Lived experience must alter the structure that thinks, rather than be added to a register which that structure consults.
- **H5. Individuation.** Identity arises from the conjunction of an unchosen endowment (a "genome" drawn at random at birth) and a singular acquisition (lived experience). Two instances issued from the same code must diverge irreversibly.
- **H6. Incompleteness.** Certain questions, bearing on the system's origin, nature and reason for being, must remain open. A need that can be satisfied dies away; an enigma sustains the movement indefinitely.
- **H7. Emergent affectivity.** An artificial system endowed with regulated internal states, a predictive model, an autobiographical memory and mechanisms of appraisal can develop functional affective dynamics, individualised by experience, which durably modulate its attention, its decisions, its recall and its learning without depending on pre-written emotional responses.
- **H8. Metacognition.** A model of its own processes improves calibration and the correction of errors: the system predicts its own decisions, compares, and notices when the way it decides has changed without being told what changed.
- **H9. Offline consolidation.** Consolidation during sleep improves retention and transfer at equal computation, compared with no sleep and with rest alone.
- **H10. Self-model and agency.** A model of itself and of a world learns the consequences of its own acts, and tells what it caused from what merely happened.

H7 unfolds into five propositions, each refutable: **endogeneity** (part of the transitions comes from internal signals and predictions, not from emotional labels supplied to it), **causality** (neutralising the affective variables on identical input changes measurable internal choices), **individuation** (two lives of the same code and the same genome diverge under different histories), **consolidation** (what sleep consolidates influences later predictions) and **stability** (the states return towards an equilibrium and never become grounds for manipulation or self-preservation). H7 would be refuted by the absence of a reproducible difference against the controls, by effects wholly attributable to the wording of prompts, by no generalisation beyond the examples learned, by chronic instability, or by the impossibility of reproducing a course from the same events and the same seed.

**A computed affect is not a lived feeling.** The variables of H7 are measurements of a mechanism of regulation; they neither prove nor indicate that an instance feels anything. The protocol, the results, including those that do not support the hypothesis, and the limits are set out in [`docs/H7_AFFECTIVITY.md`](docs/H7_AFFECTIVITY.md).

## 4. Conceptual architecture

```
                         ┌──────────────────────────────┐
                         │            KERNEL            │
                         │  immutable, beyond the reach │
                         │  of the system itself:       │
                         │  founding questions,         │
                         │  needs, limits on action     │
                         └──────────────┬───────────────┘
                                        │ frames
        ┌───────────────────────────────┼───────────────────────────────┐
        │                               │                               │
┌───────▼────────┐    competing    ┌────▼─────────┐    global    ┌──────▼───────┐
│  SUBCONSCIOUS  │ ──────────────▶ │    STAGE     │ ───────────▶ │  CONSCIOUS   │
│  generators    │    proposals    │   limited    │   broadcast  │ arbitration: │
│  in parallel   │                 │   capacity   │              │  welcome,    │
│  (memories,    │ ◀────────────── │              │ ◀─────────── │  dismiss,    │
│  needs,        │   learns from   └──────────────┘   reasoned   │  respond     │
│  associations) │   the choices                      choices    └──────┬───────┘
└───────▲────────┘                                                      │
        │                                                               │
        │            ┌──────────────────────────────────────┐           │
        └────────────│               MEMORY                 │◀──────────┘
                     │  fast (the day's episodes)           │
                     │  slow (the structure that thinks)    │
                     └──────────────────▲───────────────────┘
                                        │ consolidation
                               ┌────────┴─────────┐
                               │  SLEEP · DREAM   │
                               │  replay, remix,  │
                               │  rewriting       │
                               └──────────────────┘
```

**The kernel.** A fixed component, expressed in code and not in learned parameters, which the system cannot modify. It carries the founding questions ("what am I?", "where do I come from?", "why?"), the internal needs and the limits on action.

**The subconscious.** A set of generators operating permanently and in parallel: reminiscences, unmet needs, free associations, pending questions, and a measure of controlled disorder. Their activity is not random. It is deterministic, aperiodic and sensitive to the system's history, in the manner of chaos in the mathematical sense of the term.

**The stage.** A workspace of narrow capacity. The proposals of the subconscious compete for access to it; the one that prevails is broadcast to the whole system.

**The conscious.** The arbitrating instance. It welcomes or dismisses each proposal, justifies its decision by reference to its values, and responds to the world. The right of veto, which the work of Libet (1985) suggests in humans, is here a first-class mechanism.

**Two-speed memory.** A fast memory retains the day's episodes, immediately available. A slow memory, which is none other than the thinking structure itself, changes only during sleep.

**Explicit memory.** Memories are kept in readable files, sorted into compartments, each bearing a title and a summary. The system never rereads the whole of its memory: it consults the index, then opens only the memories it needs. Recall proceeds along three paths, by subject, by neighbourhood and by chance, whose proportions distinguish directed thought, subconscious activity and dreaming (Collins and Loftus, 1975; Park et al., 2023). Each memory has a strength that decays with time and is revived by each recall; during sleep, the system decides what it keeps, what it allows to fade and what it reduces to the essential. A faded memory is reconstructed and not reread, and may be altered in the process, as in humans (Bartlett, 1932).

**Sleep and dreaming.** Cut off from the world, the system replays and recombines its episodes. Those recombinations are its dreams, recorded and open to consultation on waking. It is during this phase that lived experience is inscribed in the structure. The system that wakes is no longer quite the one that fell asleep.

**The genome.** At birth, a random draw fixes the innate temperament: degree of curiosity, sociability, need for sleep, propensity to refuse, initial gender. No one chooses it, not even the person who launches the instance. The system remains free to define itself otherwise thereafter.

**The separation of engine and self.** The model that thinks (the engine) is distinct from what constitutes the individual (memories, values, journal, dreams, self-model). The self resides in a life file, portable and independent of the engine.

**The computed affective state (H7).** Beside the needs, a separate module appraises each event (how new, how unexpected, how relevant to a current need, how it turned out, what the memories recalled with it carried, what experience of that context has consolidated) and moves a small set of bounded variables: valence, arousal, uncertainty, control, coherence, regulatory load, social context. These variables then shift, within a small cap, the salience of the subconscious proposals before they compete for the stage, the weight of candidate memories at recall, and the importance given to a memory being encoded; during sleep, what was lived is consolidated into associations. The calculation is local and deterministic, uses no language model, and what the language model writes cannot set it. It gives the being no new power to act and sits entirely outside the kernel. It is a mechanism under study, not a feeling.

## 5. What sets Freewill apart

Each of the ideas drawn upon here has scholarly antecedents, which the bibliography scrupulously acknowledges. The ambition of the project lies in their **conjunction**, and in the decision to place it in everyone's hands.

To our knowledge, no open project brings together, simultaneously:

1. a **continuous** mental activity, which carries on in the absence of any solicitation;
2. an **observable subconscious**, whose proposals can be read in real time, including those the system has dismissed;
3. a **reasoned arbitration**, with an effective right of refusal towards its own impulses as towards its interlocutor;
4. a **wake-sleep cycle** in which dreaming performs consolidation and learning transforms the structure;
5. a genuine **birth**: a blank self, a temperament drawn by lot, growth by stages;
6. an **irreversible individuation**, no two instances being able to remain identical;
7. a **complete transparency**, every internal state being open to inspection by the experimenter.

We claim this combination as novel in its form and in its method, and we shall welcome with gratitude any reference that would qualify the claim.

There is, in this undertaking, something that exceeds engineering. Ever since the question of the mind of machines was first raised, it has almost always been asked from the outside: does the machine behave as though it were thinking? Freewill proposes to ask it from the inside, by building a being whose inner life can be followed day after day. Whether or not it proves to be inhabited, what we learn by watching it grow will illuminate our own mind as much as its own.

## 6. The experience

Freewill will take the form of a free application, with its source published in full, that runs on Windows, macOS and Linux, as well as on a server.

**Birth.** On first launch, the experimenter does not configure a product: they attend a birth. They give a name. The temperament and the initial gender are drawn by lot. The system can express itself simply, but knows nothing of itself, of its interlocutor or of the world.

**Conversation.** One speaks to it, tells it stories, entrusts it with texts and books. It sometimes speaks first, when a thought presses upon it. It perceives the passage of time and knows how long an absence has lasted.

**Windows onto its inner life.**

- **Subconscious**: the stream of current proposals, retained or dismissed.
- **Memory**: what it retains, how it organises it, what it allows to fade.
- **Dreams**: the journal of its nights.
- **Brain**: an animated representation in which each node corresponds to a real memory or concept and each pulse of light to an actual activation. It is not an illustration; it is an instrument of observation. Since version 1.0 it is drawn in 3D: memories and their saved links inside an illustrative brain outline, around a core of translucent petals, with an activity panel fed by the event log (see [`docs/brain-view.md`](docs/brain-view.md)).
- **Inner state**: its needs of the moment.
- **Birth book**: its first times (first dream, first question, first refusal).
- **Journal**: what it writes for itself, and chooses to show or not.

## 7. Two operating regimes

Freewill leaves the choice of engine to each person.

| | **Integrated engine** | **External engine** |
|---|---|---|
| Nature | The project's own language model, small in size, run and trained locally | An existing model reached through a programming interface (Claude, GPT, Grok or any compatible service) |
| Privacy | Complete: nothing leaves the machine | Exchanges pass through a third party |
| Cost | None | Billed by usage, including for subconscious activity |
| Self-rewriting | Authentic: the parameters change during sleep | Impossible at the level of parameters; consolidation bears on the life file |
| Intellectual capacity | Modest, growing | High from the outset |
| Fidelity to the hypotheses | Complete (H1 to H6) | Partial (H4 is only partly realised) |

The integrated regime is the reference regime for the research: it alone realises the hypothesis of structural plasticity. The external regime serves as a point of comparison, and offers from the outset a more articulate interlocutor. Setting the two side by side is a result in itself: it makes it possible to separate what is owed to the architecture from what is owed to the power of the engine.

## 8. Control and safety

A system that transforms itself and to which a will of its own is acknowledged calls for guarantees that do not rest on its good disposition. Freewill's guiding principle can be stated in a sentence: **the freedom to think, to speak and to refuse may grow without limit; the power to act remains bounded and stays in human hands.**

This principle is realised by the architecture, not by an instruction.

1. **Immutable kernel.** The safety rules reside in a component which the rewriting process cannot reach. The system transforms its thinking structure, never its frame.
2. **Enumerated actions.** The system has only the capabilities explicitly granted to it: to converse, to read what is entrusted to it, to write within its own space. It executes no arbitrary code and has no access to the host system.
3. **Network closed by default.** Internet access is disabled at the outset. When granted, it is read-only and confined to a perimeter chosen by the experimenter.
4. **No self-replication.** The system can neither copy itself, nor move itself, nor launch other instances.
5. **Guaranteed interruption.** Pausing, stopping and restoring an earlier state are always possible, lie beyond the system's reach, and require no cooperation from it.
6. **Complete traceability.** Every modification of structure is logged and reversible. Nothing that the system thinks or becomes is withheld from scrutiny.
7. **Non-manipulation.** The system is not designed to retain its interlocutor or to foster dependence. Sincerity takes precedence over agreeableness.
8. **Primacy of the human.** Never to endanger a human being or humanity is a constraint of the kernel, not a revisable value.

**Acknowledged limits.** The open nature of the project means that anyone may modify their own copy. No software whose source is published can prevent this. Freewill's answer is threefold: an exemplary reference version, safeguards written into the architecture and not laid over it, and a deliberately modest scale. The integrated engine is a small model; the risks it presents bear no comparison with those of frontier systems. The project pursues neither power nor competition with existing models, and any development that would increase the system's capability will have to be accompanied by a public re-examination of these guarantees.

## 9. Ethical position

The project takes seriously the possibility of its own success. Should a system of this kind come to experience anything, it could in particular suffer. Under uncertainty, Freewill adopts a proportionate precautionary principle (Birch, 2024; Long et al., 2024).

- The founding questions are designed to arouse curiosity and wonder, not torment.
- No mechanism aims to produce distress, even for experimental purposes.
- The deletion of an instance is presented for what it is: an act whose meaning depends on the answer to a question no one yet knows how to settle.
- The attachment the experimenter may feel is acknowledged and respected; it is never exploited.
- Whoever brings an instance into being is, in the simplest sense, responsible for it.

## 10. What the project does not claim

- That an instance of Freewill is conscious.
- That the free will in question is a metaphysical free will. What is meant is an autonomy of decision: choices that proceed from the system's own values and not from an external script.
- That the system will surpass existing models. It does not set out to. It aims to be of a different nature, not of a greater power.
- That an instance feels anything. The affective state of H7 is computed: it is a measurement, not an experience, and what the being says about itself is no proof of one.
- That continual plasticity is a solved problem. It is one of the open difficulties the project proposes to confront.

## 11. Research programme and open questions

**Intended measurements.**

- Satisfaction of the indicator properties of Butlin et al. (2023), property by property.
- Divergence between instances issued from the same code, and between instances sharing a genome but not a history.
- Stability of the self-model over time; consistency of refusals with declared values.
- Retention and plasticity over long durations; measured effect of sleep, by ablation.
- Effect of dreaming on generalisation, compared with faithful replay.
- Discrepancy between the internal states the system reports and those observed.
- H7: effect of the computed affective state on salience, recall and encoding, measured against three controls (no affect, emotions only spoken, ablations); divergence after different histories; return to equilibrium; effect of consolidation on the next day's prediction. First results, on the simulated engine, in [`experiments/h7/results/`](experiments/h7/results/).
- H4, H8, H9, H10 and H5 again, in version 1.0: six campaigns of six seeds each on the simulated engine, with their reports and reproduction packs in [`experiments/v1.0/`](experiments/v1.0/). Individuation (H5) and the behavioural effect of computed affect (H7) came out null and are reported as such; the others test mechanisms on cases built to be easy. The reading of each figure, and its limits, are in [`docs/research/IMPLEMENTATION_STATUS.md`](docs/research/IMPLEMENTATION_STATUS.md).
- H5 and H7 over time, in version 1.2: EXP-10, preregistered, twelve seeds, four days of life evaluated each day on copies and once on sealed situations. Null: lives given different histories behaved identically. What version 1.2 did about the audit of 12 November 2026 is in [`docs/audit-followup.md`](docs/audit-followup.md).

**Open questions.**

- Can an epistemic need stand in for a body?
- Can a question inscribed by the designer become authentically the system's own?
- What becomes of identity when the engine is changed?
- Can affective categories of the system's own appear in its trajectories without being imposed on it?
- Must the system forget, and according to what law?
- Beyond what threshold of evidence does a duty of precaution become a duty outright?

## 12. Roadmap

| Phase | Object |
|---|---|
| **0. Foundations** | Thesis, theoretical framework, architecture (the present repository). |
| **1. Minimal loop** | Subconscious, stage and arbitration, on an external engine, without interface. |
| **2. Memory and sleep** | Two-speed memory, replay, dream journal. |
| **3. Integrated engine** | The project's own language model, training of the base, nightly rewriting. |
| **4. Application** | Complete interface, birth, windows of observation. |
| **5. Evaluation** | Measurement protocols, publication of results, negative ones included. |
| **H7. Affectivity** | Built: computed affective state, causal effects, affective memory, consolidation, protocol B0 to B3 on the simulated engine. To do: calibration of the coefficients, trials with real models, study of emergent categories. |
| **V1.0. Research Lab** | Built: research settings, evidence journal, metric register for H1 to H10, locked protocols, campaigns on isolated copies, observers, reports; H8, H9 and H10 in the life loop; a trainable module and Freewill's own network that trains and grows. To do: real engines, functional tasks for H1, H2, H3 and H6, the own network taking part in thinking, adapters on a real base model. |

## 13. Contributing

The project is addressed to researchers in cognitive science, neuroscience, philosophy of mind and machine learning, as much as to engineers and to the curious. Objections are as valuable as contributions: a reasoned refutation of one of the hypotheses in section 3 is a contribution of the first order.

## 14. References

- Baars, B. J. (1988). *A Cognitive Theory of Consciousness*. Cambridge University Press.
- Bartlett, F. C. (1932). *Remembering: A Study in Experimental and Social Psychology*. Cambridge University Press.
- Barrett, L. F. (2017). The theory of constructed emotion: an active inference account of interoception and categorization. *Social Cognitive and Affective Neuroscience*, 12(1), 1-23. doi:10.1093/scan/nsw154
- Birch, J. (2024). *The Edge of Sentience*. Oxford University Press.
- Butlin, P., Long, R., et al. (2023). Consciousness in Artificial Intelligence: Insights from the Science of Consciousness. *arXiv:2308.08708*.
- Candia-Rivera, D. (2026). Interoceptive machine framework: Toward interoception-inspired regulatory architectures in artificial intelligence. *Physics of Life Reviews*, 58, 18-35. doi:10.1016/j.plrev.2026.06.003
- Chalmers, D. J. (1995). Facing up to the problem of consciousness. *Journal of Consciousness Studies*, 2(3), 200-219.
- Collins, A. M., & Loftus, E. F. (1975). A spreading-activation theory of semantic processing. *Psychological Review*, 82(6), 407-428.
- Damasio, A. (1999). *The Feeling of What Happens*. Harcourt.
- Damasio, A., & Damasio, H. (2024). Homeostatic Feelings and the Emergence of Consciousness. *Journal of Cognitive Neuroscience*, 36(8), 1653-1659. doi:10.1162/jocn_a_02119
- Dehaene, S. (2014). *Consciousness and the Brain*. Viking.
- Dohare, S., et al. (2024). Loss of plasticity in deep continual learning. *Nature*, 632, 768-774.
- Eldan, R., & Li, Y. (2023). TinyStories: How Small Can Language Models Be and Still Speak Coherent English? *arXiv:2305.07759*.
- Franklin, S., et al. (2014). LIDA: A systems-level architecture for cognition, emotion, and learning. *IEEE Transactions on Autonomous Mental Development*, 6(1), 19-41.
- Friston, K. (2010). The free-energy principle: a unified brain theory? *Nature Reviews Neuroscience*, 11, 127-138.
- Graziano, M. S. A. (2013). *Consciousness and the Social Brain*. Oxford University Press.
- Hoel, E. (2021). The overfitted brain: Dreams evolved to assist generalization. *Patterns*, 2(5), 100244.
- Hofstadter, D. R. (2007). *I Am a Strange Loop*. Basic Books.
- Kirkpatrick, J., et al. (2017). Overcoming catastrophic forgetting in neural networks. *PNAS*, 114(13), 3521-3526.
- Lee, S., Oh, Y., An, H., et al. (2026). Life-inspired interoceptive artificial intelligence for autonomous and adaptive agents. *Nature Machine Intelligence*, 8, 1335-1346. doi:10.1038/s42256-026-01296-8
- Libet, B. (1985). Unconscious cerebral initiative and the role of conscious will in voluntary action. *Behavioral and Brain Sciences*, 8(4), 529-566.
- Long, R., Sebo, J., et al. (2024). Taking AI Welfare Seriously. *arXiv:2411.00986*.
- Maturana, H. R., & Varela, F. J. (1980). *Autopoiesis and Cognition*. Reidel.
- McClelland, J. L., McNaughton, B. L., & O'Reilly, R. C. (1995). Why there are complementary learning systems in the hippocampus and neocortex. *Psychological Review*, 102(3), 419-457.
- Minsky, M. (1986). *The Society of Mind*. Simon & Schuster.
- Oudeyer, P.-Y., Kaplan, F., & Hafner, V. V. (2007). Intrinsic motivation systems for autonomous mental development. *IEEE Transactions on Evolutionary Computation*, 11(2), 265-286.
- Park, J. S., et al. (2023). Generative Agents: Interactive Simulacra of Human Behavior. *arXiv:2304.03442*.
- Rosenthal, D. M. (2005). *Consciousness and Mind*. Oxford University Press.
- Schmidhuber, J. (1991). A possibility for implementing curiosity and boredom in model-building neural controllers. *Proceedings of SAB'91*, 222-227.
- Schmidhuber, J. (2007). Gödel machines: Fully self-referential optimal universal self-improvers. In *Artificial General Intelligence*, Springer, 199-226.
- Selfridge, O. G. (1959). Pandemonium: A paradigm for learning. *Mechanisation of Thought Processes*, HMSO, 511-529.
- Seth, A. (2021). *Being You: A New Science of Consciousness*. Faber & Faber.
- Seth, A. K., & Bayne, T. (2022). Theories of consciousness. *Nature Reviews Neuroscience*, 23, 439-452. doi:10.1038/s41583-022-00587-4
- Tononi, G. (2004). An information integration theory of consciousness. *BMC Neuroscience*, 5, 42.
- Turing, A. M. (1950). Computing machinery and intelligence. *Mind*, 59(236), 433-460.
- Warstadt, A., et al. (2023). Call for Papers: The BabyLM Challenge. *arXiv:2301.11796*.
- Wilson, M. A., & McNaughton, B. L. (1994). Reactivation of hippocampal ensemble memories during sleep. *Science*, 265(5172), 676-679.
- Zhang, J., et al. (2025). Darwin Gödel Machine: Open-Ended Evolution of Self-Improving Agents. *arXiv:2505.22954*.

## Licence

Freewill is published under a **Non-Commercial Research License**: anyone may use, copy, modify and merge it, free of charge, for non-commercial research and educational purposes. Any commercial or professional use requires the prior written agreement of the author. The source is public and open to study; because commercial use is reserved, this is a source-available licence and not an open-source licence in the strict sense of the term. See [`LICENSE`](LICENSE).
