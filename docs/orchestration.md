# Orchestration

How to split work across several agents without producing conflicting edits or
unverified claims.

## When to parallelize

Parallelize when two workstreams touch different files and each takes more than a
few minutes. Typical split:

| Stream | Owns | Does not touch |
|---|---|---|
| Benchmark | `results/raw/`, `runs_*/` | source, README, docs |
| Verification | a temp clone | the working tree |
| Documentation | `docs/`, README | source, tasks |
| Implementation | `src/`, `harness/`, `tasks/` | results, docs |

If two streams need the same file, they are not independent. Run them in
sequence, or give ownership of that file to one stream and make the other report
instead of edit.

## Contract for every subagent

Each task brief must state:

1. The exact working directory.
2. The exact command to run, including environment variables.
3. The output artifact path, so results are checkable later.
4. What not to touch: no git commands, no source edits, no other agents' files.
5. The report format and a word limit.

A brief without an artifact path is not verifiable. A brief without a do-not-touch
clause will eventually collide with another stream.

## Division rules

- One writer per shared file. The orchestrator is the only agent allowed to edit
  README and models.yaml while other streams run.
- Results flow one way: agents write artifacts, the orchestrator reads them and
  updates prose.
- Never let two agents write to the same output file. Append conflicts produce
  silent data loss.
- Keep a stable naming scheme: `results/raw/<experiment>.jsonl` and
  `runs_<experiment>/`.
- Assign one question per agent. "Do the benchmark and update the docs" produces
  two half-finished jobs.

## Merge protocol

1. Collect each artifact path and the command that produced it.
2. Recompute the summary yourself from the artifact. Do not trust a number that
   appears only in a chat message.
3. Reconcile contradictions before writing prose. If two runs disagree, report
   both and say which one is reproducible.
4. Update shared files once, after all artifacts are in.
5. Run the local checks, then push a single commit per logical change.

## Failure handling

If a stream fails, do not silently retry with the same brief. Inspect the
artifact: a missing file means the command failed early, a partial file means it
was killed. Restart that stream alone, with the corrected command.

A stream that reports "done" without an artifact is treated as failed.

## Example brief

```
Working directory: <repo>
Run: <exact command with env vars>
Artifact: results/raw/<name>.jsonl
Do not: edit source, run git, touch other results files
Report: pass count, cost per solved task, failures, under 150 words
```

The orchestrator owns the narrative. Subagents own the measurements.
