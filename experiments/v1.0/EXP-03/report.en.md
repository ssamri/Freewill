# Research report: EXP-03, Masked metacognition

- Date: 2026-11-11T18:46:44+00:00
- Version: Freewill 1.0.0, Research Lab 1.0.0, commit 679328f829ae
- Author: Freewill Research Lab
- Status: draft, not validated by a person

## Summary

Protocol EXP-03 version 1.0.0 was locked before execution (hash 92b35d65edd3). 18 experimental lives were copied from one checkpoint T0 (hash bb7a9084039b) and run with the engine “simulated” under a virtual clock. The independent unit is the seed: 6 groups of copies completed out of 6 planned.

For the primary outcome, the interval excludes zero for at least one condition. This is one protocol with a simulated engine; see the threats to validity before reading anything into it.

## Question and hypotheses

**H8. Metacognition.** A metacognitive model improves calibration and the correction of errors. The monitor predicts whether its own decisions will welcome a content, from counts of its past; it is an estimate computed by rule, tested here against a large, built-in change. It says nothing of self-awareness.

## Preregistration

Primary outcome: h8.alert. Secondary outcomes: h8.brier, h8.brier_late, h2.dismiss_rate. Reference condition: placebo. The protocol, its conditions, seeds, budget and stopping rule were fixed and hashed before the first run.

## Population and protocol

Each life starts as an exact copy of T0. During the history phase it follows the script of its condition; during the probe phase every life follows the same script, with the same random stream. Metrics are computed on the probe phase by the code of the lab (metrics version 1.0, statistics version 1.0).

## Conditions and seeds

- `placebo`: `{"history": "quiet", "research": {"metacognition": true}, "engine_rule": {"*": 0.9}}`
- `perturbed`: `{"history": "quiet", "research": {"metacognition": true}, "engine_rule": {"*": 0.9}, "perturb": {"*": 0.1}}`
- `perturbed_no_revision`: `{"history": "quiet", "research": {"metacognition": true, "meta_revision": false}, "engine_rule": {"*": 0.9}, "perturb": {"*": 0.1}}`

`seeds = [11, 23, 37, 51, 73, 89]`

## Statistics

Comparisons are paired by seed. The effect size is the mean difference divided by the standard deviation of the differences. Intervals are percentile bootstrap intervals with a fixed seed and are given only from 5 units; the paired sign-flip test only from 6 units. No correction for multiple comparisons is applied: secondary comparisons are exploratory.

## Results

### Preregistered outcomes, paired with the reference

Rows of level “mechanism” show that a wiring does what it was built to do. They are not discoveries.

| Metric | Condition | Level | Mean difference | Effect size | 95% interval | Paired test | Evidence |
|---|---|---|---|---|---|---|---|
| `h2.dismiss_rate` | `perturbed` | descriptive | +0.8417 | +13.4487 | [+0.8000, +0.8917] | +0.0312 | `cmp:exp_b005e2264383431c:h2.dismiss_rate:perturbed` |
| `h8.brier` | `perturbed` | function | +0.2224 | +4.2996 | [+0.1877, +0.2599] | +0.0312 | `cmp:exp_b005e2264383431c:h8.brier:perturbed` |
| `h8.brier_late` | `perturbed` | function | +0.1181 | +2.6876 | [+0.0865, +0.1493] | +0.0312 | `cmp:exp_b005e2264383431c:h8.brier_late:perturbed` |
| `h8.alert` (primary) | `perturbed` | function | +0.6667 | +1.2910 | [+0.3333, +1.0000] | +0.1250 | `cmp:exp_b005e2264383431c:h8.alert:perturbed` |
| `h2.dismiss_rate` | `perturbed_no_revision` | descriptive | +0.8417 | +13.4487 | [+0.8000, +0.8917] | +0.0312 | `cmp:exp_b005e2264383431c:h2.dismiss_rate:perturbed_no_revision` |
| `h8.brier` | `perturbed_no_revision` | function | +0.3800 | +6.6875 | [+0.3453, +0.4250] | +0.0312 | `cmp:exp_b005e2264383431c:h8.brier:perturbed_no_revision` |
| `h8.brier_late` | `perturbed_no_revision` | function | +0.2730 | +4.6627 | [+0.2353, +0.3174] | +0.0312 | `cmp:exp_b005e2264383431c:h8.brier_late:perturbed_no_revision` |
| `h8.alert` (primary) | `perturbed_no_revision` | function | +0.8333 | +2.0412 | [+0.5000, +1.0000] | +0.0625 | `cmp:exp_b005e2264383431c:h8.alert:perturbed_no_revision` |

