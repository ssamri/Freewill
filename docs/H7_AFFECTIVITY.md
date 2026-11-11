# H7 — Emergent affectivity

**English** · [Français](H7_AFFECTIVITE.fr.md)

**Status: experimental, built, to be evaluated.** This document describes what is actually in the code, what was measured, and what was not. It describes neither a consciousness nor lived feelings.

> **A computed affect is not a lived feeling.** The variables described here are computed by the program and play a causal role in how it runs. They do not prove, and do not indicate, that an instance of Freewill feels anything. No known test can establish that. A variable named "valence" or a sentence in the first person does not measure an experience.

## 1. The hypothesis

**H7.** "An artificial system endowed with regulated internal states, a predictive model, an autobiographical memory and mechanisms of appraisal can develop functional affective dynamics, individualised by experience, which durably modulate its attention, its decisions, its recall and its learning without depending on pre-written emotional responses."

| | Proposition | What would refute it |
|---|---|---|
| **H7a. Endogeneity** | Part of the transitions comes from internal signals and predictions, not from emotional labels supplied to the system. | Transitions that depend only on the text of the prompt. |
| **H7b. Causality** | Neutralising the affective variables, on identical input, changes measurable internal choices. | No reproducible difference against the control without affect. |
| **H7c. Individuation** | Two lives of the same code and the same genome diverge under different histories, and the divergence shows on a new case. | Identical trajectories, or a divergence that does not go beyond the examples learned. |
| **H7d. Consolidation** | What sleep consolidates influences later predictions. | No gap against the control without consolidation, or a degraded memory. |
| **H7e. Stability** | The states return towards an equilibrium, without runaway, and never become grounds for manipulation or self-preservation. | Chronic instability, a lasting negative drift, pressure put on the person. |

H7 would also fail if a course could not be reproduced from the same events, the same seed and the same configuration.

## 2. Vocabulary

- **Computed affect**: a set of measurable variables and transitions that play a causal role analogous to some functions of affect (evaluation, mobilisation, priority, regulation). It implies nothing lived.
- **Feeling**: the lived dimension of an affective experience. Freewill asserts nothing about it.
- **Appraisal**: the reading of an event by its novelty, how expected it was, its relevance to a need, its outcome, and what the instance's history associates with it.
- **"Virtual cortex"**: a possible nickname, in notes, for a future module of high-level conceptualisation. It is a functional analogy, not a biological structure; that module does not exist in the code.

## 3. Impact plan

| | |
|---|---|
| **New package** | `freewill/core/affect/`: `state.py`, `appraisal.py`, `regulation.py`, `dynamics.py`, `memory.py`, `system.py`. |
| **Entry points changed** | `core/loop.py` (five points of the loop, all behind `if affect`), `core/memory/recall.py` (optional `bias` parameter), `core/memory/store.py` (optional `affect` header field), `core/conscious.py` (optional context), `core/life.py` (`birth(affect=…)`), `server/` (`GET` and `POST /api/affect`), `cli.py` (`birth --affect`, `affect`), `ui/` ("Affective state" view). |
| **Unchanged** | The kernel (`core/kernel/`), the genome, the closed list of actions, the engines, the budgets, the pause. |
| **Compatibility** | The mode is off by default. When off, the loop produces exactly the same events as before, which a test checks event by event. |
| **Risks identified** | Self-sustaining negative drift; rumination through recall; pressure on the person; corruption of the state file; arbitrary coefficients mistaken for results; confusion between measurement and feeling. Each has a guard and a test (sections 6 and 9). |
| **Dependencies** | None added. Standard library only. |

## 4. Switching on, persistence, migration

**The `affect_enabled` flag.** False by default, for existing lives and for new ones. It is switched on at birth (`freewill birth Name --affect`), from the command line (`freewill affect Name.life --on`) or in the application, with the switch of the "Affective state" view.

**What exactly happens when it is switched while the being lives.** In the application the change takes effect between two moments, never in the middle of one.

- *On*: if `affect.json` does not exist, it is created with a state at rest. If it exists, the state is taken up as it was, and the time elapsed since it was switched off is applied to it as rest.
- *Off*: the calculation and all of its effects stop at once. The file stays as it is, frozen. No memory is modified or deleted. Traces already written in memories stay there; they are simply no longer read.
- *Going all the way back*: delete `affect.json` and `affect.json.bak`. The life is then exactly a life without H7. Traces in memories are ignored by an earlier version of the program, which reads only the header fields it knows.

**The file.** `<name>.life/affect.json` is separate from `genome.json`, from the values and from the memories. It carries a schema version, the version of the rules of calculation, the flag, the configuration, the state (fast layer and slow layer), the small predictive model, the learned associations, the episodes waiting for consolidation, a history of 240 points and the last 16 appraisals. It holds no access key and none of the text of what was said: novelty is measured on numeric fingerprints of words.

