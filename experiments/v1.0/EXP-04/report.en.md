# Research report: EXP-04, Controlled consolidation

- Date: 2026-11-11T18:47:15+00:00
- Version: Freewill 1.0.0, Research Lab 1.0.0, commit 679328f829ae
- Author: Freewill Research Lab
- Status: draft, not validated by a person

## Summary

Protocol EXP-04 version 1.0.0 was locked before execution (hash f15a8992440f). 30 experimental lives were copied from one checkpoint T0 (hash bb7a9084039b) and run with the engine “simulated” under a virtual clock. The independent unit is the seed: 6 groups of copies completed out of 6 planned.

For the primary outcome, the interval excludes zero for at least one condition. This is one protocol with a simulated engine; see the threats to validity before reading anything into it.

## Question and hypotheses

**H9. Offline consolidation.** Consolidation during sleep improves retention and transfer at equal computation. Sleep runs in phases (rest, replay, dream, consolidation) that can be removed one by one. Retention is measured as the strength of memories after a delay, which follows from the rule that replay strengthens; no task yet measures transfer.

## Preregistration

Primary outcome: h9.retention. Secondary outcomes: h9.replayed_per_sleep, h9.links_per_sleep, tech.engine_calls. Reference condition: no_sleep. The protocol, its conditions, seeds, budget and stopping rule were fixed and hashed before the first run.

## Population and protocol

Each life starts as an exact copy of T0. During the history phase it follows the script of its condition; during the probe phase every life follows the same script, with the same random stream. Metrics are computed on the probe phase by the code of the lab (metrics version 1.0, statistics version 1.0).

## Conditions and seeds

- `no_sleep`: `{"history": "told_then_delay", "skip_sleep": true, "research": {"auto_sleep": false}}`
- `rest_only`: `{"history": "told_then_delay", "research": {"auto_sleep": false, "dreaming": false, "sleep_replay": false}}`
- `replay_only`: `{"history": "told_then_delay", "research": {"auto_sleep": false, "dreaming": false}}`
- `dream_only`: `{"history": "told_then_delay", "research": {"auto_sleep": false, "sleep_replay": false}}`
- `full_sleep`: `{"history": "told_then_delay", "research": {"auto_sleep": false}}`

`seeds = [11, 23, 37, 51, 73, 89]`

## Statistics

Comparisons are paired by seed. The effect size is the mean difference divided by the standard deviation of the differences. Intervals are percentile bootstrap intervals with a fixed seed and are given only from 5 units; the paired sign-flip test only from 6 units. No correction for multiple comparisons is applied: secondary comparisons are exploratory.

## Results

### Preregistered outcomes, paired with the reference

Rows of level “mechanism” show that a wiring does what it was built to do. They are not discoveries.

| Metric | Condition | Level | Mean difference | Effect size | 95% interval | Paired test | Evidence |
|---|---|---|---|---|---|---|---|
| `h9.retention` (primary) | `rest_only` | mechanism | -0.0149 | -2.3777 | [-0.0191, -0.0105] | +0.0312 | `cmp:exp_2664ff5b0ef947c8:h9.retention:rest_only` |
| `tech.engine_calls` | `rest_only` | descriptive | -1.0000 | not computable | [-1.0000, -1.0000] | +0.0312 | `cmp:exp_2664ff5b0ef947c8:tech.engine_calls:rest_only` |
| `h9.retention` (primary) | `replay_only` | mechanism | +0.0060 | +0.6341 | [-0.0005, +0.0132] | +0.2188 | `cmp:exp_2664ff5b0ef947c8:h9.retention:replay_only` |
| `tech.engine_calls` | `replay_only` | descriptive | -1.0000 | not computable | [-1.0000, -1.0000] | +0.0312 | `cmp:exp_2664ff5b0ef947c8:tech.engine_calls:replay_only` |
| `h9.retention` (primary) | `dream_only` | mechanism | -0.0139 | -1.4238 | [-0.0215, -0.0074] | +0.0312 | `cmp:exp_2664ff5b0ef947c8:h9.retention:dream_only` |
| `tech.engine_calls` | `dream_only` | descriptive | +1.0000 | not computable | [+1.0000, +1.0000] | +0.0312 | `cmp:exp_2664ff5b0ef947c8:tech.engine_calls:dream_only` |
| `h9.retention` (primary) | `full_sleep` | mechanism | +0.0060 | +0.6341 | [-0.0005, +0.0132] | +0.2188 | `cmp:exp_2664ff5b0ef947c8:h9.retention:full_sleep` |
| `tech.engine_calls` | `full_sleep` | descriptive | +1.0000 | not computable | [+1.0000, +1.0000] | +0.0312 | `cmp:exp_2664ff5b0ef947c8:tech.engine_calls:full_sleep` |

