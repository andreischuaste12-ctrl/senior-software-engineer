# Second submitted software engineering knowledge base — English project edition

## Provenance

Andrei Schuaste supplied the second Portuguese Markdown document on November 5,
2026. Original submitted SHA-256:

`e09731d10251938f07f8de32ef2c6150c4a825eb23024d95add07e57653d26c1`

This edition records the substance in English. Point-in-time source responses are
stored in `docs/verifications/knowledge-base-v2-2026-11-05.json`. The project does
not certify every claim or snapshot value from the submission.

## Target-version protocol

Before using new syntax or APIs, identify independently:

1. Runtime or compiler version.
2. Language edition or source level.
3. Resolved dependency versions.
4. Target platforms and architectures.
5. Feature flags, profiles, and build configuration.
6. CI versions and supported minimums.

A manifest range is not necessarily a lock. The installed toolchain may differ from
a declared minimum. Go's `go` and `toolchain` directives have distinct roles.
Rust's edition, `rust-version`, and installed toolchain are also distinct.

## Deprecation and diagnostics

Read the complete diagnostic and identify whether it comes from project code, a
dependency, generated code, configuration, or the toolchain. A deprecated API may
remain supported; a removed API does not. Follow the project's warning policy and
avoid broad dependency migration for an unrelated third-party warning.

Python's `DeprecationWarning` may be hidden by default outside `__main__`.
Silence is not evidence that no deprecations exist.

## Dependency verification

Before adding a dependency, verify its registry identity, exact name, maintained
source, compatible version, license, and available security information. Popularity,
download counts, recency, and absence of known advisories do not prove legitimacy
or safety. Do not send internal package names or credentials to public services.

## Migration

Official migration tools can reduce mechanical work but do not prove correctness.
Review their scope and diff, then build and test the affected targets. Do not use
dirty-worktree overrides to overwrite user changes.

`cargo fix --edition` is one part of an edition migration. Targets, features,
manifest changes, and tests remain relevant. `ruff check --fix` applies enabled
lint fixes and distinguishes safe from unsafe fixes; it is not a general runtime
or framework migrator.

## Volatile claims

For versions, support windows, advisories, and benchmarks, record source, target
version, access date, evidence type, and the specific conclusion. Vendor support,
extended support, free updates, and commercial end-of-life are different concepts.
Aggregators can help discovery, but critical decisions should use the relevant
maintainer or vendor source.

The submission referenced a continuous-code-update study that was not included.
No conclusions or metrics are attributed to that missing document.

## Sources represented in the submission

The source catalog included books and primary documentation for clean code,
refactoring, SOLID, patterns, language releases, language specifications, package
registries, OWASP, NIST, SLSA, OSV, and vendor support policies. The project review
consulted only the subset listed in `docs/knowledge-base-v2-review.md`.
