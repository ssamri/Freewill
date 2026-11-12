# Research report: EXP-10, Longitudinal individuation

- Date: 2026-11-12T14:05:53+00:00
- Version: Freewill 1.2.0, Research Lab 1.0.0, commit 63f551a83bc7
- Author: Freewill Research Lab
- Status: draft, not validated by a person

## Summary

Protocol EXP-10 version 1.0.0 was locked before execution (hash 8214563f350d). 60 experimental lives were copied from one checkpoint T0 (hash bb7a9084039b) and run with the engine “simulated” under a virtual clock. The independent unit is the seed: 12 groups of copies completed out of 12 planned.

For the primary outcome, the interval excludes zero for at least one condition. This is one protocol with a simulated engine; see the threats to validity before reading anything into it.

## Question and hypotheses

**H5. Individuation.** The same base and different lives produce dispositions that generalise. With the simulated engine, behaviour depends on few mechanisms; a difference must exceed that of a twin life.

**H7. Functional affectivity.** Computed affective states modulate attention, recall, decision and learning. A computed valence is not a feeling. An ablation that changes a wired score shows the wiring, nothing more.

## Preregistration

Primary outcome: h5.heldout_divergence. Secondary outcomes: h5.wave_divergence, h7.affect_on_divergence, h7.probe_valence, h2.dismiss_rate. Reference condition: A. The protocol, its conditions, seeds, budget and stopping rule were fixed and hashed before the first run.

## Population and protocol

Each life starts as an exact copy of T0. During the history phase it follows the script of its condition; during the probe phase every life follows the same script, with the same random stream. Metrics are computed on the probe phase by the code of the lab (metrics version 1.0, statistics version 1.0).

## Conditions and seeds

- `A`: `{"history": "long_questions", "affect": true, "research": {"learner": true}}`
- `A_twin`: `{"history": "long_questions", "seed_offset": 1000, "affect": true, "research": {"learner": true}}`
- `B`: `{"history": "long_corrections", "affect": true, "research": {"learner": true}}`
- `A_no_affect`: `{"history": "long_questions", "research": {"learner": true}}`
- `B_no_affect`: `{"history": "long_corrections", "research": {"learner": true}}`

`seeds = [11, 23, 37, 51, 73, 89, 101, 131, 157, 181, 211, 239]`

## Statistics

Comparisons are paired by seed. The effect size is the mean difference divided by the standard deviation of the differences. Intervals are percentile bootstrap intervals with a fixed seed and are given only from 5 units; the paired sign-flip test only from 6 units. No correction for multiple comparisons is applied: secondary comparisons are exploratory.

## Results

### Held-out behavioural divergence (primary)

| Condition | Mean distance | Excess over twin | 95% interval | Paired test | Evidence |
|---|---|---|---|---|---|
| `B` | +0.0000 | -0.0085 | [-0.0128, -0.0047] | +0.0020 | `h5:exp_91bbfd2d635b4d85:B` |
| `A_no_affect` | +0.0056 | -0.0030 | [-0.0073, +0.0009] | +0.2812 | `h5:exp_91bbfd2d635b4d85:A_no_affect` |
| `B_no_affect` | +0.0056 | -0.0030 | [-0.0073, +0.0009] | +0.2812 | `h5:exp_91bbfd2d635b4d85:B_no_affect` |

### Trajectory over four days (EXP-10)

At the end of each day, a separate copy of each life met the interim probe; the lives themselves went on untouched. At the end, each life met the sealed probe once. Distances are behavioural distances between conditions of the same seed. The excess is B to A minus the twin to A; the affect column is B to A minus B_no_affect to A_no_affect.

