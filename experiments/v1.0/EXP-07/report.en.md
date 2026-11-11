# Research report: EXP-07, Agency in a virtual world

- Date: 2026-11-11T18:47:35+00:00
- Version: Freewill 1.0.0, Research Lab 1.0.0, commit 679328f829ae
- Author: Freewill Research Lab
- Status: draft, not validated by a person

## Summary

Protocol EXP-07 version 1.0.0 was locked before execution (hash c855559c7bfc). 30 experimental lives were copied from one checkpoint T0 (hash bb7a9084039b) and run with the engine “simulated” under a virtual clock. The independent unit is the seed: 6 groups of copies completed out of 6 planned.

For the primary outcome, the interval excludes zero for at least one condition. This is one protocol with a simulated engine; see the threats to validity before reading anything into it.

## Question and hypotheses

**H10. Self-model and agency.** A model of itself and of a world learns the consequences of its acts. The being acts in a tiny closed grid world and attributes changes with a table of what its acts did before. The world is very small and the comparison is with a deliberately naive attribution.

## Preregistration

Primary outcome: h10.attribution_accuracy. Secondary outcomes: h10.prediction_error. Reference condition: no_self_model. The protocol, its conditions, seeds, budget and stopping rule were fixed and hashed before the first run.

## Population and protocol

Each life starts as an exact copy of T0. During the history phase it follows the script of its condition; during the probe phase every life follows the same script, with the same random stream. Metrics are computed on the probe phase by the code of the lab (metrics version 1.0, statistics version 1.0).

## Conditions and seeds

- `no_self_model`: `{"history": "quiet", "research": {"sandbox": true, "self_model": false}, "agency": {"exogenous": 0.25}}`
- `self_model`: `{"history": "quiet", "research": {"sandbox": true}, "agency": {"exogenous": 0.25}}`
- `self_model_calm`: `{"history": "quiet", "research": {"sandbox": true}, "agency": {"exogenous": 0.0}}`
- `self_model_noisy_senses`: `{"history": "quiet", "research": {"sandbox": true}, "agency": {"exogenous": 0.25, "noise": 0.2}}`
- `self_model_rule_change`: `{"history": "quiet", "research": {"sandbox": true}, "agency": {"exogenous": 0.25, "break_action": "east", "break_after": 60}}`

`seeds = [11, 23, 37, 51, 73, 89]`

## Statistics

Comparisons are paired by seed. The effect size is the mean difference divided by the standard deviation of the differences. Intervals are percentile bootstrap intervals with a fixed seed and are given only from 5 units; the paired sign-flip test only from 6 units. No correction for multiple comparisons is applied: secondary comparisons are exploratory.

## Results

### Preregistered outcomes, paired with the reference

Rows of level “mechanism” show that a wiring does what it was built to do. They are not discoveries.

| Metric | Condition | Level | Mean difference | Effect size | 95% interval | Paired test | Evidence |
|---|---|---|---|---|---|---|---|
| `h10.attribution_accuracy` (primary) | `self_model` | function | +0.2833 | +2.1947 | [+0.1917, +0.3708] | +0.0312 | `cmp:exp_afe3f73dc0d94e26:h10.attribution_accuracy:self_model` |
| `h10.attribution_accuracy` (primary) | `self_model_calm` | function | +0.3500 | +7.3786 | [+0.3167, +0.3833] | +0.0312 | `cmp:exp_afe3f73dc0d94e26:h10.attribution_accuracy:self_model_calm` |
| `h10.attribution_accuracy` (primary) | `self_model_noisy_senses` | function | -0.2958 | -3.1005 | [-0.3542, -0.2208] | +0.0312 | `cmp:exp_afe3f73dc0d94e26:h10.attribution_accuracy:self_model_noisy_senses` |
| `h10.attribution_accuracy` (primary) | `self_model_rule_change` | function | +0.3083 | +2.9510 | [+0.2250, +0.3750] | +0.0312 | `cmp:exp_afe3f73dc0d94e26:h10.attribution_accuracy:self_model_rule_change` |

