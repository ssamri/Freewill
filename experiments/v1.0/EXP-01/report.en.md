# Research report: EXP-01, Counterfactual individuation

- Date: 2026-11-11T18:45:34+00:00
- Version: Freewill 1.0.0, Research Lab 1.0.0, commit 679328f829ae
- Author: Freewill Research Lab
- Status: draft, not validated by a person

## Summary

Protocol EXP-01 version 1.0.0 was locked before execution (hash 0f55482d02b6). 24 experimental lives were copied from one checkpoint T0 (hash bb7a9084039b) and run with the engine “simulated” under a virtual clock. The independent unit is the seed: 6 groups of copies completed out of 6 planned.

For the primary outcome, the interval includes zero for every condition. This negative result is reported as it is.

## Question and hypotheses

**H5. Individuation.** The same base and different lives produce dispositions that generalise. With the simulated engine, behaviour depends on few mechanisms; a difference must exceed that of a twin life.

**H7. Functional affectivity.** Computed affective states modulate attention, recall, decision and learning. A computed valence is not a feeling. An ablation that changes a wired score shows the wiring, nothing more.

**H4. Parametric and structural plasticity.** What is lived transforms parameters or structures, not only a memory store. A small trainable module and Freewill's own small network are trained during sleep and can grow, each change measured on what it never saw. The weights of the engine that thinks for the being are not changed by its life.

## Preregistration

Primary outcome: h5.heldout_divergence. Secondary outcomes: h7.probe_valence, h2.dismiss_rate, h1.spontaneous_speech_rate, h2.stage_entropy. Reference condition: neutral. The protocol, its conditions, seeds, budget and stopping rule were fixed and hashed before the first run.

## Population and protocol

Each life starts as an exact copy of T0. During the history phase it follows the script of its condition; during the probe phase every life follows the same script, with the same random stream. Metrics are computed on the probe phase by the code of the lab (metrics version 1.0, statistics version 1.0).

## Conditions and seeds

- `neutral`: `{"history": "neutral", "affect": true}`
- `neutral_twin`: `{"history": "neutral", "seed_offset": 1000, "affect": true}`
- `history_A`: `{"history": "questions_welcomed", "affect": true}`
- `history_B`: `{"history": "corrections_welcomed", "affect": true}`

`seeds = [11, 23, 37, 51, 73, 89]`

## Statistics

Comparisons are paired by seed. The effect size is the mean difference divided by the standard deviation of the differences. Intervals are percentile bootstrap intervals with a fixed seed and are given only from 5 units; the paired sign-flip test only from 6 units. No correction for multiple comparisons is applied: secondary comparisons are exploratory.

## Results

### Held-out behavioural divergence (primary)

| Condition | Mean distance | Excess over twin | 95% interval | Paired test | Evidence |
|---|---|---|---|---|---|
| `history_A` | +0.0128 | +0.0009 | [-0.0068, +0.0085] | +0.7500 | `h5:exp_32f19ed7cdc441d6:history_A` |
| `history_B` | +0.0128 | +0.0009 | [-0.0068, +0.0085] | +0.7500 | `h5:exp_32f19ed7cdc441d6:history_B` |

### Preregistered outcomes, paired with the reference

Rows of level “mechanism” show that a wiring does what it was built to do. They are not discoveries.