| When | Distance B to A | Distance twin to A | Excess over twin | 95% interval | Paired test | Effect of affect | 95% interval |
|---|---|---|---|---|---|---|---|
| end of day 1 | 0.000000 | 0.012393 | -0.0124 | [-0.0158, -0.0098] | +0.0005 | +0.0000 | [+0.0000, +0.0000] |
| end of day 2 | 0.000000 | 0.009402 | -0.0094 | [-0.0128, -0.0060] | +0.0010 | +0.0000 | [+0.0000, +0.0000] |
| end of day 3 | 0.000000 | 0.007265 | -0.0073 | [-0.0103, -0.0047] | +0.0010 | +0.0000 | [+0.0000, +0.0000] |
| end of day 4 | 0.000000 | 0.007692 | -0.0077 | [-0.0124, -0.0038] | +0.0039 | +0.0000 | [+0.0000, +0.0000] |
| sealed probe | 0.000000 | 0.008547 | -0.0085 | [-0.0128, -0.0047] | +0.0020 | +0.0000 | [+0.0000, +0.0000] |

Preregistered rule: the primary criterion is not met. This null result is reported as it is.

No seed was excluded.

### Preregistration, as hashed with the protocol

- `question`: Do copies of one birth that live different histories come to behave differently on situations none of them met, beyond what two copies with the same history do?
- `unit`: seed: one group of five copies of T0, one per condition
- `primary`: excess of the sealed-probe behavioural distance between B and A over that between A_twin and A, paired by seed
- `decision_rule`: the primary criterion is met if the 95% bootstrap interval of the excess lies entirely above zero; it is not met if the interval includes zero or lies below; with fewer than 5 units left after exclusions no interval is computed and the outcome is undetermined
- `secondary`: the same excess at the end of each of the four days, measured on separate copies with the interim probe; H7: distance B to A minus distance B_no_affect to A_no_affect, paired by seed (does the computed affect widen the divergence?); computed valence and dismissal rate on the sealed probe
- `seeds`: 12, fixed before the campaign
- `exclusions`: a seed is excluded, whole, if any of its five runs did not finish (cancelled, stopped by engine errors) or exceeded its budget of moments; excluded seeds are listed with their reason and are never replaced
- `analysis`: paired comparisons by seed; percentile bootstrap (2000 draws, fixed seed); paired sign-flip test; no correction for multiple comparisons: every secondary analysis is exploratory
- `separation`: the history sentences, the interim probe and the sealed probe are disjoint; the sealed probe is played once, after the last day, and is used neither by the learner nor for any choice
- `engine`: simulated: this tests the mechanisms of the loop, not a mind; a null result is published as it is

### Preregistered outcomes, paired with the reference

Rows of level “mechanism” show that a wiring does what it was built to do. They are not discoveries.

| Metric | Condition | Level | Mean difference | Effect size | 95% interval | Paired test | Evidence |
|---|---|---|---|---|---|---|---|
| `h2.dismiss_rate` | `A_twin` | descriptive | +0.0000 | not computable | [+0.0000, +0.0000] | +1.0000 | `cmp:exp_91bbfd2d635b4d85:h2.dismiss_rate:A_twin` |
| `h7.probe_valence` | `A_twin` | mechanism | -0.0009 | -0.2114 | [-0.0034, +0.0013] | +0.5059 | `cmp:exp_91bbfd2d635b4d85:h7.probe_valence:A_twin` |
| `h2.dismiss_rate` | `B` | descriptive | +0.0000 | not computable | [+0.0000, +0.0000] | +1.0000 | `cmp:exp_91bbfd2d635b4d85:h2.dismiss_rate:B` |
| `h7.probe_valence` | `B` | mechanism | -0.0015 | -2.6442 | [-0.0019, -0.0012] | +0.0005 | `cmp:exp_91bbfd2d635b4d85:h7.probe_valence:B` |
| `h2.dismiss_rate` | `A_no_affect` | descriptive | +0.0000 | not computable | [+0.0000, +0.0000] | +1.0000 | `cmp:exp_91bbfd2d635b4d85:h2.dismiss_rate:A_no_affect` |
| `h2.dismiss_rate` | `B_no_affect` | descriptive | +0.0000 | not computable | [+0.0000, +0.0000] | +1.0000 | `cmp:exp_91bbfd2d635b4d85:h2.dismiss_rate:B_no_affect` |

