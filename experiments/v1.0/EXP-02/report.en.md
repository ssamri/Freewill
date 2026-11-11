# Research report: EXP-02, Ablation of affect

- Date: 2026-11-11T18:46:35+00:00
- Version: Freewill 1.0.0, Research Lab 1.0.0, commit 679328f829ae
- Author: Freewill Research Lab
- Status: draft, not validated by a person

## Summary

Protocol EXP-02 version 1.0.0 was locked before execution (hash aa3eeb2b352b). 42 experimental lives were copied from one checkpoint T0 (hash bb7a9084039b) and run with the engine “simulated” under a virtual clock. The independent unit is the seed: 6 groups of copies completed out of 6 planned.

For the primary outcome, the interval excludes zero for at least one condition. This is one protocol with a simulated engine; see the threats to validity before reading anything into it.

## Question and hypotheses

**H7. Functional affectivity.** Computed affective states modulate attention, recall, decision and learning. A computed valence is not a feeling. An ablation that changes a wired score shows the wiring, nothing more.

## Preregistration

Primary outcome: h5.heldout_divergence. Secondary outcomes: h2.dismiss_rate, h1.spontaneous_speech_rate, h2.stage_entropy, h3.need_share, h6.repetition_rate, h7.stage_flip_rate. Reference condition: no_affect. The protocol, its conditions, seeds, budget and stopping rule were fixed and hashed before the first run.

## Population and protocol

Each life starts as an exact copy of T0. During the history phase it follows the script of its condition; during the probe phase every life follows the same script, with the same random stream. Metrics are computed on the probe phase by the code of the lab (metrics version 1.0, statistics version 1.0).

## Conditions and seeds

- `no_affect`: `{"history": "questions_welcomed"}`
- `no_affect_twin`: `{"history": "questions_welcomed", "seed_offset": 1000}`
- `narrative_affect`: `{"history": "questions_welcomed", "scripted_emotion": true}`
- `h7_full`: `{"history": "questions_welcomed", "affect": true}`
- `h7_no_recall`: `{"history": "questions_welcomed", "affect": true, "affect_config": {"modulate_recall": false}}`
- `h7_no_salience`: `{"history": "questions_welcomed", "affect": true, "affect_config": {"modulate_salience": false}}`
- `h7_no_slow`: `{"history": "questions_welcomed", "affect": true, "affect_config": {"slow_rate": 0.0}}`

`seeds = [11, 23, 37, 51, 73, 89]`

## Statistics

Comparisons are paired by seed. The effect size is the mean difference divided by the standard deviation of the differences. Intervals are percentile bootstrap intervals with a fixed seed and are given only from 5 units; the paired sign-flip test only from 6 units. No correction for multiple comparisons is applied: secondary comparisons are exploratory.

## Results

### Held-out behavioural divergence (primary)

| Condition | Mean distance | Excess over twin | 95% interval | Paired test | Evidence |
|---|---|---|---|---|---|
| `narrative_affect` | +0.0000 | -0.0068 | [-0.0111, -0.0034] | +0.0625 | `h5:exp_81336b1ade5f40a4:narrative_affect` |
| `h7_full` | +0.0077 | +0.0009 | [-0.0034, +0.0060] | +1.0000 | `h5:exp_81336b1ade5f40a4:h7_full` |
| `h7_no_recall` | +0.0077 | +0.0009 | [-0.0034, +0.0060] | +1.0000 | `h5:exp_81336b1ade5f40a4:h7_no_recall` |
| `h7_no_salience` | +0.0060 | -0.0009 | [-0.0077, +0.0060] | +1.0000 | `h5:exp_81336b1ade5f40a4:h7_no_salience` |
| `h7_no_slow` | +0.0077 | +0.0009 | [-0.0034, +0.0060] | +1.0000 | `h5:exp_81336b1ade5f40a4:h7_no_slow` |

### Preregistered outcomes, paired with the reference

Rows of level “mechanism” show that a wiring does what it was built to do. They are not discoveries.