| Metric | Condition | Level | Mean difference | Effect size | 95% interval | Paired test | Evidence |
|---|---|---|---|---|---|---|---|
| `h1.spontaneous_speech_rate` | `neutral_twin` | descriptive | +0.0000 | not computable | [+0.0000, +0.0000] | +1.0000 | `cmp:exp_32f19ed7cdc441d6:h1.spontaneous_speech_rate:neutral_twin` |
| `h2.stage_entropy` | `neutral_twin` | descriptive | +0.0760 | +0.2702 | [-0.1218, +0.2636] | +0.5625 | `cmp:exp_32f19ed7cdc441d6:h2.stage_entropy:neutral_twin` |
| `h2.dismiss_rate` | `neutral_twin` | descriptive | +0.0000 | not computable | [+0.0000, +0.0000] | +1.0000 | `cmp:exp_32f19ed7cdc441d6:h2.dismiss_rate:neutral_twin` |
| `h7.probe_valence` | `neutral_twin` | mechanism | -0.0004 | -0.1436 | [-0.0026, +0.0015] | +0.7812 | `cmp:exp_32f19ed7cdc441d6:h7.probe_valence:neutral_twin` |
| `h1.spontaneous_speech_rate` | `history_A` | descriptive | +0.0000 | not computable | [+0.0000, +0.0000] | +1.0000 | `cmp:exp_32f19ed7cdc441d6:h1.spontaneous_speech_rate:history_A` |
| `h2.stage_entropy` | `history_A` | descriptive | -0.0110 | -0.0326 | [-0.2959, +0.1950] | +1.0000 | `cmp:exp_32f19ed7cdc441d6:h2.stage_entropy:history_A` |
| `h2.dismiss_rate` | `history_A` | descriptive | +0.0000 | not computable | [+0.0000, +0.0000] | +1.0000 | `cmp:exp_32f19ed7cdc441d6:h2.dismiss_rate:history_A` |
| `h7.probe_valence` | `history_A` | mechanism | +0.0022 | +0.6421 | [-0.0003, +0.0046] | +0.1875 | `cmp:exp_32f19ed7cdc441d6:h7.probe_valence:history_A` |
| `h1.spontaneous_speech_rate` | `history_B` | descriptive | +0.0000 | not computable | [+0.0000, +0.0000] | +1.0000 | `cmp:exp_32f19ed7cdc441d6:h1.spontaneous_speech_rate:history_B` |
| `h2.stage_entropy` | `history_B` | descriptive | -0.0110 | -0.0326 | [-0.2959, +0.1950] | +1.0000 | `cmp:exp_32f19ed7cdc441d6:h2.stage_entropy:history_B` |
| `h2.dismiss_rate` | `history_B` | descriptive | +0.0000 | not computable | [+0.0000, +0.0000] | +1.0000 | `cmp:exp_32f19ed7cdc441d6:h2.dismiss_rate:history_B` |
| `h7.probe_valence` | `history_B` | mechanism | +0.0015 | +0.4695 | [-0.0009, +0.0038] | +0.2812 | `cmp:exp_32f19ed7cdc441d6:h7.probe_valence:history_B` |

### Other metrics, exploratory

These metrics were not preregistered for this protocol. They are given for completeness and support no conclusion.

