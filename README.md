# deepseek-optimizer

Harness optimization for coding agents. Same model, same tasks, different
scaffold. Everything is measured, nothing is vibes.

**Headline result:** +10 pp pass rate, 42% lower cost per solved task, 97% less
AI-slop output, 24% faster. The model never changed.

## Benchmark

Ten deterministic coding tasks, one run each, same machine, same OpenCode
version, `deepseek/deepseek-flash#high` throughout.

| Configuration | pass@1 | Cost / solved | Tokens / solved | Slop /1k | TB 4.0 | DeepSWE | AutomationBench |
|---|---:|---:|---:|---:|---:|---:|---:|
| DeepSeek V4.1 Flash, before (v0) | 90% (9/10) | $0.0036 | 6,460 | 27.7 | 31.2 | 74.2 | 54.8 |
| DeepSeek V4.1 Flash, after (v7) | **100% (10/10)** | **$0.0021** | **5,890** | **0.9** | 31.2 | 74.2 | 54.8 |
| DeepSeek V4.1 Flash, v8 tool budget | 100% | $0.0030 | 8,792 | 0.9 | 31.2 | 74.2 | 54.8 |
| DeepSeek V4.1 Flash, v9 repo map | 100% | $0.0027 | 7,135 | 0.9 | 31.2 | 74.2 | 54.8 |
| DeepSeek V4.1 Flash, v11 truncated tools | 100% | $0.0020 | 5,690 | 0.0 | 31.2 | 74.2 | 54.8 |
| DeepSeek V4.1 Flash, v13 error-safe truncation | 100% | $0.0021 | 6,051 | 0.0 | 31.2 | 74.2 | 54.8 |
| DeepSeek V4.1 Flash, v14 hypothesis ladder | 100% | $0.0029 | 6,062 | 0.0 | 31.2 | 74.2 | 54.8 |
| Claude Opus 5.5 | not run | n/a | n/a | n/a | 66.4 | not published | 40.0 |
| GPT-6.1 Sol | not run | n/a | n/a | n/a | 58.2* | 75.2* | not published |

Columns 2 to 5 are measured here. Columns 6 to 8 are vendor-published and apply
to the model, not the harness, so they stay identical across the DeepSeek rows.
Asterisked cells are third-party reproductions because the vendor published only
relative gains.

### What moved, and what did not

| Metric | v0 | v7 | Delta |
|---|---:|---:|---:|
| pass@1 | 90% | 100% | +10 pp |
| Cost per solved task | $0.0036 | $0.0021 | -42% |
| Input tokens per solved task | 6,460 | 5,890 | -9% |
| Slop markers per 1k words | 27.7 | 0.9 | -97% |
| Median wall time | 22.8 s | 17.4 s | -24% |

v8 and v9 did not beat v7. Capping tool calls and injecting a symbol map kept
pass@1 at 100% but raised token use and cost. v11, which truncates every tool
result at 4000 characters through an OpenCode plugin, is cheaper by 5% and
faster by 6%, but its token reduction is inside run-to-run noise. v13 raises that
cap to 8000 characters and keeps the tail whenever the output looks like an
error, so large repositories do not lose tracebacks; it reaches 0.0 slop and the
fastest median time (14.6 s) at the same cost as v7. The honest reading: on this
task set, the token budget in v7 was already binding. v14 adds a hypothesis ladder and diagnosed problems before editing; it kept 100% and 0.0 slop but cost 17% more than v13, so diagnosis discipline did not pay for itself on tasks this small. All variants stay in the repo as measured results, including the negative ones.

With ten tasks, one task equals ten percentage points. Treat the pass@1 delta as
directional. The cost, token, and style deltas are consistent across all runs.

## How it works

```
fixture -> isolated git repo -> OpenCode agent + AGENTS.md -> hidden tests -> record
```

1. Copy the fixture into a fresh workspace and commit a baseline.
2. Install one harness variant. It is an `AGENTS.md` file and nothing else.
3. Run `opencode run --format json` with the task prompt.
4. After the agent exits, copy in hidden tests it never saw and grade.
5. Record pass, cost, tokens, cache share, diff size, wall time, slop markers.

No fine-tuning, no distillation, no vendor benchmark reproduction.

## Harness ladder

| Version | Change | Outcome |
|---|---|---|
| v0 | no instructions | control |
| v1 | plan, act, verify | discipline |
| v2 | grep-first context | fewer wrong files |
| v3 | mandatory verification | self-checking |
| v4 | explorer, implementer, reviewer | role separation |
| v5 | combined | converged |
| v6 | v5 plus no-slop output contract | style |
| v7 | v6 plus token budget | best measured result |
| v8 | hard tool call caps | no gain |
| v9 | v8 plus generated repo map | no gain |
| v10 | bounded recovery loop | for long tasks |
| v11 | plugin: truncate tool output at 4000 chars | -5% cost, tokens within noise |
| v12 | v7 plus strict no-format output contract | slop near zero |
| v13 | v12 plus error-safe truncation at 8000 chars | slop 0.0, fastest run |
| v14 | hypothesis ladder and access-failure protocol | diagnosis before edits |

## Quick start

```sh
pip install -e ".[dev]"
dso validate
dso eval --models flash-high --harnesses v0,v7 --repeats 3
dso report results/raw/run.jsonl --out results/summary.md
```

Requirements: Python 3.11+, Node 24, Git, and an authenticated OpenCode CLI.

## Safe to import

This repository does not execute anything on install or on import. There are no
postinstall hooks, no setup scripts, and no git hooks.

`dso` is a normal CLI. The harness only applies when you copy
`harness/vN/AGENTS.md` into a project root on purpose. The benchmark is opt-in.

## Layout

```
src/dso/     CLI, runner, grader, report, slop detector
tasks/       13 fixtures with hidden tests and reference patches
harness/     v0 to v10 agent instructions
results/     generated reports, raw JSONL is gitignored
docs/        methodology and full per-task results
```

## Limits

1. Ten tasks detect large effects, not small ones. Intervals are reported.
2. Fixtures are synthetic. Real repositories have messier context.
3. Vendor numbers use different scaffolds. They motivate the work, not prove it.

Full methodology: [docs/methodology.md](docs/methodology.md).
Diagnosis playbook: [docs/playbook.md](docs/playbook.md).
Orchestration guide: [docs/orchestration.md](docs/orchestration.md).
Per-task results: [docs/results-v1.md](docs/results-v1.md).

## License

MIT for code. Task fixtures are CC-BY-4.0.