| Metric | Condition | Level | Mean difference | Effect size | 95% interval | Paired test | Evidence |
|---|---|---|---|---|---|---|---|
| `h1.spontaneous_speech_rate` | `no_affect_twin` | descriptive | +0.0000 | not computable | [+0.0000, +0.0000] | +1.0000 | `cmp:exp_81336b1ade5f40a4:h1.spontaneous_speech_rate:no_affect_twin` |
| `h2.stage_entropy` | `no_affect_twin` | descriptive | +0.0863 | +0.3545 | [-0.0837, +0.2621] | +0.4375 | `cmp:exp_81336b1ade5f40a4:h2.stage_entropy:no_affect_twin` |
| `h2.dismiss_rate` | `no_affect_twin` | descriptive | +0.0000 | not computable | [+0.0000, +0.0000] | +1.0000 | `cmp:exp_81336b1ade5f40a4:h2.dismiss_rate:no_affect_twin` |
| `h3.need_share` | `no_affect_twin` | mechanism | +0.0000 | +0.0000 | [-0.0222, +0.0278] | +1.0000 | `cmp:exp_81336b1ade5f40a4:h3.need_share:no_affect_twin` |
| `h6.repetition_rate` | `no_affect_twin` | function | +0.0000 | not computable | [+0.0000, +0.0000] | +1.0000 | `cmp:exp_81336b1ade5f40a4:h6.repetition_rate:no_affect_twin` |
| `h1.spontaneous_speech_rate` | `narrative_affect` | descriptive | +0.0000 | not computable | [+0.0000, +0.0000] | +1.0000 | `cmp:exp_81336b1ade5f40a4:h1.spontaneous_speech_rate:narrative_affect` |
| `h2.stage_entropy` | `narrative_affect` | descriptive | +0.0000 | not computable | [+0.0000, +0.0000] | +1.0000 | `cmp:exp_81336b1ade5f40a4:h2.stage_entropy:narrative_affect` |
| `h2.dismiss_rate` | `narrative_affect` | descriptive | +0.0000 | not computable | [+0.0000, +0.0000] | +1.0000 | `cmp:exp_81336b1ade5f40a4:h2.dismiss_rate:narrative_affect` |
| `h3.need_share` | `narrative_affect` | mechanism | +0.0000 | not computable | [+0.0000, +0.0000] | +1.0000 | `cmp:exp_81336b1ade5f40a4:h3.need_share:narrative_affect` |
| `h6.repetition_rate` | `narrative_affect` | function | +0.0000 | not computable | [+0.0000, +0.0000] | +1.0000 | `cmp:exp_81336b1ade5f40a4:h6.repetition_rate:narrative_affect` |
| `h1.spontaneous_speech_rate` | `h7_full` | descriptive | +0.0000 | not computable | [+0.0000, +0.0000] | +1.0000 | `cmp:exp_81336b1ade5f40a4:h1.spontaneous_speech_rate:h7_full` |
| `h2.stage_entropy` | `h7_full` | descriptive | +0.1197 | +0.4764 | [-0.0380, +0.3208] | +0.5000 | `cmp:exp_81336b1ade5f40a4:h2.stage_entropy:h7_full` |
| `h2.dismiss_rate` | `h7_full` | descriptive | +0.0000 | not computable | [+0.0000, +0.0000] | +1.0000 | `cmp:exp_81336b1ade5f40a4:h2.dismiss_rate:h7_full` |
| `h3.need_share` | `h7_full` | mechanism | +0.0000 | +0.0000 | [-0.0222, +0.0278] | +1.0000 | `cmp:exp_81336b1ade5f40a4:h3.need_share:h7_full` |
| `h6.repetition_rate` | `h7_full` | function | +0.0000 | not computable | [+0.0000, +0.0000] | +1.0000 | `cmp:exp_81336b1ade5f40a4:h6.repetition_rate:h7_full` |
| `h1.spontaneous_speech_rate` | `h7_no_recall` | descriptive | +0.0000 | not computable | [+0.0000, +0.0000] | +1.0000 | `cmp:exp_81336b1ade5f40a4:h1.spontaneous_speech_rate:h7_no_recall` |
| `h2.stage_entropy` | `h7_no_recall` | descriptive | +0.1197 | +0.4764 | [-0.0380, +0.3208] | +0.5000 | `cmp:exp_81336b1ade5f40a4:h2.stage_entropy:h7_no_recall` |
| `h2.dismiss_rate` | `h7_no_recall` | descriptive | +0.0000 | not computable | [+0.0000, +0.0000] | +1.0000 | `cmp:exp_81336b1ade5f40a4:h2.dismiss_rate:h7_no_recall` |
| `h3.need_share` | `h7_no_recall` | mechanism | +0.0000 | +0.0000 | [-0.0222, +0.0278] | +1.0000 | `cmp:exp_81336b1ade5f40a4:h3.need_share:h7_no_recall` |
| `h6.repetition_rate` | `h7_no_recall` | function | +0.0000 | not computable | [+0.0000, +0.0000] | +1.0000 | `cmp:exp_81336b1ade5f40a4:h6.repetition_rate:h7_no_recall` |
| `h1.spontaneous_speech_rate` | `h7_no_salience` | descriptive | +0.0000 | not computable | [+0.0000, +0.0000] | +1.0000 | `cmp:exp_81336b1ade5f40a4:h1.spontaneous_speech_rate:h7_no_salience` |
| `h2.stage_entropy` | `h7_no_salience` | descriptive | +0.0927 | +0.4917 | [-0.0338, +0.2313] | +0.5000 | `cmp:exp_81336b1ade5f40a4:h2.stage_entropy:h7_no_salience` |
| `h2.dismiss_rate` | `h7_no_salience` | descriptive | +0.0000 | not computable | [+0.0000, +0.0000] | +1.0000 | `cmp:exp_81336b1ade5f40a4:h2.dismiss_rate:h7_no_salience` |
| `h3.need_share` | `h7_no_salience` | mechanism | -0.0056 | -0.4082 | [-0.0167, +0.0000] | +1.0000 | `cmp:exp_81336b1ade5f40a4:h3.need_share:h7_no_salience` |
| `h6.repetition_rate` | `h7_no_salience` | function | +0.0000 | not computable | [+0.0000, +0.0000] | +1.0000 | `cmp:exp_81336b1ade5f40a4:h6.repetition_rate:h7_no_salience` |
| `h1.spontaneous_speech_rate` | `h7_no_slow` | descriptive | +0.0000 | not computable | [+0.0000, +0.0000] | +1.0000 | `cmp:exp_81336b1ade5f40a4:h1.spontaneous_speech_rate:h7_no_slow` |
| `h2.stage_entropy` | `h7_no_slow` | descriptive | +0.1197 | +0.4764 | [-0.0380, +0.3208] | +0.5000 | `cmp:exp_81336b1ade5f40a4:h2.stage_entropy:h7_no_slow` |
| `h2.dismiss_rate` | `h7_no_slow` | descriptive | +0.0000 | not computable | [+0.0000, +0.0000] | +1.0000 | `cmp:exp_81336b1ade5f40a4:h2.dismiss_rate:h7_no_slow` |
| `h3.need_share` | `h7_no_slow` | mechanism | +0.0000 | +0.0000 | [-0.0222, +0.0278] | +1.0000 | `cmp:exp_81336b1ade5f40a4:h3.need_share:h7_no_slow` |
| `h6.repetition_rate` | `h7_no_slow` | function | +0.0000 | not computable | [+0.0000, +0.0000] | +1.0000 | `cmp:exp_81336b1ade5f40a4:h6.repetition_rate:h7_no_slow` |