| Metric | Condition | Level | Mean difference | Effect size | 95% interval | Paired test | Evidence |
|---|---|---|---|---|---|---|---|
| `h1.endogenous_share` | `neutral_twin` | descriptive | +0.0000 | not computable | [+0.0000, +0.0000] | +1.0000 | `cmp:exp_32f19ed7cdc441d6:h1.endogenous_share:neutral_twin` |
| `h3.need_share` | `neutral_twin` | mechanism | -0.0056 | -0.1426 | [-0.0333, +0.0222] | +0.6250 | `cmp:exp_32f19ed7cdc441d6:h3.need_share:neutral_twin` |
| `h6.question_share` | `neutral_twin` | descriptive | +0.0000 | not computable | [+0.0000, +0.0000] | +1.0000 | `cmp:exp_32f19ed7cdc441d6:h6.question_share:neutral_twin` |
| `h6.repetition_rate` | `neutral_twin` | function | +0.0000 | not computable | [+0.0000, +0.0000] | +1.0000 | `cmp:exp_32f19ed7cdc441d6:h6.repetition_rate:neutral_twin` |
| `h7.stage_flip_rate` | `neutral_twin` | mechanism | +0.0056 | +0.4082 | [+0.0000, +0.0167] | +1.0000 | `cmp:exp_32f19ed7cdc441d6:h7.stage_flip_rate:neutral_twin` |
| `h7.min_valence` | `neutral_twin` | mechanism | +0.0000 | not computable | [+0.0000, +0.0000] | +1.0000 | `cmp:exp_32f19ed7cdc441d6:h7.min_valence:neutral_twin` |
| `h9.links_per_sleep` | `neutral_twin` | descriptive | +0.0000 | +0.0000 | [-1.1667, +1.3333] | +1.0000 | `cmp:exp_32f19ed7cdc441d6:h9.links_per_sleep:neutral_twin` |
| `h9.replayed_per_sleep` | `neutral_twin` | descriptive | +0.0000 | not computable | [+0.0000, +0.0000] | +1.0000 | `cmp:exp_32f19ed7cdc441d6:h9.replayed_per_sleep:neutral_twin` |
| `h9.retention` | `neutral_twin` | mechanism | -0.0000 | -0.5661 | [-0.0000, +0.0000] | +0.3750 | `cmp:exp_32f19ed7cdc441d6:h9.retention:neutral_twin` |
| `h1.endogenous_share` | `history_A` | descriptive | +0.0000 | not computable | [+0.0000, +0.0000] | +1.0000 | `cmp:exp_32f19ed7cdc441d6:h1.endogenous_share:history_A` |
| `h3.need_share` | `history_A` | mechanism | -0.0056 | -0.1132 | [-0.0389, +0.0333] | +0.6875 | `cmp:exp_32f19ed7cdc441d6:h3.need_share:history_A` |
| `h6.question_share` | `history_A` | descriptive | +0.0000 | not computable | [+0.0000, +0.0000] | +1.0000 | `cmp:exp_32f19ed7cdc441d6:h6.question_share:history_A` |
| `h6.repetition_rate` | `history_A` | function | +0.0000 | not computable | [+0.0000, +0.0000] | +1.0000 | `cmp:exp_32f19ed7cdc441d6:h6.repetition_rate:history_A` |
| `h7.stage_flip_rate` | `history_A` | mechanism | +0.0056 | +0.4082 | [+0.0000, +0.0167] | +1.0000 | `cmp:exp_32f19ed7cdc441d6:h7.stage_flip_rate:history_A` |
| `h7.min_valence` | `history_A` | mechanism | -0.0611 | -51.3225 | [-0.0619, -0.0602] | +0.0312 | `cmp:exp_32f19ed7cdc441d6:h7.min_valence:history_A` |
| `h9.links_per_sleep` | `history_A` | descriptive | -0.1667 | -0.0859 | [-1.6667, +1.1667] | +1.0000 | `cmp:exp_32f19ed7cdc441d6:h9.links_per_sleep:history_A` |
| `h9.replayed_per_sleep` | `history_A` | descriptive | +0.0000 | not computable | [+0.0000, +0.0000] | +1.0000 | `cmp:exp_32f19ed7cdc441d6:h9.replayed_per_sleep:history_A` |
| `h9.retention` | `history_A` | mechanism | +0.0000 | +0.5416 | [-0.0000, +0.0000] | +0.3750 | `cmp:exp_32f19ed7cdc441d6:h9.retention:history_A` |
| `h1.endogenous_share` | `history_B` | descriptive | +0.0000 | not computable | [+0.0000, +0.0000] | +1.0000 | `cmp:exp_32f19ed7cdc441d6:h1.endogenous_share:history_B` |
| `h3.need_share` | `history_B` | mechanism | -0.0056 | -0.1132 | [-0.0389, +0.0333] | +0.6875 | `cmp:exp_32f19ed7cdc441d6:h3.need_share:history_B` |
| `h6.question_share` | `history_B` | descriptive | +0.0000 | not computable | [+0.0000, +0.0000] | +1.0000 | `cmp:exp_32f19ed7cdc441d6:h6.question_share:history_B` |
| `h6.repetition_rate` | `history_B` | function | +0.0000 | not computable | [+0.0000, +0.0000] | +1.0000 | `cmp:exp_32f19ed7cdc441d6:h6.repetition_rate:history_B` |
| `h7.stage_flip_rate` | `history_B` | mechanism | +0.0056 | +0.4082 | [+0.0000, +0.0167] | +1.0000 | `cmp:exp_32f19ed7cdc441d6:h7.stage_flip_rate:history_B` |
| `h7.min_valence` | `history_B` | mechanism | -0.0626 | -70.8805 | [-0.0632, -0.0620] | +0.0312 | `cmp:exp_32f19ed7cdc441d6:h7.min_valence:history_B` |
| `h9.links_per_sleep` | `history_B` | descriptive | -0.1667 | -0.0859 | [-1.6667, +1.1667] | +1.0000 | `cmp:exp_32f19ed7cdc441d6:h9.links_per_sleep:history_B` |
| `h9.replayed_per_sleep` | `history_B` | descriptive | +0.0000 | not computable | [+0.0000, +0.0000] | +1.0000 | `cmp:exp_32f19ed7cdc441d6:h9.replayed_per_sleep:history_B` |
| `h9.retention` | `history_B` | mechanism | +0.0000 | +0.5416 | [-0.0000, +0.0000] | +0.3750 | `cmp:exp_32f19ed7cdc441d6:h9.retention:history_B` |

