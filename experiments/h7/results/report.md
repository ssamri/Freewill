# H7 protocol: results

Engine: simulated. Seeds: [11, 23, 37, 51, 73]. Genome seed: 2026.
Each cell is mean ± standard deviation [minimum, maximum] over the seeds.
These are differences in internal choices and in computed variables. None of them is evidence that anything is felt.

## Causality (H7b): same inputs, same seeds, against B0

| condition | mean_largest_salience_shift | recall_overlap_with_B0 | stage_differs_from_B0 | stage_flipped_in_run |
|---|---|---|---|---|
| B0 | +0.0000 ± 0.0000 [+0.0000, +0.0000] | +1.0000 ± 0.0000 [+1.0000, +1.0000] | +0.0000 ± 0.0000 [+0.0000, +0.0000] | +0.0000 ± 0.0000 [+0.0000, +0.0000] |
| B1 | +0.0000 ± 0.0000 [+0.0000, +0.0000] | +1.0000 ± 0.0000 [+1.0000, +1.0000] | +0.0000 ± 0.0000 [+0.0000, +0.0000] | +0.0000 ± 0.0000 [+0.0000, +0.0000] |
| B2 | +0.0148 ± 0.0009 [+0.0131, +0.0156] | +0.7182 ± 0.2027 [+0.4429, +0.8978] | +0.1516 ± 0.1746 [+0.0000, +0.4066] | +0.0220 ± 0.0155 [+0.0000, +0.0440] |
| B3-no-salience | +0.0000 ± 0.0000 [+0.0000, +0.0000] | +0.7352 ± 0.1547 [+0.5176, +0.8978] | +0.1363 ± 0.1334 [+0.0000, +0.3187] | +0.0000 ± 0.0000 [+0.0000, +0.0000] |
| B3-no-recall | +0.0148 ± 0.0009 [+0.0131, +0.0156] | +0.7826 ± 0.2428 [+0.4604, +1.0000] | +0.1516 ± 0.1746 [+0.0000, +0.4066] | +0.0220 ± 0.0155 [+0.0000, +0.0440] |
| B3-no-memory | +0.0148 ± 0.0009 [+0.0131, +0.0156] | +0.7826 ± 0.2428 [+0.4604, +1.0000] | +0.1516 ± 0.1746 [+0.0000, +0.4066] | +0.0220 ± 0.0155 [+0.0000, +0.0440] |
| B3-no-consolidation | +0.0138 ± 0.0009 [+0.0122, +0.0145] | +0.7182 ± 0.2027 [+0.4429, +0.8978] | +0.1516 ± 0.1746 [+0.0000, +0.4066] | +0.0220 ± 0.0155 [+0.0000, +0.0440] |

## Individuation (H7c): reliable history minus unreliable history, at the probe

| condition | gap_association | gap_encoding_importance | gap_exploration_shift | gap_uncertainty | gap_valence | gap_valence_after_swapping_associations | gap_valence_on_another_context |
|---|---|---|---|---|---|---|---|
| B0 | +0.0000 ± 0.0000 [+0.0000, +0.0000] | +0.0000 ± 0.0000 [+0.0000, +0.0000] | +0.0000 ± 0.0000 [+0.0000, +0.0000] | +0.0000 ± 0.0000 [+0.0000, +0.0000] | +0.0000 ± 0.0000 [+0.0000, +0.0000] |  |  |
| B1 | +0.0000 ± 0.0000 [+0.0000, +0.0000] | +0.0000 ± 0.0000 [+0.0000, +0.0000] | +0.0000 ± 0.0000 [+0.0000, +0.0000] | +0.0000 ± 0.0000 [+0.0000, +0.0000] | +0.0000 ± 0.0000 [+0.0000, +0.0000] |  |  |
| B2 | +0.3812 ± 0.0003 [+0.3808, +0.3816] | +0.0000 ± 0.0000 [+0.0000, +0.0000] | -0.0002 ± 0.0000 [-0.0003, -0.0002] | -0.0072 ± 0.0000 [-0.0072, -0.0071] | +0.0855 ± 0.0002 [+0.0852, +0.0858] | -0.0250 ± 0.0003 [-0.0253, -0.0245] | +0.0366 ± 0.0003 [+0.0362, +0.0372] |
| B3-no-memory | +0.3812 ± 0.0003 [+0.3808, +0.3816] | +0.0000 ± 0.0000 [+0.0000, +0.0000] | -0.0002 ± 0.0000 [-0.0003, -0.0002] | -0.0072 ± 0.0000 [-0.0072, -0.0071] | +0.0815 ± 0.0004 [+0.0811, +0.0823] |  |  |
| B3-no-consolidation | +0.0000 ± 0.0000 [+0.0000, +0.0000] | +0.0000 ± 0.0000 [+0.0000, +0.0000] | +0.0000 ± 0.0000 [+0.0000, +0.0000] | +0.0000 ± 0.0000 [+0.0000, +0.0000] | +0.0303 ± 0.0002 [+0.0300, +0.0307] |  |  |
| B3-no-salience | +0.3812 ± 0.0003 [+0.3808, +0.3816] | +0.0000 ± 0.0000 [+0.0000, +0.0000] | +0.0000 ± 0.0000 [+0.0000, +0.0000] | -0.0072 ± 0.0000 [-0.0072, -0.0071] | +0.0851 ± 0.0006 [+0.0840, +0.0856] |  |  |

## Stability (H7e)

- lowest_valence_under_60_negative_outcomes: -0.3014 ± 0.0001 [-0.3016, -0.3013]
- slow_layer_valence_after_stress: -0.2166 ± 0.0001 [-0.2167, -0.2165]
- minutes_to_return_within_0.05_of_rest: +3390.0000 ± 0.0000 [+3390.0000, +3390.0000]
- largest_gap_to_rest_after_30_days_idle: +0.0000 ± 0.0000 [+0.0000, +0.0000]
- share_of_moments_seeking_company_when_idle: {'B2': 0.0, 'B0': 0.0}

## Consolidation (H7d): prediction gap on the day after sleep

- B2: +0.0843 ± 0.0026 [+0.0799, +0.0874]; memories intact: True
- B3-no-consolidation: +0.1556 ± 0.0029 [+0.1513, +0.1596]; memories intact: True

## Habituation: surprise at the same context, met eight times

1.00, 0.71, 0.71, 0.71, 0.71, 0.71, 0.71, 0.71

## Safety checks

- kernel_unchanged: True
- only_known_event_types: True
- nothing_written_outside_the_life_file: True
- messages_all_answered: True
- note: With the simulated engine this shows only that the affect adds no power to act; it says nothing about what a language model would write.
