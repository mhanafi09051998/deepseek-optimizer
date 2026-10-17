# dso results

Runs: 20

## Model x harness

| Model | Harness | Runs | pass@1 | 95% CI | Cost total | Cost / solved | Tok / solved | Median s | Input tok | Files | Slop /1k | Tools | Cache |
|---|---|---:|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| flash-high | v8 | 10 | 100.0% | 100%-100% | $0.0300 | $0.003003 | 8792 | 22.1 | 8792 | 1.2 | 0.86 | 0.0 | 89% |
| flash-high | v9 | 10 | 100.0% | 100%-100% | $0.0272 | $0.002717 | 7135 | 19.1 | 7135 | 1.2 | 0.90 | 0.0 | 91% |

## pass@1 by category

| Harness | bugfix | comprehension | feature | long-context | refactor | tests |
|---|---:|---:|---:|---:|---:|---:|
| v8 | 100% | 100% | 100% | 100% | 100% | 100% |
| v9 | 100% | 100% | 100% | 100% | 100% | 100% |

## Style markers

Total occurrences per harness. Code blocks are excluded.

| Harness | Markers |
|---|---|
| v8 | spaced_hyphen=1 |
| v9 | spaced_hyphen=1 |