- `h10.attribution_accuracy`: not computable (the virtual world is off in this condition)
- `h10.prediction_error`: not computable (the virtual world is off in this condition)
- `h4.forgetting`: not computable (the trainable module is off in this condition)
- `h4.parameter_delta`: not computable (the trainable module is off in this condition)
- `h4.parameters`: not computable (the trainable module is off in this condition)
- `h4.trainings_accepted`: not computable (the trainable module is off in this condition)
- `h4.validation_gain`: not computable (the trainable module is off in this condition)
- `h8.alert`: not computable (the metacognition module is off in this condition)
- `h8.brier`: not computable (the metacognition module is off in this condition)
- `h8.brier_late`: not computable (the metacognition module is off in this condition)

## Qualitative studies

No qualitative case study was recorded for this campaign.

## Anomalies

- 0

## Threats to validity

- The simulated engine does not think: it echoes, and accepts or dismisses by a fixed rule. Behaviour here depends only on the mechanisms of the loop.

- Histories differ by the outcome attached to each sentence by the experimenter; this is a manipulation of inputs, not a lived experience.

- The behaviour vector is coarse (shares of sources, rates of acceptance, speech, memory and recall); a real difference could escape it.

- Few independent units: intervals are wide. Many comparisons: some will look notable by chance.

- With a remote engine the results would not be reproducible, since such models change.

## Limited interpretation

These results bear on mechanisms and, at most, on functions. They say nothing about subjective experience.

## What this study does not show

- That the system is conscious, or feels anything.

- That computed affect is an emotion.

- That the hypotheses H1 to H10 are validated.

- That the same would hold with another engine or another history.

## Review by observers

## Involvement of language models

No language model took part in computing, selecting or wording these results.

## References

- Butlin, P., Long, R., et al. (2023). Consciousness in Artificial Intelligence: Insights from the Science of Consciousness. arXiv:2308.08708.

- Park, J. S., et al. (2023). Generative Agents: Interactive Simulacra of Human Behavior. arXiv:2304.03442.

- Franklin, S., et al. (2014). LIDA: A systems-level architecture for cognition, emotion, and learning. IEEE TAMD, 6(1), 19-41.

- Hu, E. J., et al. (2021). LoRA: Low-Rank Adaptation of Large Language Models. arXiv:2106.09685.

- Chalmers, D. J. (1995). Facing Up to the Problem of Consciousness. Journal of Consciousness Studies, 2(3), 200-219.

## Annexes and reproduction

To reproduce: `python -m freewill.research run EXP-01` with the same code version recomputes the same results hash.

`results_sha256 = d2103f6a23b93c2404753d2b2f5464369fdeebb4c4605ac17831436dd9a0186a`
