# dso results

Runs: 20

## Model x harness

| Model | Harness | Runs | pass@1 | 95% CI | Cost total | Cost / solved | Tok / solved | Median s | Input tok | Files | Slop /1k |
|---|---|---:|---:|---|---:|---:|---:|---:|---:|---:|---:|
| flash-high | v0 | 10 | 90.0% | 70%-100% | $0.0327 | $0.003629 | 6460 | 22.8 | 5814 | 1.2 | 27.74 |
| flash-high | v7 | 10 | 100.0% | 100%-100% | $0.0206 | $0.002063 | 5890 | 17.4 | 5890 | 1.2 | 0.90 |

## Delta vs v0

| Model | Harness | pass@1 delta | Cost / solved delta |
|---|---|---:|---:|
| flash-high | v7 | +10.0% | $-0.001566 |

## pass@1 by category

| Harness | bugfix | comprehension | feature | long-context | refactor | tests |
|---|---:|---:|---:|---:|---:|---:|
| v0 | 100% | 100% | 67% | 100% | 100% | 100% |
| v7 | 100% | 100% | 100% | 100% | 100% | 100% |

## Style markers

Total occurrences per harness. Code blocks are excluded.

| Harness | Markers |
|---|---|
| v0 | bold=16, em_dash=13, heading=2 |
| v7 | em_dash=1 |

## Failing runs

| Task | Model | Harness | Detail |
|---|---|---|---|
| feature-001-pagination | flash-high | v0 | agent timed out after 60s |