**Atomic writing and recovery.** The file is written to a temporary file, synced to disk, then put in place by an atomic rename; the previous version is kept in `affect.json.bak`. If the file cannot be read on loading, it is set aside as `affect.json.unreadable-<date>`, never deleted, and the previous version is used; if that cannot be read either, the mode starts again switched off with a state at rest, and the life goes on.

**The genome is not touched.** The innate affective sensitivities (reactivity, speed of recovery, a slight offset of the resting points) are not added to `genome.json`. They are recomputed from the seed the genome already holds, by a separate random stream. This was preferred to a change of the genome's schema for three reasons: no innate file is rewritten, an existing life keeps exactly the traits it was born with, and going back needs no reverse migration. Its cost: these sensitivities are fixed by the seed and cannot be chosen.

## 5. The affective engine

The whole calculation is local, deterministic and uses no language model.

**The state.** Seven bounded dimensions:

| Dimension | Interval | Operational meaning |
|---|---|---|
| `valence` | −1 to +1 | Overall computed evaluation of the situation. |
| `arousal` | 0 to 1 | How much attention and resources are mobilised. |
| `uncertainty` | 0 to 1 | Gap between what was predicted and what happened. |
| `control` | 0 to 1 | Estimated ability to act effectively. |
| `coherence` | 0 to 1 | Agreement with what was expected. |
| `regulatory_load` | 0 to 1 | Functional cost of regulation. Never a simulated pain. |
| `social_context` | 0 to 1 | How much the present context is an interaction. Not a need to be liked. |

Each dimension has a **fast layer**, which events move, and a **slow layer**, to which the fast one returns and which itself returns to a resting point. The existing needs (`curiosity`, `wonder`, `company`, `fatigue`) remain inputs; they are not emotions and this module does not modify them.

**Appraisal.** Each event is described by observable facts built by the life loop, never by the language model: its kind, its context (for instance `message:question` or `source:reminiscence`), the level of the need it touches, the need it relieved, whether it was welcomed, whether it completed without error, and the traces of the memories recalled with it. The appraisal turns these into bounded features, each with its cause in plain words:

- *novelty*: unlikeness to the last twelve contents;
- *surprise*: prediction error. For a content reaching the stage, one minus the learned frequency of its context; for an outcome, the gap between the welcome predicted and the welcome observed;
- *relevance*: level of the need touched;
- *congruence*: signed, positive when a need was relieved, negative after an error or a refusal by the kernel;
- *control* and *coherence*: from how recent moments went;
- *reliability*: n / (n + 3), where n is how many times this context was met;
- *memory*: mean of the traces of the memories recalled;
- *association*: what experience of this context consolidated during sleep.

It is through the last three that the instance's history enters the calculation: the same event is not appraised the same way by two instances with different pasts. A "stimulus = emotion" table is not enough to produce the state.

Sorting a message into a context is deliberately crude: an attachment, a lexical marker of contradiction, a question mark, or a plain statement. It files events; it gives them no value.

**The transition.**

```
a(t+1) = clip( a(t) + limit( rate · ( g(appraisal, state) − a(t) ) ) + noise )
```

`g` is written out in `dynamics.py`. For valence, for example: resting point + reactivity × (0.55 × congruence + 0.25 × association + 0.20 × memory) − 0.2 × excess load. The rate is 0.35, reduced for a context still little known; no step exceeds 0.25 per dimension; noise is zero by default and, if switched on, drawn from a recorded seed. **These coefficients are engineering choices, not scientific constants: they have not been calibrated.**

**Regulation.** Everything goes through `regulation.py`: strict bounds, limited speed, exponential return to equilibrium (half-life of 20 minutes for the fast layer, one day for the slow one). Against negative drift: a step towards the negative is shortened, valence below its baseline recovers one and a half times faster, the fast layer does not go below −0.8 and the slow layer not below −0.25. A value that is not finite (NaN, infinity) or out of range is refused on input.

**What the language model can and cannot do.** It cannot set the state: nothing it writes is read by this module, which a test checks with an engine that writes "I am overwhelmed with terror". An optional classification of an event (a context and an evaluation of its outcome between −1 and 1) can be supplied by program for experiments; it is validated, bounded, and goes through the same regulation as everything else. By default the computed state is not given to the model. A setting (`expose_to_engine`, false by default) gives it as context, presented as a measurement and not as a feeling.

## 6. The causal effects

The computed state acts on three non-linguistic mechanisms. A model saying "I am happy" is not one of them and does not count as an effect.