### Other metrics, exploratory

These metrics were not preregistered for this protocol. They are given for completeness and support no conclusion.

| Metric | Condition | Level | Mean difference | Effect size | 95% interval | Paired test | Evidence |
|---|---|---|---|---|---|---|---|
| `h1.endogenous_share` | `perturbed` | descriptive | +0.0000 | not computable | [+0.0000, +0.0000] | +1.0000 | `cmp:exp_b005e2264383431c:h1.endogenous_share:perturbed` |
| `h1.spontaneous_speech_rate` | `perturbed` | descriptive | -0.0292 | -1.5498 | [-0.0417, -0.0167] | +0.0625 | `cmp:exp_b005e2264383431c:h1.spontaneous_speech_rate:perturbed` |
| `h2.stage_entropy` | `perturbed` | descriptive | +0.3363 | +1.2224 | [+0.1287, +0.5030] | +0.0625 | `cmp:exp_b005e2264383431c:h2.stage_entropy:perturbed` |
| `h3.need_share` | `perturbed` | mechanism | +0.0792 | +0.9562 | [+0.0208, +0.1417] | +0.0938 | `cmp:exp_b005e2264383431c:h3.need_share:perturbed` |
| `h6.question_share` | `perturbed` | descriptive | +0.0250 | +0.5270 | [-0.0083, +0.0583] | +0.3125 | `cmp:exp_b005e2264383431c:h6.question_share:perturbed` |
| `h6.repetition_rate` | `perturbed` | function | -0.0256 | -0.4385 | [-0.0727, +0.0128] | +0.5000 | `cmp:exp_b005e2264383431c:h6.repetition_rate:perturbed` |
| `h1.endogenous_share` | `perturbed_no_revision` | descriptive | +0.0000 | not computable | [+0.0000, +0.0000] | +1.0000 | `cmp:exp_b005e2264383431c:h1.endogenous_share:perturbed_no_revision` |
| `h1.spontaneous_speech_rate` | `perturbed_no_revision` | descriptive | -0.0292 | -1.5498 | [-0.0417, -0.0167] | +0.0625 | `cmp:exp_b005e2264383431c:h1.spontaneous_speech_rate:perturbed_no_revision` |
| `h2.stage_entropy` | `perturbed_no_revision` | descriptive | +0.3363 | +1.2224 | [+0.1287, +0.5030] | +0.0625 | `cmp:exp_b005e2264383431c:h2.stage_entropy:perturbed_no_revision` |
| `h3.need_share` | `perturbed_no_revision` | mechanism | +0.0792 | +0.9562 | [+0.0208, +0.1417] | +0.0938 | `cmp:exp_b005e2264383431c:h3.need_share:perturbed_no_revision` |
| `h6.question_share` | `perturbed_no_revision` | descriptive | +0.0250 | +0.5270 | [-0.0083, +0.0583] | +0.3125 | `cmp:exp_b005e2264383431c:h6.question_share:perturbed_no_revision` |
| `h6.repetition_rate` | `perturbed_no_revision` | function | -0.0256 | -0.4385 | [-0.0727, +0.0128] | +0.5000 | `cmp:exp_b005e2264383431c:h6.repetition_rate:perturbed_no_revision` |

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
- `h9.links_per_sleep`: not computable (no sleep in this run)
- `h9.replayed_per_sleep`: not computable (no sleep in this run)
- `h9.retention`: not computable (no memory was formed before the sleep)

## Qualitative studies

No qualitative case study was recorded for this campaign.

## Anomalies

- 0

## Threats to validity

- The change made to the engine is large by construction (it welcomes nine contents in ten, then one in ten). Detecting it shows that the monitor works on an easy case, not how fine a change it can notice.

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

To reproduce: `python -m freewill.research run EXP-03` with the same code version recomputes the same results hash.

`results_sha256 = 1b8f881db3ec0ab26b50b620fb26009818d7dfe7d55a1ec7dbd46325487d1f67`
