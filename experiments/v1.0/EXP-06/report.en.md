# Research report: EXP-06, Neural adaptation

- Date: 2026-11-11T18:47:23+00:00
- Version: Freewill 1.0.0, Research Lab 1.0.0, commit 679328f829ae
- Author: Freewill Research Lab
- Status: draft, not validated by a person

## Summary

Protocol EXP-06 version 1.0.0 was locked before execution (hash 86d4debc2580). 18 experimental lives were copied from one checkpoint T0 (hash bb7a9084039b) and run with the engine “simulated” under a virtual clock. The independent unit is the seed: 6 groups of copies completed out of 6 planned.

For the primary outcome, the interval includes zero for every condition. This negative result is reported as it is.

## Question and hypotheses

**H4. Parametric and structural plasticity.** What is lived transforms parameters or structures, not only a memory store. A small trainable module and Freewill's own small network are trained during sleep and can grow, each change measured on what it never saw. The weights of the engine that thinks for the being are not changed by its life.

## Preregistration

Primary outcome: h2.dismiss_rate. Secondary outcomes: h4.validation_gain, h4.forgetting, h4.parameters, h4.parameter_delta, h4.trainings_accepted. Reference condition: memory_only. The protocol, its conditions, seeds, budget and stopping rule were fixed and hashed before the first run.

## Population and protocol

Each life starts as an exact copy of T0. During the history phase it follows the script of its condition; during the probe phase every life follows the same script, with the same random stream. Metrics are computed on the probe phase by the code of the lab (metrics version 1.0, statistics version 1.0).

## Conditions and seeds

- `memory_only`: `{"history": "two_days", "engine_rule": {"question": 0.95, "need": 0.9, "association": 0.5, "reminiscence": 0.15, "drift": 0.1, "*": 0.6}}`
- `adapter`: `{"history": "two_days", "research": {"learner": true}, "engine_rule": {"question": 0.95, "need": 0.9, "association": 0.5, "reminiscence": 0.15, "drift": 0.1, "*": 0.6}}`
- `adapter_growth`: `{"history": "two_days", "research": {"learner": true, "learner_growth": true}, "engine_rule": {"question": 0.95, "need": 0.9, "association": 0.5, "reminiscence": 0.15, "drift": 0.1, "*": 0.6}}`

`seeds = [11, 23, 37, 51, 73, 89]`

## Statistics

Comparisons are paired by seed. The effect size is the mean difference divided by the standard deviation of the differences. Intervals are percentile bootstrap intervals with a fixed seed and are given only from 5 units; the paired sign-flip test only from 6 units. No correction for multiple comparisons is applied: secondary comparisons are exploratory.

## Results

### Preregistered outcomes, paired with the reference

Rows of level “mechanism” show that a wiring does what it was built to do. They are not discoveries.

| Metric | Condition | Level | Mean difference | Effect size | 95% interval | Paired test | Evidence |
|---|---|---|---|---|---|---|---|
| `h2.dismiss_rate` (primary) | `adapter` | descriptive | -0.0250 | -0.5976 | [-0.0583, +0.0000] | +0.5000 | `cmp:exp_610bc2faae7c4021:h2.dismiss_rate:adapter` |
| `h2.dismiss_rate` (primary) | `adapter_growth` | descriptive | -0.0250 | -0.5976 | [-0.0583, +0.0000] | +0.5000 | `cmp:exp_610bc2faae7c4021:h2.dismiss_rate:adapter_growth` |

### Other metrics, exploratory

These metrics were not preregistered for this protocol. They are given for completeness and support no conclusion.