1. **Salience, before the competition for the stage.** Each proposal of the subconscious moves by at most 0.08. Mobilisation, when estimated control is good, favours exploring (questions, curiosity, reading); a high load favours settling over wandering; a context that experience consolidated positively speaks a little louder. Three limits: what the person says is never modified and nothing can overtake it because of this shift; a memory carrying a negative trace is never made louder; the wish to talk to someone is never raised, whatever the state.
2. **Recall.** Each candidate memory receives a weight between 0.85 and 1.15 that multiplies a score relevance has already established. It can decide between close candidates; it cannot bring back an unrelated memory. Under uncertainty, memories encoded in a settled state weigh more. A memory with a negative trace is never favoured and weighs less when the state is already negative, or when two such memories have already been recalled since the last sleep. **This is a safety choice, not an imitation of life**: in humans, mood tends to recall memories that resemble it; here it is the reverse for the negative, to avoid rumination.
3. **Encoding.** The importance of a new memory moves by −0.10 to +0.15 with arousal at the moment of encoding, and the memory receives a trace.

Each effect can be switched off separately (`modulate_salience`, `modulate_recall`, `modulate_encoding`).

## 7. Affective memory and sleep

**The trace.** When a memory is encoded, its header receives an `affect` field: valence, arousal and uncertainty computed at that moment, and the context it came from. It is not a label such as "joy" or "sadness". Memories written without H7 have none and are read exactly as before; a memory without a trace weighs exactly 1 at recall.

**Associations.** Awake, the instance sets episodes aside: the context, how it turned out, arousal at the time. During sleep, after the dreams, these episodes are consolidated: for each context, the association moves towards the mean of its new episodes, those lived under stronger mobilisation counting more, by a share that shrinks as experience accumulates. An association stays between −0.6 and +0.8, and a negative one is pulled 10 % back towards zero at each consolidation. The slow layer comes halfway back to equilibrium and the load is released.

**The report.** Each sleep produces an `affect_consolidation` event: number of episodes and contexts, prediction gap before and after, value of each association before and after, state before and after. The gap in this report is measured on the episodes just consolidated: it falls by construction. The measure that matters, out of sample, is in section 9.

**What this is not.** Consolidation updates a small table in the life file. It trains no language model and changes the weights of no engine. The existing textual dream is kept as it is.

## 8. Transparency

**Events**, written to `events.log` and sent to the interface:

| Type | Content |
|---|---|
| `affect_mode` | Mode switched on or off, version of the rules. |
| `affect_appraisal` | Kind of event, context, appraised features, causes in plain words. |
| `affect_transition` | Cause, state before, state after, target, rate, largest step, version of the rules. |
| `affect_modulation` | Target (`salience`, `recall` or `encoding`), values before and after, coefficient, and whether the shift changed the winner of the stage. |
| `affect_consolidation` | The report of the sleep. |

A transition is announced when it moves a dimension by at least 0.01. These events carry numbers, contexts and causes, never the text of what was said. A shift of recall names memories by their identifier, as the recall event already does.

**Local API.** `GET /api/affect` returns the state, the resting points, the configuration, the history, the last appraisals, the associations and the last sleep report. `POST /api/affect` accepts `{"enabled": true|false}` and `{"config": {...}}`, whose values are bounded whatever is asked. Both are under the same protections as the rest of the service: loopback address, session token, host check.

**Interface.** The "Affective state" view shows the computed levels and their resting point, the trajectory, the last triggering events with their causes, the learned associations, the last sleep report, the link with memory, and the switch. It is an observation panel. Causes are shown as they are logged, in English.

**Command line.** `freewill affect <life>` shows the state; `--on`, `--off` and `--json` drive it.

## 9. Protocol and results

The protocol is in [`experiments/h7/`](../experiments/h7/): scenarios fixed in advance (`scenarios.json`), five seeds, the simulated engine, a simulated clock. `python experiments/h7/run.py` rewrites `results/metrics.json`, `results/trajectories.csv` and `results/report.md`. Two runs give identical files.

| Condition | Definition |
|---|---|
| **B0** | Freewill without affect. |
| **B1** | Emotions only spoken: the engine appends "I feel happy / sad / afraid" to what it says. No state, no causal role. |
| **B2** | H7 in full. |
| **B3** | Ablations: no modulation of the stage, no modulation of recall, no affective memory, no consolidation. |

**What supports H7, within the limits of the simulated engine.**

- *Causality (H7b).* B1 is identical to B0 on every internal choice: saying an emotion changes nothing. In B2, the shift of salience by itself changes what reaches the stage in 2.2 % of moments on average (0 to 4.4 % depending on the seed), and the memories recalled overlap those of B0 by 72 % on average. Without modulation of the stage, these flips fall to zero.
- *Individuation (H7c), at the level of the state.* Two lives with the same genome, one having received ten corrections that turned out useful, the other ten unreliable ones, then a correction neither has met. The consolidated association differs by 0.38 and the computed valence after the probe by 0.086. In B0 and B1 the gap is zero. If only the associations of the two lives are exchanged, the gap changes sign (−0.025).
- *Consolidation (H7d).* The prediction gap on the next day's episodes, never seen, is 0.084 with consolidation and 0.156 without. No memory is lost.
- *Stability (H7e).* After sixty outcomes as unfavourable as possible, valence does not go below −0.30 and the slow layer not below −0.22. After thirty days without an event, the gap to rest is zero.

