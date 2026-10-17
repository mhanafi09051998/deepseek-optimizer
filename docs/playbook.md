# Diagnosis playbook

A scenario catalog for coding agents. Each row states the first probe, the test
that falsifies the leading hypothesis, and the conclusion that agents reach too
early.

## Problem classes

| Symptom | First probe | Falsifier | Premature conclusion |
|---|---|---|---|
| Wrong output, no crash | Reproduce with the smallest input | The same input through a second code path gives the correct result, so the bug is in the shared layer | "The logic looks right" |
| Crash or traceback | Read the last frame, not the whole log | Adding a print at the frame shows the value is already wrong earlier | "Raised in line X, so X is wrong" |
| Test fails only in CI | Compare interpreter and dependency versions | The test passes locally with the CI version pinned | "Flaky test" |
| Test passes but behavior is wrong | Check what the test asserts | The assertion is weaker than the spec, or the fixture bypasses the path | "Tests pass, so it works" |
| Auth or permission denied | Read the client config for an existing host or user entry | A second credential source authenticates | "Access is impossible" |
| Command not found | Check PATH, version manager shims, and the actual binary | The binary exists but the shell resolves another one | "Not installed" |
| Empty result where data is expected | Check the filter before the query | The source has zero rows for that key | "The database is empty" |
| Works once, fails on repeat | Look for shared mutable state | A fresh process handles the repeat correctly | "Intermittent, cannot reproduce" |
| Slow over time | Measure the growth of the data structure per iteration | Memory is flat but latency still grows, so the cost is elsewhere | "Needs caching" |
| Config value ignored | Trace precedence order end to end | The effective value comes from a higher-precedence layer | "The config is broken" |

## Repair patterns

| Pattern | Use when | Trap |
|---|---|---|
| Narrowing | The failure is reproducible | Fixing the first failing case and assuming the class is covered |
| Differential | Two environments disagree | Changing the environment until both "look" the same |
| Bisect | A behavior regressed between two known states | Bisecting commits when the input data changed instead |
| Instrumentation | The value at the failure point is unknown | Leaving debug output in the final diff |
| Inversion | The expected result is easier to compute than the actual | Rewriting the implementation before confirming the spec |
| Boundary sweep | The bug involves limits, empty input, or repeats | Testing only the happy path and calling it verified |

## Stop conditions

A cause is confirmed when a test distinguishes it from every competing cause and
the fix makes that test pass.

A conclusion is allowed to be negative only after three named alternatives were
tested. Each alternative needs a result, not an opinion.

An environment failure is not a code failure. Fix or report the environment
before editing source.

## Anti-patterns

- Declaring the root cause from reading code alone.
- Patching the symptom because the test went green.
- Skipping a failing test instead of reading it.
- Adding a retry around a deterministic failure.
- Concluding "impossible" after the first rejected attempt.
