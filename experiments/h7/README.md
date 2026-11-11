# H7 protocol

Reproducible experiments for H7 (emergent affectivity). No network, no model: the simulated engine, seeded random streams and a simulated clock.

```bash
python experiments/h7/run.py                 # runs everything, rewrites results/ (a few minutes)
python experiments/h7/run.py --report-only   # rebuilds results/report.md from results/metrics.json
```

- `scenarios.json`: the scenarios, fixed in advance. Their texts carry no emotion word.
- `harness.py`: one life under one condition (B0, B1, B2, B3 ablations), with everything that happened recorded.
- `run.py`: the measures. Causality, individuation, stability, consolidation, habituation, safety checks.
- `results/metrics.json`, `results/trajectories.csv`, `results/report.md`: the output. Two runs give identical files.

What the numbers mean, and what they do not, is in [`docs/H7_AFFECTIVITY.md`](../../docs/H7_AFFECTIVITY.md) ([français](../../docs/H7_AFFECTIVITE.fr.md)). Results that do not support the hypothesis are reported there with the others.
