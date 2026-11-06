# API currency and migrations

This review covers version and migration guidance supplied by Andrei Schuaste on
November 5, 2026. It does not promote submission snapshots to verified current facts.

## Target version before new syntax

Identify runtime/compiler, resolved dependencies, language edition, targets, and
flags separately. A Go `go` directive expresses a language/module requirement and
interacts with `toolchain`; it is not a universal exact runtime pin. In Rust,
`edition`, `rust-version`, and the installed toolchain have distinct meanings.
On Windows, also verify launcher, architecture, SDK, and terminal syntax.

## Diagnostics and deprecations

Investigate a warning's source and distinguish removed APIs from supported but
deprecated ones. Follow project policy. Do not migrate an entire dependency graph
for an unrelated warning or suppress diagnostics merely to pass.

Python may hide `DeprecationWarning` by default outside `__main__`. Missing
symbols can also result from incorrect imports, targets, flags, or environments.

## Dependency identity

Before installing a package, verify registry identity, compatible version, license,
source, and available security evidence. Popularity and absence of advisories are
not proof of safety. Without sufficient access, report what remains unverified.
Never expose private package names or credentials in public queries.

## Reviewable migrations

Use compatible official migrators only when an upgrade is authorized. Review their
scope and diff. `cargo fix --edition` is part of a process involving targets,
features, manifests, and tests. Do not override dirty-worktree safeguards.

`ruff check --fix` applies enabled rules and distinguishes safe and unsafe fixes;
it is not a general runtime or framework migrator. Waiting periods, bots, and
scheduled CI changes require explicit project decisions and do not guarantee safety.

## Evidence limits

For every volatile claim, record source, target version, access date, and whether it
was observed, inferred, or unverified. Vendor, extended, free-update, and commercial
support phases are not interchangeable. A missing continuous-update study mentioned
by the submission produced no attributable findings.

Limited primary sources consulted on November 5, 2026: the Go Modules Reference,
Cargo manifest and cargo-fix documentation, Python warnings documentation, Ruff
maintainer documentation, and Oracle's Java support roadmap. Pages can change after
the recorded review.
