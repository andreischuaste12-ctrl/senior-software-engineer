# Reviewed supplemental knowledge

This is an original project synthesis of material supplied by Andrei Schuaste on
November 5, 2026. Submission labels and version snapshots are not certified facts.

## Stable and volatile knowledge

Design principles are relatively stable heuristics. Releases, support windows,
CVEs, deprecations, and new syntax require target-version evidence. An accepted
proposal does not prove delivery in an installed release, and Java support terms
can differ by distributor.

Distinguish direct observation, a source's claim, and inference. Record URL,
version or revision, access date, and reading scope. HTTP 200 proves access only.
Aggregators aid discovery; critical decisions should use the relevant maintainer or
vendor source.

## Additional patterns

Prototype, Bridge, Composite, Flyweight, and Iterator can solve specific object
copying, independent variation, tree, shared-state, and traversal problems.
Mediator can centralize communication but also responsibility. Memento requires a
clear snapshot boundary. Template Method relies on inheritance, while Strategy
supports composition. Visitor favors new operations on stable structures.
Interpreter fits small grammars; dedicated parsers may be more appropriate.

No pattern is a prerequisite for quality.

## Architecture, reliability, and testing

Ports/adapters and layers can protect domain logic and change boundaries without
requiring a wholesale architecture. Twelve-Factor guidance targets certain service
types and is not a universal rule for CLIs, embedded software, or desktop apps.

Balance unit, integration, contract, and end-to-end tests according to risk. A
pyramid does not prescribe counts. Define SLIs, SLOs, and error budgets when they
support operational decisions. Use OWASP ASVS/Top 10, NIST SSDF, and SLSA only
within their applicable scope; a checklist is not certification.

## Knowledge evolution

A cache may store source, revision or hash, access time, and expiration. TTL depends
on risk and cannot guarantee freshness. Old publication dates do not invalidate
documentation for an old installed version. When execution and docs disagree,
investigate version, configuration, flags, and platform.

Source registries, advisory feeds, scheduled jobs, RAG, and persistent memory are
future proposals. The CLI does not implement them. Knowledge changes must produce
an authorized, reviewable diff without sensitive data.
