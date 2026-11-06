# Debugging reference

Use the techniques that separate plausible causes from implausible ones. Do not run
all of them on every failure; pick the cheapest that can change your mind.

## Anchor the investigation

- Write the expected and the observed behavior as one sentence each. Then find the
  first point where program state stops matching the expectation. That is often
  earlier than where the program finally failed.
- In a stack trace, find the first frame that belongs to the project and ask where
  the bad value was created. Follow chained causes back to the earliest one.
- Treat recent changes (commits, lockfiles, configuration, data, deployed versions)
  as leads, not verdicts. Compare them when the timeline suggests a regression.

## Shrink the problem

- Remove inputs, options, and dependencies until the smallest case that still fails
  remains. Replace the network, clock, randomness, and database with fixed fixtures
  when the failure survives the replacement.
- Bisect over time (commits or releases) or over input (halving the data) when the
  search space is large and the failure is deterministic. A VCS bisect moves the
  checkout: do it only when the working tree is safe to move.

## Choose experiments that can disprove

- For each hypothesis, name an observation that would refute it, and run the cheapest
  one first. Do not collect evidence that every hypothesis would explain.
- Keep two or three rival hypotheses until an observation separates them. A fix that
  explains only part of the facts points to a second cause.

## Symptom to first experiment

| Symptom | First experiment |
| --- | --- |
| Passes locally, fails in CI | Diff the environments: OS, runtime version, locale and timezone, permissions, environment variables, parallelism, network, data. Reproduce in an equivalent container. |
| Fails only sometimes | Follow the intermittent-failure protocol below. |
| Wrong value after several steps | Inspect state at each boundary and bisect the pipeline by stage. |
| Slow, not wrong | Measure one representative run before reading code; a guess about the hot spot is not evidence. |
| Worked before | List what changed in code, dependencies, configuration, data, and time-dependent state. |
| Still fails after the fix | Suspect a second cause or a stale artifact such as a cache, build output, or migration. |

## Intermittent failures

- Look for races, test ordering, shared state, clock and timezone, randomness, rate
  limits, resource limits, and cache state.
- Make the run controllable: fix the seed and the clock, run the test alone and inside
  the suite, then vary ordering or add load.
- Repeat only in a safe sandbox with idempotent actions. Choose the number of runs
  from the failure rate, the variance, and the cost, and record the tally (for
  example "failed 3 of 40"). One green run does not show an intermittent bug is gone.
  Never estimate a rate in production.

## After the fix

- Confirm that the original reproduction now passes and that the cause is gone, not
  hidden by luck, a cache, or a changed environment.
- Search for siblings of the same pattern before closing.
- Change an existing test only when it asserts behavior that is itself wrong, and say
  why in the report.
- Remove temporary instrumentation. Never log secrets, tokens, or personal data.

## Evidence hygiene

Logs, traces, and dumps often hold credentials and personal data. Reduce them to the
smallest slice that shows the problem and redact sensitive values before analyzing or
sharing them. In the CLI agent, read logs with `read_log`, which redacts
credential-like content.
