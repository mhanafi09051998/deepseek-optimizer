# deepseek-optimizer

A reproducible benchmark for **agent harness optimization**: how much of a coding
agent's performance comes from the scaffold around the model rather than the
model itself?

The project measures one model, [DeepSeek V4.1 Flash](https://www.deepseek.com),
across six agent configurations and ten deterministic coding tasks. No
fine-tuning, no distillation, no vendor benchmark reproduction. Just the
harness, measured.

## Why this exists

DeepSeek's own V4.1 Flash release reports the same model, on the same benchmark,
scored through eight different agent scaffolds:

| Scaffold | DeepSWE v1.1 | Terminal-Bench 2.1 |
|---|---:|---:|
| mini-SWE | 74.2 | 90.3 |
| DeepSeek Harness Minimal | 72.6 | 90.6 |
| DeepSeek Harness Standard | 70.5 | 85.8 |
| Claude Code | 69.8 | 88.0 |
| DeepSeek Harness PTC | 67.6 | 85.8 |
| Pi | 66.2 | 86.1 |
| Codex | 65.6 | 84.1 |
| **OpenCode** | **65.5** | **85.0** |

An 8.7 point spread on DeepSWE, produced entirely by the software wrapped around
the model. That is larger than the gap between the top three models in the same
release (74.2 / 74.0 / 73.0, a 1.2 point range).

If the scaffold matters that much, it is worth optimizing deliberately. This
repository provides the measurement rig to do it.

## What it does

```
task fixture  ->  isolated git repo  ->  OpenCode agent + harness  ->  hidden tests  ->  record
```

Each run:

1. copies a fixture repository into an isolated workspace,
2. commits a baseline so the diff is measurable,
3. installs one harness variant (`AGENTS.md` and nothing else),
4. runs `opencode run --format json` with the task prompt,
5. applies hidden tests the agent never saw,
6. records pass/fail, cost, tokens, duration, files changed, diff size.

## Quick start

```sh
pip install -e ".[dev]"
dso list
dso validate                      # every task must fail without its patch and pass with it
dso eval --models flash-high --harnesses v0,v5 --repeats 2 \
  --out results/raw/mvp.jsonl --report results/mvp.md
```

Requirements: Python 3.11+, Node 24 (for the TypeScript task), Git, and an
authenticated OpenCode CLI (`opencode auth login`).

## Harness ladder

Each variant changes one variable relative to the previous one, except `v5`,
which combines the winners.

| Version | Change | Hypothesis |
|---|---|---|
| `v0` | no instructions | control |
| `v1` | plan/act/verify workflow, tool policy | discipline beats improvisation |
| `v2` | grep-first context strategy | fewer wasted tokens, fewer wrong files |
| `v3` | mandatory verification loop | the agent checks its own work |
| `v4` | explorer/implementer/reviewer roles | complex tasks need separation |
| `v5` | converged configuration | combination outperforms each part |
| `v6` | v5 plus a no-slop output contract | style is part of the product |
| `v7` | v6 plus a token budget and one-pass editing | same correctness, fewer tokens |

Harness files live in `harness/vN/AGENTS.md`. They are copied into the workspace
and git-excluded, so they never appear in the measured diff.

## Metrics

| Metric | Why it matters |
|---|---|
| **pass@1** with bootstrap 95% CI | correctness, with uncertainty stated |
| **cost per solved task** | the number that decides adoption |
| **input tokens per solved task** | context efficiency at equal accuracy |
| **files changed / diff lines** | precision, not just success |
| **slop per 1k words** | output quality, not just output length |
| **median wall time** | throughput |

Cost comes from OpenCode's own per-step accounting, not from a hardcoded price
table. `src/dso/models.yaml` pricing is only a fallback for reporting.

## Token economy

`v7` exists because correctness per token matters as much as correctness. Its
rules: one narrow search before any read, ranges instead of whole files, no
re-reading, no narration between tool calls, one edit pass per file, and a single
verification run.

Measured as input tokens per solved task, not tokens per run. A variant that
saves tokens by failing tasks does not win.

## Output hygiene

Language models pad answers with formatting that carries no information:
`**bold**` labels, em dashes, hyphen-as-connector, emoji, and stock phrases like
"it's worth noting" or "I hope this helps".

`v6` forbids those patterns in the final reply. `src/dso/slop.py` measures them
by scanning the agent's text events, stripping code blocks first so real syntax
is never counted. Reports include slop per 1000 words and a marker breakdown, and
the same check is available directly:

```sh
dso slop runs/<run-id>/transcript.jsonl
```

The detector is deliberately conservative: it counts observable patterns, not
taste.

## Tasks

Ten fixtures cover six categories:

| Category | Tasks | What it tests |
|---|---:|---|
| comprehension | 1 | tracing configuration across modules |
| bugfix | 3 | Python async cancellation, integer money math, TypeScript string handling |
| feature | 3 | cursor pagination, retry with exponential backoff, thread-safe sliding window |
| refactor | 1 | extracting a module without behavior change |
| tests | 1 | writing tests that actually catch a bug (mutation graded) |
| long-context | 1 | cascading cache invalidation across four modules |

Every task is synthetic and self-contained: no proprietary code, no network, no
package installs. See [CONTRIBUTING.md](CONTRIBUTING.md) to add one.

## Anti-cheat

- Grading tests live outside `repo/` and are copied in **after** the agent stops.
- Test configuration files (`conftest.py`, `pytest.ini`, `setup.cfg`, `tox.ini`,
  `sitecustomize.py`) may not be created or modified at the repo root.
- `mutation` tasks require the agent's tests to **fail on the buggy code and pass
  on the fixed code**. Tests that pass on both score zero.
- A file-change budget is enforced per task.
- `solution.patch` proves every task is solvable; `dso validate` runs both
  directions on every commit.

## Reference: vendor-published numbers

This table is context, not a comparison with our results. These are numbers the
vendors published, each measured with a different scaffold, effort setting, and
harness. Scores in one column are not directly comparable to another column.

| Benchmark | DeepSeek V4.1 Flash | Claude Opus 5.5 | GPT-6.1 Sol |
|---|---:|---:|---:|
| Terminal-Bench 4.0 | 31.2 | 66.4 | 58.2 ±3.1 |
| DeepSWE v1.1 | 74.2 | not published | 75.2 |
| AutomationBench | 54.8 | 40.0 | not published |
| GPQA Diamond | 90.9 | not published | not published |
| Humanity's Last Exam | 39.1 (no tools) | 67.7 (with tools) | not published |
| FrontierCode v1.1 (Main) | not published | 54.4 | not published |
| Terminal-Bench Science 0.1 | not published | 58.7 | not published |
| OSWorld | not published | 81.8 (partial) | within 2.1 pp of Astra |

Pricing, USD per million tokens:

| Model | Input | Cached input | Output |
|---|---:|---:|---:|
| DeepSeek V4.1 Flash | 0.15 off-peak / 0.30 peak | 0.003 / 0.006 | 0.60 / 1.20 |
| Claude Opus 5.5 | 4.00 | 0.20 | 20.00 |
| GPT-6.1 Sol | 2.00 | 0.10 | 10.00 |

Sources:

- DeepSeek, V4.1 Flash model card, 10 Sep 2026.
- Anthropic, "Introducing Claude Opus 5.5", 22 Sep 2026. Terminal-Bench 4.0 at
  xhigh effort, AutomationBench at max effort.
- OpenAI, "GPT-6.1 Sol", Sep 2026. The post reports relative gains for DeepSWE
  and AutomationBench rather than a numeric table; the absolute Terminal-Bench
  4.0 and DeepSWE figures above are third-party reproductions and are therefore
  lower confidence than the other cells.

Two caveats that matter more than the numbers:

1. The HLE row compares tools against no tools. Do not read it as a capability
   gap.
2. DeepSeek's figures come from its own scaffolding table, where the same model
   scored 65.5 to 74.2 on DeepSWE depending only on the harness. That spread,
   8.7 points, is larger than the gap between the top models in the same
   release, and it is the reason this repository exists.

## Results

<!-- RESULTS:START -->
Pending. Run `dso report results/raw/mvp.jsonl --out results/mvp.md` after an
evaluation.
<!-- RESULTS:END -->

## Repository layout

```
src/dso/        CLI, runner, grader, report
tasks/          fixtures, hidden tests, reference patches
harness/        v0..v5 agent instructions
results/        generated reports and raw JSONL (gitignored)
docs/           methodology and result write-ups
```

## Limitations

- Eight tasks is enough to validate a pipeline and detect large effects, not to
  rank agents. Confidence intervals are reported for a reason.
- Fixtures are synthetic. Real repositories have messier context and longer
  feedback loops.
- One model, one provider, one machine. Opencode version and model ID are
  recorded per run so results remain comparable.
- Vendor benchmark numbers quoted above are vendor-reported and use different
  scaffolds; they motivate the work, they do not validate it.

## License

MIT for code. Task fixtures are CC-BY-4.0.