### Other metrics, exploratory

These metrics were not preregistered for this protocol. They are given for completeness and support no conclusion.

| Metric | Condition | Level | Mean difference | Effect size | 95% interval | Paired test | Evidence |
|---|---|---|---|---|---|---|---|
| `h1.endogenous_share` | `no_affect_twin` | descriptive | +0.0000 | not computable | [+0.0000, +0.0000] | +1.0000 | `cmp:exp_81336b1ade5f40a4:h1.endogenous_share:no_affect_twin` |
| `h6.question_share` | `no_affect_twin` | descriptive | +0.0000 | not computable | [+0.0000, +0.0000] | +1.0000 | `cmp:exp_81336b1ade5f40a4:h6.question_share:no_affect_twin` |
| `h9.links_per_sleep` | `no_affect_twin` | descriptive | -0.1667 | -0.1695 | [-1.0000, +0.5000] | +1.0000 | `cmp:exp_81336b1ade5f40a4:h9.links_per_sleep:no_affect_twin` |
| `h9.replayed_per_sleep` | `no_affect_twin` | descriptive | +0.0000 | not computable | [+0.0000, +0.0000] | +1.0000 | `cmp:exp_81336b1ade5f40a4:h9.replayed_per_sleep:no_affect_twin` |
| `h9.retention` | `no_affect_twin` | mechanism | +0.0000 | +0.1059 | [-0.0000, +0.0000] | +1.0000 | `cmp:exp_81336b1ade5f40a4:h9.retention:no_affect_twin` |
| `h1.endogenous_share` | `narrative_affect` | descriptive | +0.0000 | not computable | [+0.0000, +0.0000] | +1.0000 | `cmp:exp_81336b1ade5f40a4:h1.endogenous_share:narrative_affect` |
| `h6.question_share` | `narrative_affect` | descriptive | +0.0000 | not computable | [+0.0000, +0.0000] | +1.0000 | `cmp:exp_81336b1ade5f40a4:h6.question_share:narrative_affect` |
| `h9.links_per_sleep` | `narrative_affect` | descriptive | +0.0000 | not computable | [+0.0000, +0.0000] | +1.0000 | `cmp:exp_81336b1ade5f40a4:h9.links_per_sleep:narrative_affect` |
| `h9.replayed_per_sleep` | `narrative_affect` | descriptive | +0.0000 | not computable | [+0.0000, +0.0000] | +1.0000 | `cmp:exp_81336b1ade5f40a4:h9.replayed_per_sleep:narrative_affect` |
| `h9.retention` | `narrative_affect` | mechanism | +0.0000 | not computable | [+0.0000, +0.0000] | +1.0000 | `cmp:exp_81336b1ade5f40a4:h9.retention:narrative_affect` |
| `h1.endogenous_share` | `h7_full` | descriptive | +0.0000 | not computable | [+0.0000, +0.0000] | +1.0000 | `cmp:exp_81336b1ade5f40a4:h1.endogenous_share:h7_full` |
| `h6.question_share` | `h7_full` | descriptive | +0.0000 | not computable | [+0.0000, +0.0000] | +1.0000 | `cmp:exp_81336b1ade5f40a4:h6.question_share:h7_full` |
| `h9.links_per_sleep` | `h7_full` | descriptive | +0.1667 | +0.0816 | [-1.1667, +1.8333] | +1.0000 | `cmp:exp_81336b1ade5f40a4:h9.links_per_sleep:h7_full` |
| `h9.replayed_per_sleep` | `h7_full` | descriptive | +0.0000 | not computable | [+0.0000, +0.0000] | +1.0000 | `cmp:exp_81336b1ade5f40a4:h9.replayed_per_sleep:h7_full` |
| `h9.retention` | `h7_full` | mechanism | +0.0000 | +0.7931 | [+0.0000, +0.0000] | +0.2500 | `cmp:exp_81336b1ade5f40a4:h9.retention:h7_full` |
| `h1.endogenous_share` | `h7_no_recall` | descriptive | +0.0000 | not computable | [+0.0000, +0.0000] | +1.0000 | `cmp:exp_81336b1ade5f40a4:h1.endogenous_share:h7_no_recall` |
| `h6.question_share` | `h7_no_recall` | descriptive | +0.0000 | not computable | [+0.0000, +0.0000] | +1.0000 | `cmp:exp_81336b1ade5f40a4:h6.question_share:h7_no_recall` |
| `h9.links_per_sleep` | `h7_no_recall` | descriptive | +0.1667 | +0.0816 | [-1.1667, +1.8333] | +1.0000 | `cmp:exp_81336b1ade5f40a4:h9.links_per_sleep:h7_no_recall` |
| `h9.replayed_per_sleep` | `h7_no_recall` | descriptive | +0.0000 | not computable | [+0.0000, +0.0000] | +1.0000 | `cmp:exp_81336b1ade5f40a4:h9.replayed_per_sleep:h7_no_recall` |
| `h9.retention` | `h7_no_recall` | mechanism | +0.0000 | +0.7931 | [+0.0000, +0.0000] | +0.2500 | `cmp:exp_81336b1ade5f40a4:h9.retention:h7_no_recall` |
| `h1.endogenous_share` | `h7_no_salience` | descriptive | +0.0000 | not computable | [+0.0000, +0.0000] | +1.0000 | `cmp:exp_81336b1ade5f40a4:h1.endogenous_share:h7_no_salience` |
| `h6.question_share` | `h7_no_salience` | descriptive | +0.0000 | not computable | [+0.0000, +0.0000] | +1.0000 | `cmp:exp_81336b1ade5f40a4:h6.question_share:h7_no_salience` |
| `h9.links_per_sleep` | `h7_no_salience` | descriptive | -0.8333 | -0.6270 | [-1.8333, +0.0000] | +0.5000 | `cmp:exp_81336b1ade5f40a4:h9.links_per_sleep:h7_no_salience` |
| `h9.replayed_per_sleep` | `h7_no_salience` | descriptive | +0.0000 | not computable | [+0.0000, +0.0000] | +1.0000 | `cmp:exp_81336b1ade5f40a4:h9.replayed_per_sleep:h7_no_salience` |
| `h9.retention` | `h7_no_salience` | mechanism | +0.0000 | +0.4082 | [+0.0000, +0.0000] | +1.0000 | `cmp:exp_81336b1ade5f40a4:h9.retention:h7_no_salience` |
| `h1.endogenous_share` | `h7_no_slow` | descriptive | +0.0000 | not computable | [+0.0000, +0.0000] | +1.0000 | `cmp:exp_81336b1ade5f40a4:h1.endogenous_share:h7_no_slow` |
| `h6.question_share` | `h7_no_slow` | descriptive | +0.0000 | not computable | [+0.0000, +0.0000] | +1.0000 | `cmp:exp_81336b1ade5f40a4:h6.question_share:h7_no_slow` |
| `h9.links_per_sleep` | `h7_no_slow` | descriptive | +0.1667 | +0.0816 | [-1.1667, +1.8333] | +1.0000 | `cmp:exp_81336b1ade5f40a4:h9.links_per_sleep:h7_no_slow` |
| `h9.replayed_per_sleep` | `h7_no_slow` | descriptive | +0.0000 | not computable | [+0.0000, +0.0000] | +1.0000 | `cmp:exp_81336b1ade5f40a4:h9.replayed_per_sleep:h7_no_slow` |
| `h9.retention` | `h7_no_slow` | mechanism | +0.0000 | +0.7931 | [+0.0000, +0.0000] | +0.2500 | `cmp:exp_81336b1ade5f40a4:h9.retention:h7_no_slow` |

- `h10.attribution_accuracy`: not computable (the virtual world is off in this condition)
- `h10.prediction_error`: not computable (the virtual world is off in this condition)
- `h4.forgetting`: not computable (the trainable module is off in this condition)
- `h4.parameter_delta`: not computable (the trainable module is off in this condition)
- `h4.parameters`: not computable (the trainable module is off in this condition)
- `h4.trainings_accepted`: not computable (the trainable module is off in this condition)
- `h4.validation_gain`: not computable (the trainable module is off in this condition)
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

To reproduce: `python -m freewill.research run EXP-02` with the same code version recomputes the same results hash.

`results_sha256 = 733c67362655aa64e7e0e0c2e9bd5fdfcdce789edd57db71fd3df59e2009e2fb`