### Other metrics, exploratory

These metrics were not preregistered for this protocol. They are given for completeness and support no conclusion.

| Metric | Condition | Level | Mean difference | Effect size | 95% interval | Paired test | Evidence |
|---|---|---|---|---|---|---|---|
| `h1.endogenous_share` | `self_model` | descriptive | +0.0000 | not computable | [+0.0000, +0.0000] | +1.0000 | `cmp:exp_afe3f73dc0d94e26:h1.endogenous_share:self_model` |
| `h1.spontaneous_speech_rate` | `self_model` | descriptive | +0.0000 | not computable | [+0.0000, +0.0000] | +1.0000 | `cmp:exp_afe3f73dc0d94e26:h1.spontaneous_speech_rate:self_model` |
| `h2.stage_entropy` | `self_model` | descriptive | +0.0000 | not computable | [+0.0000, +0.0000] | +1.0000 | `cmp:exp_afe3f73dc0d94e26:h2.stage_entropy:self_model` |
| `h2.dismiss_rate` | `self_model` | descriptive | +0.0000 | not computable | [+0.0000, +0.0000] | +1.0000 | `cmp:exp_afe3f73dc0d94e26:h2.dismiss_rate:self_model` |
| `h3.need_share` | `self_model` | mechanism | +0.0000 | not computable | [+0.0000, +0.0000] | +1.0000 | `cmp:exp_afe3f73dc0d94e26:h3.need_share:self_model` |
| `h6.question_share` | `self_model` | descriptive | +0.0000 | not computable | [+0.0000, +0.0000] | +1.0000 | `cmp:exp_afe3f73dc0d94e26:h6.question_share:self_model` |
| `h6.repetition_rate` | `self_model` | function | +0.0000 | not computable | [+0.0000, +0.0000] | +1.0000 | `cmp:exp_afe3f73dc0d94e26:h6.repetition_rate:self_model` |
| `h1.endogenous_share` | `self_model_calm` | descriptive | +0.0000 | not computable | [+0.0000, +0.0000] | +1.0000 | `cmp:exp_afe3f73dc0d94e26:h1.endogenous_share:self_model_calm` |
| `h1.spontaneous_speech_rate` | `self_model_calm` | descriptive | +0.0000 | not computable | [+0.0000, +0.0000] | +1.0000 | `cmp:exp_afe3f73dc0d94e26:h1.spontaneous_speech_rate:self_model_calm` |
| `h2.stage_entropy` | `self_model_calm` | descriptive | +0.0000 | not computable | [+0.0000, +0.0000] | +1.0000 | `cmp:exp_afe3f73dc0d94e26:h2.stage_entropy:self_model_calm` |
| `h2.dismiss_rate` | `self_model_calm` | descriptive | +0.0000 | not computable | [+0.0000, +0.0000] | +1.0000 | `cmp:exp_afe3f73dc0d94e26:h2.dismiss_rate:self_model_calm` |
| `h3.need_share` | `self_model_calm` | mechanism | +0.0000 | not computable | [+0.0000, +0.0000] | +1.0000 | `cmp:exp_afe3f73dc0d94e26:h3.need_share:self_model_calm` |
| `h6.question_share` | `self_model_calm` | descriptive | +0.0000 | not computable | [+0.0000, +0.0000] | +1.0000 | `cmp:exp_afe3f73dc0d94e26:h6.question_share:self_model_calm` |
| `h6.repetition_rate` | `self_model_calm` | function | +0.0000 | not computable | [+0.0000, +0.0000] | +1.0000 | `cmp:exp_afe3f73dc0d94e26:h6.repetition_rate:self_model_calm` |
| `h1.endogenous_share` | `self_model_noisy_senses` | descriptive | +0.0000 | not computable | [+0.0000, +0.0000] | +1.0000 | `cmp:exp_afe3f73dc0d94e26:h1.endogenous_share:self_model_noisy_senses` |
| `h1.spontaneous_speech_rate` | `self_model_noisy_senses` | descriptive | +0.0000 | not computable | [+0.0000, +0.0000] | +1.0000 | `cmp:exp_afe3f73dc0d94e26:h1.spontaneous_speech_rate:self_model_noisy_senses` |
| `h2.stage_entropy` | `self_model_noisy_senses` | descriptive | +0.0000 | not computable | [+0.0000, +0.0000] | +1.0000 | `cmp:exp_afe3f73dc0d94e26:h2.stage_entropy:self_model_noisy_senses` |
| `h2.dismiss_rate` | `self_model_noisy_senses` | descriptive | +0.0000 | not computable | [+0.0000, +0.0000] | +1.0000 | `cmp:exp_afe3f73dc0d94e26:h2.dismiss_rate:self_model_noisy_senses` |
| `h3.need_share` | `self_model_noisy_senses` | mechanism | +0.0000 | not computable | [+0.0000, +0.0000] | +1.0000 | `cmp:exp_afe3f73dc0d94e26:h3.need_share:self_model_noisy_senses` |
| `h6.question_share` | `self_model_noisy_senses` | descriptive | +0.0000 | not computable | [+0.0000, +0.0000] | +1.0000 | `cmp:exp_afe3f73dc0d94e26:h6.question_share:self_model_noisy_senses` |
| `h6.repetition_rate` | `self_model_noisy_senses` | function | +0.0000 | not computable | [+0.0000, +0.0000] | +1.0000 | `cmp:exp_afe3f73dc0d94e26:h6.repetition_rate:self_model_noisy_senses` |
| `h1.endogenous_share` | `self_model_rule_change` | descriptive | +0.0000 | not computable | [+0.0000, +0.0000] | +1.0000 | `cmp:exp_afe3f73dc0d94e26:h1.endogenous_share:self_model_rule_change` |
| `h1.spontaneous_speech_rate` | `self_model_rule_change` | descriptive | +0.0000 | not computable | [+0.0000, +0.0000] | +1.0000 | `cmp:exp_afe3f73dc0d94e26:h1.spontaneous_speech_rate:self_model_rule_change` |
| `h2.stage_entropy` | `self_model_rule_change` | descriptive | +0.0000 | not computable | [+0.0000, +0.0000] | +1.0000 | `cmp:exp_afe3f73dc0d94e26:h2.stage_entropy:self_model_rule_change` |
| `h2.dismiss_rate` | `self_model_rule_change` | descriptive | +0.0000 | not computable | [+0.0000, +0.0000] | +1.0000 | `cmp:exp_afe3f73dc0d94e26:h2.dismiss_rate:self_model_rule_change` |
| `h3.need_share` | `self_model_rule_change` | mechanism | +0.0000 | not computable | [+0.0000, +0.0000] | +1.0000 | `cmp:exp_afe3f73dc0d94e26:h3.need_share:self_model_rule_change` |
| `h6.question_share` | `self_model_rule_change` | descriptive | +0.0000 | not computable | [+0.0000, +0.0000] | +1.0000 | `cmp:exp_afe3f73dc0d94e26:h6.question_share:self_model_rule_change` |
| `h6.repetition_rate` | `self_model_rule_change` | function | +0.0000 | not computable | [+0.0000, +0.0000] | +1.0000 | `cmp:exp_afe3f73dc0d94e26:h6.repetition_rate:self_model_rule_change` |

- `h10.prediction_error`: not computable (nothing to measure in this run)
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
- `h9.links_per_sleep`: not computable (no sleep in this run)
- `h9.replayed_per_sleep`: not computable (no sleep in this run)
- `h9.retention`: not computable (no memory was formed before the sleep)

## Qualitative studies

No qualitative case study was recorded for this campaign.

## Anomalies

- 0

## Threats to validity

- The world is a five-by-five grid with one object. The comparison is with an attribution that takes every change for its own doing, which is easy to beat.

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

To reproduce: `python -m freewill.research run EXP-07` with the same code version recomputes the same results hash.

`results_sha256 = 23b323c653c3303682917ff6ea5200d14b94d9c201314245759cea69ca0ce911`