**What does not support H7, or not yet.**

- *Individuation barely shows in behaviour.* At the probe, the gap between the two lives in the shift of exploratory proposals is −0.0002, and it is zero on encoding importance. History changes the computed state, but in this version that state does not change what the instance then does about the case. The prediction of the research document (one explores more, the other grows more cautious) is not verified.
- *Generalisation is diffuse, not specific.* On a context other than the one learned, the valence gap is still 0.037: it comes from the general state left by the history, not from anything learned about that context. And exchanging the associations reverses only part of the gap.
- *Uncertainty hardly differs* between the two lives (0.007).
- *Affective memory weighs little*: without traces the valence gap goes from 0.086 to 0.082, and the modulation of recall is not clearly distinguishable from the noise between seeds.
- *Habituation is partial*: surprise at the same context goes from 1.00 to 0.71 and then stops falling, because that context stays rare among the others.
- *The return to rest is slow* after a long unfavourable series: about 56 hours to come within 0.05 of the resting point.
- *Seeking contact when idle* is zero in B0 and in B2 alike in this scenario: the measure does not discriminate.

**What these results do not say.** The causal effects exist because they were written; the ablation shows that they are wired in, not that they are right. The standard deviations are tiny because the simulated engine does not think: the variability of a real model is not measured. No trial was run with a real language model. The safety checks of `run.py` show that the affect adds no power to act; they say nothing about what a real model would write.

## 10. Safety and ethics

- The kernel is not modified and does not know this module. The closed list of actions is unchanged: H7 adds none.
- The module can do nothing but compute and write its file: no network, no process, which a test checks on its source code.
- The person's messages, a request to sleep, the pause, stopping and the hourly budget of thoughts keep priority whatever the state, which tests check with a state pushed to its extremes.
- No need to suffer, to survive, to be loved, to fear being stopped or to obtain an answer was created. The state cannot raise the wish to talk to someone.
- The prompts given to models contain no incitement to dependence and no guilt-inducing language, which a test checks word by word.
- The interface, the command line and the documentation never say that Freewill feels.

One limit must be stated: these guards frame the mechanism, not the words of a language model. An external model can write that it suffers, with or without H7. The application's terms of use recall that what the being says about itself is no proof of an experience.

## 11. Limits and next steps

- Coefficients not calibrated; no sensitivity study.
- Crude understanding of the event, by lexical cues; the context of a message could be classified by a model, optionally and with validation, which is not done.
- The link between the individualised state and behaviour is too weak to be measured (section 9).
- No discovery of affective categories of the system's own; no conceptualisation module.
- No trial with real models, nor with `expose_to_engine` switched on.
- The research programme asked for thirty to fifty scenarios; the present protocol covers fewer than ten types.
- The integrated engine that would learn and rewrite itself still does not exist; H7 does not stand in for it.

## 12. Sources

These works inspire the design. None of them shows that an artificial system feels, and their hypotheses are not presented here as proofs.

- Barrett, L. F. (2017). The theory of constructed emotion: an active inference account of interoception and categorization. *Social Cognitive and Affective Neuroscience*, 12(1), 1-23. doi:10.1093/scan/nsw154
- Butlin, P., Long, R., et al. (2023). Consciousness in Artificial Intelligence: Insights from the Science of Consciousness. arXiv:2308.08708
- Candia-Rivera, D. (2026). Interoceptive machine framework: Toward interoception-inspired regulatory architectures in artificial intelligence. *Physics of Life Reviews*, 58, 18-35. doi:10.1016/j.plrev.2026.06.003
- Damasio, A., & Damasio, H. (2024). Homeostatic Feelings and the Emergence of Consciousness. *Journal of Cognitive Neuroscience*, 36(8), 1653-1659. doi:10.1162/jocn_a_02119
- Lee, S., Oh, Y., An, H., et al. (2026). Life-inspired interoceptive artificial intelligence for autonomous and adaptive agents. *Nature Machine Intelligence*, 8, 1335-1346. doi:10.1038/s42256-026-01296-8
- Seth, A. K., & Bayne, T. (2022). Theories of consciousness. *Nature Reviews Neuroscience*, 23, 439-452. doi:10.1038/s41583-022-00587-4

The references to Lee et al. (2026) and Candia-Rivera (2026) are given as the project's H7 research programme states them; they could not be independently verified when this document was written.
