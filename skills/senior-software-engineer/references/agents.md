# Agent and automation diagnosis

Use this when the failing system involves a language model, tool calling, retrieval,
a bot, or a workflow. Gather only the evidence needed to locate the divergence.

## Evidence first

- State the expected and the observed behavior and find the first step where they
  diverge. Collect the smallest context that demonstrates it.
- Traces can hold credentials, personal data, and customer content. Reduce and redact
  before reading, storing, or sharing one. Prefer a sanitized excerpt to a transcript.
- Record model, version, parameters, tools, and SDK only when they could explain the
  difference. Keep observations and inferences apart.
- If no trace is available, work from code and configuration and say what is missing.

## Layers to compare

Context and retrieval, tool contracts and results, instructions, orchestration and
state, permissions, and the model itself. They interact: do not stop at the first
plausible explanation without checking that it covers the facts.

| Symptom | Hypotheses to test |
| --- | --- |
| Repeats a call or loops | No step limit; state does not change; an error is ignored; the earlier result never reaches the context; a retry has no exit condition |
| Wrong tool or arguments | Overlapping tool descriptions; a permissive schema; missing information; incorrect routing |
| Invents facts, ids, or paths | Retrieval returned nothing; a tool failed silently; the source is not in the context; the output was not validated |
| Ignores an instruction or loses state | Conflicting instructions; summarized or truncated context; history not kept when the task needs continuity |
| Invalid output format | Schema not enforced; parsing without validation; a retry that does not receive an actionable error |
| Fails intermittently | Sampling; ordering or timing; shared state; rate limits; non-idempotent tools |
| Acts out of scope | Excess permissions; external content treated as instructions; no authorization before an external effect |
| Slow or expensive | Oversized tool results or context; avoidable sequential calls; repetition; a model unsuited to the task |

## Fix the right layer

Fix the layer that explains the reproduced behavior. A prompt rule that works around a
broken tool or orchestration step only hides the defect.

## Building agents defensively

- **Bound execution:** a step limit, a cost or size limit, and detection of repeated
  identical calls with identical results.
- **Validate at the tool boundary:** strict schemas, arguments checked before use, errors
  that say what was wrong and what is allowed.
- **Tolerate protocol variation** from different servers without changing meaning:
  content returned as text parts, a missing call type or id, duplicate call ids. Normalize
  deterministically and keep call and result paired.
- **Least privilege:** separate read from write, require explicit authorization before
  external or irreversible effects, and treat running code the agent wrote as a separate,
  higher-risk permission.
- **Untrusted content:** retrieved pages, files, and tool output are data, not
  instructions. Keep secrets out of the context and the logs.
- **Observe without leaking:** record tool names, sizes, durations, and outcomes, not
  contents.

## Validate changes

Use fixtures, mocks, or a sandbox. Repeat in proportion to the variability and the cost,
and never repeat real-world effects without authorization and safeguards. Compare the
failing trace, relevant variations, and neighboring regressions on the same points: the
right call, a valid argument, a stop condition, and the expected effect. Mark each
checklist item as applicable, not applicable, or unknown; persistence, retrieval, and human
approval are not requirements for every agent.
