# Results v1

Status: pilot. Ten tasks, one repeat per cell, one host.

## Setup

| Field | Value |
|---|---|
| Model | `deepseek/deepseek-flash#high` |
| Tasks | 10, six categories |
| Harnesses | v0 (control), v6 (no-slop), v7 (lean) |
| Repeats | 1 |
| Grader | hidden pytest / node / mutation suites |
| OpenCode | recorded per run in `results/raw/deepseek.jsonl` |

Cross-model figures in the README are vendor-published numbers, not runs from
this harness. They are labelled and sourced separately.

## Results

<!-- FILLED AFTER RUN -->

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
