# Results v1

Status: pilot. Ten tasks, one repeat per cell, one host.

## Setup

| Field | Value |
|---|---|
| Model | `deepseek/deepseek-flash#high` |
| Tasks | 10, six categories |
| Harnesses | v0 (control), v7 (lean) |
| Repeats | 1 |
| Timeout | 0.1x default (48 s for most tasks, 90 s for long-context) |
| Grader | hidden pytest / node / mutation suites |
| OpenCode | recorded per run in `results/raw/deepseek.jsonl` |

Cross-model figures in the README are vendor-published numbers, not runs from
this harness. They are labelled and sourced separately.

## Results

| Configuration | pass@1 | Cost per solved | Tokens per solved | Slop /1k | Median time |
|---|---:|---:|---:|---:|---:|
| v0 baseline | 90% (9/10) | $0.0036 | 6,460 | 27.7 | 22.8 s |
| v7 lean | 100% (10/10) | $0.0021 | 5,890 | 0.9 | 17.4 s |

Per task:

| Task | Category | v0 | v7 |
|---|---|---|---|
| bugfix-001-cancel-token | bugfix | pass | pass |
| bugfix-002-money-remainder | bugfix | pass | pass |
| bugfix-003-slugify-ts | bugfix | pass | pass |
| comprehension-001-timeout-default | comprehension | pass | pass |
| feature-001-pagination | feature | fail | pass |
| feature-002-retry-backoff | feature | pass | pass |
| feature-003-sliding-window-limiter | feature | pass | pass |
| long-context-001-dependency-cache | long-context | pass | pass |
| refactor-001-split-parser | refactor | pass | pass |
| tests-001-merge-ranges | tests | pass | pass |

## Observations

1. The task set has a ceiling effect. Eight of ten tasks pass without any harness
   instructions, so the measurable headroom is small. Harder fixtures are the
   next requirement, not more harness variants.
2. The one failure is a feature task where the function did not exist yet and the
   agent had to add a cursor format. v7 solved it; v0 did not.
3. Cost per solved task fell 42% while pass rate rose. That is the intended
   direction: the lean harness spends fewer tokens and also fails less.
4. Slop markers fell from 27.7 to 0.9 per 1k words. The v0 agent used bold labels
   and hyphen connectors habitually; the v7 contract removed them.
5. Wall time fell 24%, mostly from fewer exploratory tool calls.

## Next measurement

The next run should add harder fixtures and three repeats, then compare v7
against v8 (tool budget) and v9 (repo map). Those variants were added after this
run and are not part of these numbers.

## Reading the numbers

- pass@1 over ten tasks moves in steps of 10 percentage points. Treat a one-task
  difference as noise.
- cost per solved task is the decision metric. A model that costs 20 times more
  per token must solve far more tasks to justify itself.
- tokens per solved task guards against a harness that "saves" tokens by giving
  up.
- slop per 1k words is a style measure, reported next to response length so a
  short answer cannot win by being short alone.

## What this does not show

- No claim about tasks outside this fixture set.
- No claim about repeated sessions or human-in-the-loop use.
- No claim that the winning harness is optimal. It is the best of seven attempts
  on this task set.
