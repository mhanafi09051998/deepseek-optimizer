# Methodology

## Question

Given a fixed model, how much does the agent harness change task success, cost,
and precision on coding tasks?

## Design

A within-subject comparison: every task is solved by the same model under every
harness variant. Task difficulty is held constant by construction; the only
manipulated variable is `AGENTS.md`.

| Factor | Held constant |
|---|---|
| Model | one ID per experiment, e.g. `deepseek/deepseek-flash#high` |
| Tasks | the same fixture set for every variant |
| Machine | same host, same OpenCode version, same provider |
| Isolation | a fresh git repo per run, private OpenCode server (`--standalone`) |
| Budget | per-task time limit and file-change limit |

Repeats are independent: the workspace is recreated from the fixture each time
and no session is continued.

## Measurement

Collected per run:

- `passed`: hidden tests exit zero, within the file-change budget, with test
  configuration untouched,
- `cost_usd`: sum of the per-step costs reported by OpenCode,
- `tokens`: input, output, reasoning, cache read/write,
- `duration_s`: wall time from spawn to exit,
- `files_changed`, `diff_lines`: from `git status` and `git diff --numstat`,
- `response_words`, `slop_per_1k_words`, `slop_markers`: from the agent's text
  events, with code blocks removed before scanning,
- `grade_detail`: the grader's explanation for failures.

Aggregations:

- **pass@1** = passed runs / total runs.
- **95% CI** = percentile bootstrap over runs, 2000 resamples, fixed seed.
- **cost per solved task** = total cost / solved runs. This is the decision
  metric: a cheap model that solves half as much can still lose.
- **input tokens per solved task** = total input tokens / solved runs. This is
  the token-economy metric, so a variant cannot win by doing less work.
- **slop per 1k words** = detected style markers / response words * 1000. Code
  blocks and inline code are stripped first, so syntax is never counted.
- **median duration** rather than mean, to limit the effect of outliers.

## Grading

Hidden tests are copied into the workspace only after the agent process exits.
The agent never sees the assertions, so it cannot optimize against them.

Three grading modes:

- `pytest`: run the hidden pytest suite.
- `node`: run the hidden `node:test` suite.
- `mutation`: the agent writes tests; those tests must fail on the buggy code and
  pass on the reference-patched code. This grades the *test*, not the
  implementation.

A run fails when any of these hold: the agent times out, produces no completion,
exceeds the file budget, modifies protected test configuration, or the tests
fail.

## Solvability gate

`dso validate` runs every task twice:

1. unpatched fixture, tests must **fail**;
2. fixture with `solution.patch`, tests must **pass**.

A task that passes without the patch is broken (it measures nothing). A task that
fails with the patch is also broken (it is unsolvable). Both block CI.

## Style measurement

The slop detector counts observable patterns only: markdown emphasis, em and en
dashes, a spaced hyphen used as a clause connector, emoji, decorative headings,
and a fixed list of stock phrases. It does not judge whether prose is good, and
it does not count anything inside code fences or inline code.

This keeps the metric reproducible and cheap. It also means the score can be
gamed by writing unusually long prose, which is why it is reported alongside
response word count rather than as a standalone quality measure.

## Threats to validity

- **Sample size.** Ten tasks and a single repeat per cell cannot resolve small
  effects. The design detects large ones and reports intervals rather than point
  claims.
- **Task bias.** Fixtures favor code with clean module boundaries and
  deterministic tests. Real code is less cooperative.
- **Scaffold interaction.** Harness effects may not transfer across models. The
  runner is model-agnostic; a claim about one model is not a claim about all.
- **Cost accounting.** Provider-reported cost depends on cache behavior and
  pricing that can change. Absolute dollar values age; relative comparisons
  within one run do not.
- **Single-shot prompting.** Each task is attempted once per repeat with no
  human intervention or follow-up turns.
