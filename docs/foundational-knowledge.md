# Foundational software engineering knowledge

## Purpose and status

This reference supports an agent that analyzes, implements, refactors, and debugs
software in multiple languages. It is an English project edition of foundational
material supplied by the project owner on November 5, 2026. It is independent of
the unreviewed external skill listed in CONTRIBUTING.md.

The recommendations are contextual heuristics. The CLI does not include RAG, a
dedicated sandbox, MCP integration, or automatic memory updates. Real-model
effectiveness remains unmeasured.

## Design and code quality

| Principle | Practical use | Warning signs |
| --- | --- | --- |
| Clarity | Use domain names, cohesive responsibilities, and readable control flow. | Hidden intent, deep nesting, surprising side effects. |
| DRY | Centralize rules that share a reason to change. | One business change requires coordinated edits in many locations. |
| KISS and YAGNI | Implement the simplest solution that preserves required contracts. | Speculative extensibility and abstractions without consumers. |

Function size, parameter count, indentation, and cyclomatic complexity are signals,
not universal limits. Follow project configuration and justify exceptions with
evidence. Comments should explain decisions and contracts rather than restate code.

SOLID principles are decision aids, not a demand for classes or interfaces.
Prefer explicit dependencies and composition when they reduce coupling. Preserve
public behavior unless a breaking change is authorized.

Patterns such as Strategy, Adapter, Decorator, Factory, Observer, Command, State,
and Repository are useful only when they solve a concrete problem. Describe the
problem, the simpler alternative, and the trade-off before adding one.

## Architecture and task scope

Map actual boundaries, dependencies, data flow, and change points. Keep domain
logic independent from infrastructure where that separation reduces change cost.
Do not impose a full architecture on a small task.

For a review, report located findings with impact and reproduction conditions.
For a bug, reproduce and fix the cause. For a feature, define behavior and failure
modes. For refactoring, state the behavior that must remain unchanged. For
performance, measure a representative baseline and compare under the same conditions.

## API and version discipline

Determine the declared, resolved, and installed runtime and dependency versions.
Inspect manifests, lockfiles, wrappers, scripts, and CI before choosing commands.
Use official documentation for the target version and local types or source when
available. Do not confuse a project's main branch with a released dependency.

Separate facts into observed evidence, source claims, and inference. Record the URL,
revision or version, access date, and the exact conclusion used. A successful HTTP
request proves access only. Without sufficient evidence, state uncertainty instead
of inventing an API or upgrading dependencies to avoid the question.

## Security, performance, and resources

Identify trust boundaries, authentication, authorization, and data validation.
Consider injection, XSS, SSRF, deserialization, traversal, and access control when
relevant. Parameterize query values and validate dynamic identifiers.

Avoid exposing credentials or personal data. Preserve TLS and integrity checks.
Use password-specific hashing for stored passwords. Run processes with separated
arguments and avoid a shell when possible.

Set deadlines, cancellation, payload bounds, and resource limits appropriate to the
operation. Retry only transient failures on safe or idempotent work within a budget.
Measure before complex optimization. Investigate N+1 queries, unbounded work,
blocking, and excessive allocation. Release resources on success, failure, and
cancellation while preserving error causes.

## Evidence and evolution

Define acceptance criteria before consequential changes. Select tests, builds,
type checks, static analysis, and functional probes that can detect the relevant
failure. Compilation and lint alone do not prove functional correctness, security,
or performance. Confirm that intended tests actually ran and distinguish passes,
failures, skips, and checks not run.

Evolve this knowledge through reviewable changes that include the problem,
proposal, compatibility impact, sources, and evidence. Do not claim universal
language support or production readiness without context-specific validation.