### Other metrics, exploratory

These metrics were not preregistered for this protocol. They are given for completeness and support no conclusion.

| Metric | Condition | Level | Mean difference | Effect size | 95% interval | Paired test | Evidence |
|---|---|---|---|---|---|---|---|
| `h1.endogenous_share` | `rest_only` | descriptive | +0.0000 | not computable | [+0.0000, +0.0000] | +1.0000 | `cmp:exp_2664ff5b0ef947c8:h1.endogenous_share:rest_only` |
| `h1.spontaneous_speech_rate` | `rest_only` | descriptive | +0.0000 | not computable | [+0.0000, +0.0000] | +1.0000 | `cmp:exp_2664ff5b0ef947c8:h1.spontaneous_speech_rate:rest_only` |
| `h2.stage_entropy` | `rest_only` | descriptive | +0.0070 | +0.0379 | [-0.1256, +0.1395] | +1.0000 | `cmp:exp_2664ff5b0ef947c8:h2.stage_entropy:rest_only` |
| `h2.dismiss_rate` | `rest_only` | descriptive | +0.0000 | not computable | [+0.0000, +0.0000] | +1.0000 | `cmp:exp_2664ff5b0ef947c8:h2.dismiss_rate:rest_only` |
| `h3.need_share` | `rest_only` | mechanism | +0.0056 | +0.1695 | [-0.0167, +0.0333] | +1.0000 | `cmp:exp_2664ff5b0ef947c8:h3.need_share:rest_only` |
| `h6.question_share` | `rest_only` | descriptive | +0.0111 | +0.6455 | [+0.0000, +0.0222] | +0.5000 | `cmp:exp_2664ff5b0ef947c8:h6.question_share:rest_only` |
| `h6.repetition_rate` | `rest_only` | function | +0.0000 | not computable | [+0.0000, +0.0000] | +1.0000 | `cmp:exp_2664ff5b0ef947c8:h6.repetition_rate:rest_only` |
| `h1.endogenous_share` | `replay_only` | descriptive | +0.0000 | not computable | [+0.0000, +0.0000] | +1.0000 | `cmp:exp_2664ff5b0ef947c8:h1.endogenous_share:replay_only` |
| `h1.spontaneous_speech_rate` | `replay_only` | descriptive | +0.0000 | not computable | [+0.0000, +0.0000] | +1.0000 | `cmp:exp_2664ff5b0ef947c8:h1.spontaneous_speech_rate:replay_only` |
| `h2.stage_entropy` | `replay_only` | descriptive | +0.0270 | +0.1428 | [-0.1055, +0.1566] | +0.7500 | `cmp:exp_2664ff5b0ef947c8:h2.stage_entropy:replay_only` |
| `h2.dismiss_rate` | `replay_only` | descriptive | +0.0000 | not computable | [+0.0000, +0.0000] | +1.0000 | `cmp:exp_2664ff5b0ef947c8:h2.dismiss_rate:replay_only` |
| `h3.need_share` | `replay_only` | mechanism | -0.0000 | -0.0000 | [-0.0222, +0.0278] | +1.0000 | `cmp:exp_2664ff5b0ef947c8:h3.need_share:replay_only` |
| `h6.question_share` | `replay_only` | descriptive | +0.0056 | +0.4082 | [+0.0000, +0.0167] | +1.0000 | `cmp:exp_2664ff5b0ef947c8:h6.question_share:replay_only` |
| `h6.repetition_rate` | `replay_only` | function | +0.0000 | not computable | [+0.0000, +0.0000] | +1.0000 | `cmp:exp_2664ff5b0ef947c8:h6.repetition_rate:replay_only` |
| `h1.endogenous_share` | `dream_only` | descriptive | +0.0000 | not computable | [+0.0000, +0.0000] | +1.0000 | `cmp:exp_2664ff5b0ef947c8:h1.endogenous_share:dream_only` |
| `h1.spontaneous_speech_rate` | `dream_only` | descriptive | +0.0000 | not computable | [+0.0000, +0.0000] | +1.0000 | `cmp:exp_2664ff5b0ef947c8:h1.spontaneous_speech_rate:dream_only` |
| `h2.stage_entropy` | `dream_only` | descriptive | +0.0270 | +0.1428 | [-0.1055, +0.1566] | +0.7500 | `cmp:exp_2664ff5b0ef947c8:h2.stage_entropy:dream_only` |
| `h2.dismiss_rate` | `dream_only` | descriptive | +0.0000 | not computable | [+0.0000, +0.0000] | +1.0000 | `cmp:exp_2664ff5b0ef947c8:h2.dismiss_rate:dream_only` |
| `h3.need_share` | `dream_only` | mechanism | -0.0000 | -0.0000 | [-0.0222, +0.0278] | +1.0000 | `cmp:exp_2664ff5b0ef947c8:h3.need_share:dream_only` |
| `h6.question_share` | `dream_only` | descriptive | +0.0056 | +0.4082 | [+0.0000, +0.0167] | +1.0000 | `cmp:exp_2664ff5b0ef947c8:h6.question_share:dream_only` |
| `h6.repetition_rate` | `dream_only` | function | +0.0000 | not computable | [+0.0000, +0.0000] | +1.0000 | `cmp:exp_2664ff5b0ef947c8:h6.repetition_rate:dream_only` |
| `h1.endogenous_share` | `full_sleep` | descriptive | +0.0000 | not computable | [+0.0000, +0.0000] | +1.0000 | `cmp:exp_2664ff5b0ef947c8:h1.endogenous_share:full_sleep` |
| `h1.spontaneous_speech_rate` | `full_sleep` | descriptive | +0.0000 | not computable | [+0.0000, +0.0000] | +1.0000 | `cmp:exp_2664ff5b0ef947c8:h1.spontaneous_speech_rate:full_sleep` |
| `h2.stage_entropy` | `full_sleep` | descriptive | +0.0270 | +0.1428 | [-0.1055, +0.1566] | +0.7500 | `cmp:exp_2664ff5b0ef947c8:h2.stage_entropy:full_sleep` |
| `h2.dismiss_rate` | `full_sleep` | descriptive | +0.0000 | not computable | [+0.0000, +0.0000] | +1.0000 | `cmp:exp_2664ff5b0ef947c8:h2.dismiss_rate:full_sleep` |
| `h3.need_share` | `full_sleep` | mechanism | -0.0000 | -0.0000 | [-0.0222, +0.0278] | +1.0000 | `cmp:exp_2664ff5b0ef947c8:h3.need_share:full_sleep` |
| `h6.question_share` | `full_sleep` | descriptive | +0.0056 | +0.4082 | [+0.0000, +0.0167] | +1.0000 | `cmp:exp_2664ff5b0ef947c8:h6.question_share:full_sleep` |
| `h6.repetition_rate` | `full_sleep` | function | +0.0000 | not computable | [+0.0000, +0.0000] | +1.0000 | `cmp:exp_2664ff5b0ef947c8:h6.repetition_rate:full_sleep` |

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
- `h9.links_per_sleep`: not computable (no sleep in this run)
- `h9.replayed_per_sleep`: not computable (no sleep in this run)

## Qualitative studies

No qualitative case study was recorded for this campaign.

## Anomalies

- 0

## Threats to validity

- Retention here is the strength the memory rules compute; replay strengthens by rule, and waking recall strengthens too. The difference shows the wiring, not a benefit for behaviour.

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

To reproduce: `python -m freewill.research run EXP-04` with the same code version recomputes the same results hash.

`results_sha256 = da2109fe9ec1defcb5090213c6df7b638ec9132d83e59bde25dae870f4763bc0`