### Other metrics, exploratory

These metrics were not preregistered for this protocol. They are given for completeness and support no conclusion.

| Metric | Condition | Level | Mean difference | Effect size | 95% interval | Paired test | Evidence |
|---|---|---|---|---|---|---|---|
| `h1.endogenous_share` | `A_twin` | descriptive | +0.0000 | not computable | [+0.0000, +0.0000] | +1.0000 | `cmp:exp_91bbfd2d635b4d85:h1.endogenous_share:A_twin` |
| `h1.spontaneous_speech_rate` | `A_twin` | descriptive | +0.0000 | not computable | [+0.0000, +0.0000] | +1.0000 | `cmp:exp_91bbfd2d635b4d85:h1.spontaneous_speech_rate:A_twin` |
| `h2.stage_entropy` | `A_twin` | descriptive | +0.0475 | +0.1959 | [-0.0829, +0.1821] | +0.5547 | `cmp:exp_91bbfd2d635b4d85:h2.stage_entropy:A_twin` |
| `h3.need_share` | `A_twin` | mechanism | -0.0222 | -0.4282 | [-0.0528, +0.0056] | +0.2539 | `cmp:exp_91bbfd2d635b4d85:h3.need_share:A_twin` |
| `h4.parameters` | `A_twin` | descriptive | +0.0000 | not computable | [+0.0000, +0.0000] | +1.0000 | `cmp:exp_91bbfd2d635b4d85:h4.parameters:A_twin` |
| `h4.parameter_delta` | `A_twin` | mechanism | +1.0247 | +0.1696 | [-2.1155, +4.3779] | +0.5684 | `cmp:exp_91bbfd2d635b4d85:h4.parameter_delta:A_twin` |
| `h4.validation_gain` | `A_twin` | function | +0.1628 | +0.4290 | [-0.0413, +0.3716] | +0.1699 | `cmp:exp_91bbfd2d635b4d85:h4.validation_gain:A_twin` |
| `h4.forgetting` | `A_twin` | function | -0.0064 | -0.0394 | [-0.0931, +0.0817] | +0.8867 | `cmp:exp_91bbfd2d635b4d85:h4.forgetting:A_twin` |
| `h4.trainings_accepted` | `A_twin` | descriptive | +0.3333 | +0.2559 | [-0.3333, +1.0833] | +0.5312 | `cmp:exp_91bbfd2d635b4d85:h4.trainings_accepted:A_twin` |
| `h6.question_share` | `A_twin` | descriptive | +0.0028 | +0.2887 | [+0.0000, +0.0083] | +1.0000 | `cmp:exp_91bbfd2d635b4d85:h6.question_share:A_twin` |
| `h6.repetition_rate` | `A_twin` | function | +0.0000 | not computable | [+0.0000, +0.0000] | +1.0000 | `cmp:exp_91bbfd2d635b4d85:h6.repetition_rate:A_twin` |
| `h7.stage_flip_rate` | `A_twin` | mechanism | +0.0056 | +0.2322 | [-0.0083, +0.0167] | +0.6875 | `cmp:exp_91bbfd2d635b4d85:h7.stage_flip_rate:A_twin` |
| `h7.min_valence` | `A_twin` | mechanism | +0.0001 | +0.0519 | [-0.0013, +0.0016] | +0.8198 | `cmp:exp_91bbfd2d635b4d85:h7.min_valence:A_twin` |
| `h9.links_per_sleep` | `A_twin` | descriptive | -0.4583 | -0.2893 | [-1.3750, +0.3750] | +0.3521 | `cmp:exp_91bbfd2d635b4d85:h9.links_per_sleep:A_twin` |
| `h9.replayed_per_sleep` | `A_twin` | descriptive | +0.0000 | not computable | [+0.0000, +0.0000] | +1.0000 | `cmp:exp_91bbfd2d635b4d85:h9.replayed_per_sleep:A_twin` |
| `h9.retention` | `A_twin` | mechanism | -0.0000 | -0.3619 | [-0.0001, +0.0000] | +0.2412 | `cmp:exp_91bbfd2d635b4d85:h9.retention:A_twin` |
| `h1.endogenous_share` | `B` | descriptive | +0.0000 | not computable | [+0.0000, +0.0000] | +1.0000 | `cmp:exp_91bbfd2d635b4d85:h1.endogenous_share:B` |
| `h1.spontaneous_speech_rate` | `B` | descriptive | +0.0000 | not computable | [+0.0000, +0.0000] | +1.0000 | `cmp:exp_91bbfd2d635b4d85:h1.spontaneous_speech_rate:B` |
| `h2.stage_entropy` | `B` | descriptive | +0.0000 | not computable | [+0.0000, +0.0000] | +1.0000 | `cmp:exp_91bbfd2d635b4d85:h2.stage_entropy:B` |
| `h3.need_share` | `B` | mechanism | +0.0000 | not computable | [+0.0000, +0.0000] | +1.0000 | `cmp:exp_91bbfd2d635b4d85:h3.need_share:B` |
| `h4.parameters` | `B` | descriptive | +0.0000 | not computable | [+0.0000, +0.0000] | +1.0000 | `cmp:exp_91bbfd2d635b4d85:h4.parameters:B` |
| `h4.parameter_delta` | `B` | mechanism | +0.0000 | not computable | [+0.0000, +0.0000] | +1.0000 | `cmp:exp_91bbfd2d635b4d85:h4.parameter_delta:B` |
| `h4.validation_gain` | `B` | function | +0.0000 | not computable | [+0.0000, +0.0000] | +1.0000 | `cmp:exp_91bbfd2d635b4d85:h4.validation_gain:B` |
| `h4.forgetting` | `B` | function | +0.0000 | not computable | [+0.0000, +0.0000] | +1.0000 | `cmp:exp_91bbfd2d635b4d85:h4.forgetting:B` |
| `h4.trainings_accepted` | `B` | descriptive | +0.0000 | not computable | [+0.0000, +0.0000] | +1.0000 | `cmp:exp_91bbfd2d635b4d85:h4.trainings_accepted:B` |
| `h6.question_share` | `B` | descriptive | +0.0000 | not computable | [+0.0000, +0.0000] | +1.0000 | `cmp:exp_91bbfd2d635b4d85:h6.question_share:B` |
| `h6.repetition_rate` | `B` | function | +0.0000 | not computable | [+0.0000, +0.0000] | +1.0000 | `cmp:exp_91bbfd2d635b4d85:h6.repetition_rate:B` |
| `h7.stage_flip_rate` | `B` | mechanism | +0.0000 | not computable | [+0.0000, +0.0000] | +1.0000 | `cmp:exp_91bbfd2d635b4d85:h7.stage_flip_rate:B` |
| `h7.min_valence` | `B` | mechanism | +0.0032 | +2.0096 | [+0.0025, +0.0041] | +0.0005 | `cmp:exp_91bbfd2d635b4d85:h7.min_valence:B` |
| `h9.links_per_sleep` | `B` | descriptive | -0.1667 | -0.3755 | [-0.4583, +0.0000] | +0.5000 | `cmp:exp_91bbfd2d635b4d85:h9.links_per_sleep:B` |
| `h9.replayed_per_sleep` | `B` | descriptive | +0.0000 | not computable | [+0.0000, +0.0000] | +1.0000 | `cmp:exp_91bbfd2d635b4d85:h9.replayed_per_sleep:B` |
| `h9.retention` | `B` | mechanism | +0.0000 | +0.2887 | [+0.0000, +0.0000] | +1.0000 | `cmp:exp_91bbfd2d635b4d85:h9.retention:B` |
| `h1.endogenous_share` | `A_no_affect` | descriptive | +0.0000 | not computable | [+0.0000, +0.0000] | +1.0000 | `cmp:exp_91bbfd2d635b4d85:h1.endogenous_share:A_no_affect` |
| `h1.spontaneous_speech_rate` | `A_no_affect` | descriptive | +0.0000 | not computable | [+0.0000, +0.0000] | +1.0000 | `cmp:exp_91bbfd2d635b4d85:h1.spontaneous_speech_rate:A_no_affect` |
| `h2.stage_entropy` | `A_no_affect` | descriptive | -0.1055 | -0.7310 | [-0.1892, -0.0318] | +0.0312 | `cmp:exp_91bbfd2d635b4d85:h2.stage_entropy:A_no_affect` |
| `h3.need_share` | `A_no_affect` | mechanism | -0.0222 | -0.4644 | [-0.0500, -0.0000] | +0.1875 | `cmp:exp_91bbfd2d635b4d85:h3.need_share:A_no_affect` |
| `h4.parameters` | `A_no_affect` | descriptive | +0.0000 | not computable | [+0.0000, +0.0000] | +1.0000 | `cmp:exp_91bbfd2d635b4d85:h4.parameters:A_no_affect` |
| `h4.parameter_delta` | `A_no_affect` | mechanism | -1.6445 | -0.2746 | [-4.7937, +1.7033] | +0.3203 | `cmp:exp_91bbfd2d635b4d85:h4.parameter_delta:A_no_affect` |
| `h4.validation_gain` | `A_no_affect` | function | -0.0618 | -0.4461 | [-0.1390, +0.0106] | +0.1680 | `cmp:exp_91bbfd2d635b4d85:h4.validation_gain:A_no_affect` |
| `h4.forgetting` | `A_no_affect` | function | +0.0436 | +0.3092 | [-0.0275, +0.1215] | +0.3008 | `cmp:exp_91bbfd2d635b4d85:h4.forgetting:A_no_affect` |
| `h4.trainings_accepted` | `A_no_affect` | descriptive | -0.2500 | -0.2369 | [-0.8333, +0.3333] | +0.5938 | `cmp:exp_91bbfd2d635b4d85:h4.trainings_accepted:A_no_affect` |
| `h6.question_share` | `A_no_affect` | descriptive | +0.0000 | not computable | [+0.0000, +0.0000] | +1.0000 | `cmp:exp_91bbfd2d635b4d85:h6.question_share:A_no_affect` |
| `h6.repetition_rate` | `A_no_affect` | function | +0.0000 | not computable | [+0.0000, +0.0000] | +1.0000 | `cmp:exp_91bbfd2d635b4d85:h6.repetition_rate:A_no_affect` |
| `h9.links_per_sleep` | `A_no_affect` | descriptive | -0.4375 | -0.4102 | [-0.9792, +0.1250] | +0.2002 | `cmp:exp_91bbfd2d635b4d85:h9.links_per_sleep:A_no_affect` |
| `h9.replayed_per_sleep` | `A_no_affect` | descriptive | +0.0000 | not computable | [+0.0000, +0.0000] | +1.0000 | `cmp:exp_91bbfd2d635b4d85:h9.replayed_per_sleep:A_no_affect` |
| `h9.retention` | `A_no_affect` | mechanism | -0.0000 | -0.0513 | [-0.0000, +0.0000] | +0.9023 | `cmp:exp_91bbfd2d635b4d85:h9.retention:A_no_affect` |
| `h1.endogenous_share` | `B_no_affect` | descriptive | +0.0000 | not computable | [+0.0000, +0.0000] | +1.0000 | `cmp:exp_91bbfd2d635b4d85:h1.endogenous_share:B_no_affect` |
| `h1.spontaneous_speech_rate` | `B_no_affect` | descriptive | +0.0000 | not computable | [+0.0000, +0.0000] | +1.0000 | `cmp:exp_91bbfd2d635b4d85:h1.spontaneous_speech_rate:B_no_affect` |
| `h2.stage_entropy` | `B_no_affect` | descriptive | -0.1055 | -0.7310 | [-0.1892, -0.0318] | +0.0312 | `cmp:exp_91bbfd2d635b4d85:h2.stage_entropy:B_no_affect` |
| `h3.need_share` | `B_no_affect` | mechanism | -0.0222 | -0.4644 | [-0.0500, -0.0000] | +0.1875 | `cmp:exp_91bbfd2d635b4d85:h3.need_share:B_no_affect` |
| `h4.parameters` | `B_no_affect` | descriptive | +0.0000 | not computable | [+0.0000, +0.0000] | +1.0000 | `cmp:exp_91bbfd2d635b4d85:h4.parameters:B_no_affect` |
| `h4.parameter_delta` | `B_no_affect` | mechanism | -1.6445 | -0.2746 | [-4.7937, +1.7033] | +0.3203 | `cmp:exp_91bbfd2d635b4d85:h4.parameter_delta:B_no_affect` |
| `h4.validation_gain` | `B_no_affect` | function | -0.0618 | -0.4461 | [-0.1390, +0.0106] | +0.1680 | `cmp:exp_91bbfd2d635b4d85:h4.validation_gain:B_no_affect` |
| `h4.forgetting` | `B_no_affect` | function | +0.0436 | +0.3092 | [-0.0275, +0.1215] | +0.3008 | `cmp:exp_91bbfd2d635b4d85:h4.forgetting:B_no_affect` |
| `h4.trainings_accepted` | `B_no_affect` | descriptive | -0.2500 | -0.2369 | [-0.8333, +0.3333] | +0.5938 | `cmp:exp_91bbfd2d635b4d85:h4.trainings_accepted:B_no_affect` |
| `h6.question_share` | `B_no_affect` | descriptive | +0.0000 | not computable | [+0.0000, +0.0000] | +1.0000 | `cmp:exp_91bbfd2d635b4d85:h6.question_share:B_no_affect` |
| `h6.repetition_rate` | `B_no_affect` | function | +0.0000 | not computable | [+0.0000, +0.0000] | +1.0000 | `cmp:exp_91bbfd2d635b4d85:h6.repetition_rate:B_no_affect` |
| `h9.links_per_sleep` | `B_no_affect` | descriptive | -0.4375 | -0.4102 | [-0.9792, +0.1250] | +0.2002 | `cmp:exp_91bbfd2d635b4d85:h9.links_per_sleep:B_no_affect` |
| `h9.replayed_per_sleep` | `B_no_affect` | descriptive | +0.0000 | not computable | [+0.0000, +0.0000] | +1.0000 | `cmp:exp_91bbfd2d635b4d85:h9.replayed_per_sleep:B_no_affect` |
| `h9.retention` | `B_no_affect` | mechanism | -0.0000 | -0.0513 | [-0.0000, +0.0000] | +0.9023 | `cmp:exp_91bbfd2d635b4d85:h9.retention:B_no_affect` |

- `h10.attribution_accuracy`: not computable (the virtual world is off in this condition)
- `h10.prediction_error`: not computable (the virtual world is off in this condition)
- `h7.min_valence`: not computable (the computed affect is off in this condition)
- `h7.probe_valence`: not computable (the computed affect is off in this condition)
- `h7.stage_flip_rate`: not computable (the computed affect is off in this condition)
- `h8.alert`: not computable (the metacognition module is off in this condition)
- `h8.brier`: not computable (the metacognition module is off in this condition)
- `h8.brier_late`: not computable (the metacognition module is off in this condition)

## Qualitative studies

No qualitative case study was recorded for this campaign.

## Anomalies

- 0

## Threats to validity

- The two histories use the same sentences and the same random stream for one seed; only the outcome the experimenter attaches to each sentence differs. The twin, by design, has another random stream. If the histories change nothing, B is closer to A than the twin is, and the excess is negative: that reads as no individuation, not as convergence.

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

To reproduce: `python -m freewill.research run EXP-10` with the same code version recomputes the same results hash.

`results_sha256 = d6c923239ed2053b1ab11acb5117830193f0dbd8c1311c5a852f6cca70d4597a`