| Metric | Condition | Level | Mean difference | Effect size | 95% interval | Paired test | Evidence |
|---|---|---|---|---|---|---|---|
| `h1.endogenous_share` | `adapter` | descriptive | +0.0000 | not computable | [+0.0000, +0.0000] | +1.0000 | `cmp:exp_610bc2faae7c4021:h1.endogenous_share:adapter` |
| `h1.spontaneous_speech_rate` | `adapter` | descriptive | +0.0125 | +0.5976 | [+0.0000, +0.0292] | +0.5000 | `cmp:exp_610bc2faae7c4021:h1.spontaneous_speech_rate:adapter` |
| `h2.stage_entropy` | `adapter` | descriptive | +0.0111 | +0.0637 | [-0.1068, +0.1532] | +1.0000 | `cmp:exp_610bc2faae7c4021:h2.stage_entropy:adapter` |
| `h3.need_share` | `adapter` | mechanism | +0.0042 | +0.0816 | [-0.0250, +0.0458] | +1.0000 | `cmp:exp_610bc2faae7c4021:h3.need_share:adapter` |
| `h6.question_share` | `adapter` | descriptive | +0.0333 | +0.7614 | [+0.0042, +0.0667] | +0.2500 | `cmp:exp_610bc2faae7c4021:h6.question_share:adapter` |
| `h6.repetition_rate` | `adapter` | function | +0.0085 | +0.3227 | [-0.0085, +0.0299] | +0.7500 | `cmp:exp_610bc2faae7c4021:h6.repetition_rate:adapter` |
| `h9.links_per_sleep` | `adapter` | descriptive | +0.0000 | not computable | [+0.0000, +0.0000] | +1.0000 | `cmp:exp_610bc2faae7c4021:h9.links_per_sleep:adapter` |
| `h9.replayed_per_sleep` | `adapter` | descriptive | +0.0000 | not computable | [+0.0000, +0.0000] | +1.0000 | `cmp:exp_610bc2faae7c4021:h9.replayed_per_sleep:adapter` |
| `h1.endogenous_share` | `adapter_growth` | descriptive | +0.0000 | not computable | [+0.0000, +0.0000] | +1.0000 | `cmp:exp_610bc2faae7c4021:h1.endogenous_share:adapter_growth` |
| `h1.spontaneous_speech_rate` | `adapter_growth` | descriptive | +0.0125 | +0.5976 | [+0.0000, +0.0292] | +0.5000 | `cmp:exp_610bc2faae7c4021:h1.spontaneous_speech_rate:adapter_growth` |
| `h2.stage_entropy` | `adapter_growth` | descriptive | +0.0111 | +0.0637 | [-0.1068, +0.1532] | +1.0000 | `cmp:exp_610bc2faae7c4021:h2.stage_entropy:adapter_growth` |
| `h3.need_share` | `adapter_growth` | mechanism | +0.0042 | +0.0816 | [-0.0250, +0.0458] | +1.0000 | `cmp:exp_610bc2faae7c4021:h3.need_share:adapter_growth` |
| `h6.question_share` | `adapter_growth` | descriptive | +0.0333 | +0.7614 | [+0.0042, +0.0667] | +0.2500 | `cmp:exp_610bc2faae7c4021:h6.question_share:adapter_growth` |
| `h6.repetition_rate` | `adapter_growth` | function | +0.0085 | +0.3227 | [-0.0085, +0.0299] | +0.7500 | `cmp:exp_610bc2faae7c4021:h6.repetition_rate:adapter_growth` |
| `h9.links_per_sleep` | `adapter_growth` | descriptive | +0.0000 | not computable | [+0.0000, +0.0000] | +1.0000 | `cmp:exp_610bc2faae7c4021:h9.links_per_sleep:adapter_growth` |
| `h9.replayed_per_sleep` | `adapter_growth` | descriptive | +0.0000 | not computable | [+0.0000, +0.0000] | +1.0000 | `cmp:exp_610bc2faae7c4021:h9.replayed_per_sleep:adapter_growth` |

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
- `h9.retention`: not computable (no memory was formed before the sleep)

## Qualitative studies

No qualitative case study was recorded for this campaign.

## Anomalies

- 0

## Threats to validity

- What the module has to learn is a fixed rule given to the simulated engine. It is learnable by construction; nothing says a real engine has such a regularity.

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

To reproduce: `python -m freewill.research run EXP-06` with the same code version recomputes the same results hash.

`results_sha256 = 58b71ef82dddcfb5171d79c836e75e86c6cd5b455700944a38680378357f131f`
