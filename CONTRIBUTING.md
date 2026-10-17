# Contributing

Two kinds of contributions are welcome: new tasks and harness variants.

## Adding a task

Create `tasks/<id>/` with this layout:

```
tasks/bugfix-004-example/
├─ task.yaml
├─ repo/            # the starting code the agent sees
├─ tests/           # hidden grader tests (not visible to the agent)
└─ solution.patch   # reference fix, used to validate the task
```

`task.yaml`:

```yaml
id: bugfix-004-example
category: bugfix        # comprehension | bugfix | feature | refactor | tests | long-context
difficulty: 2
language: python
title: One line summary
prompt: |
  What the agent must achieve. Describe the required behavior, not the fix.
limits:
  max_minutes: 10
  max_files_changed: 3
grade:
  type: pytest          # pytest | node | mutation
  timeout: 120
```

For `mutation` tasks, add `grade.test_file` (where the agent must write tests)
and put a reference test in `reference/`:

```yaml
grade:
  type: mutation
  test_file: tests_written/test_example.py
  timeout: 120
```

Rules:

1. The task must fail without `solution.patch` and pass with it.
2. Tests must be deterministic: no network, no wall-clock assertions, no
   randomness without a fixed seed.
3. Tests must not exist inside `repo/`. Hidden tests are copied in at grade
   time, which is what makes the benchmark resistant to test editing.
4. `solution.patch` must be a `git diff` against `repo/` and must apply cleanly.
5. Keep fixtures small. A task that needs a package install will not run in CI.

Validate before opening a PR:

```sh
dso validate --tasks <id>
```

All tasks must report `ok`.

## Adding a harness variant

Add `harness/vN/AGENTS.md`. Anything placed there is copied into the workspace
root and excluded from the measured diff. Then register it in
`src/dso/models.yaml` under `harnesses`.

Variants must change one variable at a time relative to the previous version.
A variant that changes prompt, context policy, and verification at once tells
you nothing.

## Reporting results

Run at least three repeats and report:

- pass@1 with a confidence interval,
- cost per solved task,
- the harness version and model ID,
- the OpenCode version.

One run is an anecdote, not a result.

## Code style

```sh
ruff check src
```

Keep the runner model-agnostic. No provider-specific branching outside
`models.yaml`.

## File size

No file under `src/dso/` may exceed 300 lines. `tests/test_structure.py` enforces
this in CI. If a module grows past the limit, split it by responsibility rather
than by layer: collection, parsing, execution, reporting. `agent.py` was split
out of `runner.py` for exactly this reason.
