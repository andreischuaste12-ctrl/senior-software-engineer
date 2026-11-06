# Changelog

## 0.5.0 - 2026-11-06

- Normalized access globs so trailing slashes, repeated separators, and anchored
  `./` patterns behave predictably; invalid separator-only patterns are rejected.
- Compacted oversized values from the current tool round, used UTF-8 JSON sizing,
  and rejected context budgets too small for the base prompt.
- Defined ranged reads for empty files and enforced the write limit after CRLF conversion.
- Strengthened E01, E03, E05, and E10 graders and converted evaluator timeouts into failures.
- Added deterministic fixtures and positive/negative grader tests for E02, E06,
  E07, and E08, plus machine-readable evaluation coverage metadata.
- Reduced the CLI system prompt to the skill body, removed YAML frontmatter, and
  clarified that package references are outside the user workspace.
- Allowed directory-scoped patterns relative to either the workspace or selected
  directory, while preventing direct enumeration of root artifact directories.
- Enabled strict mypy configuration for the agent and scripts, forced LF checkout
  normalization, and made standalone wheel checks explicitly use UTF-8 on Windows.

## 0.4.0 - 2026-11-06

- Converted maintained code, CLI output, skill instructions, tests, and
  documentation to English; renamed Portuguese documentation paths.
- Made root-level `vendor`, `coverage`, and `.next` directories behave like other
  root artifacts while allowing legitimate nested source directories with those names.
- Adopted current SPDX project-license metadata and a `license-files` declaration;
  the build backend now requires `setuptools>=77`.
- Avoided reconfiguring global output streams when a CLI `main()` function is
  called programmatically with an explicit argument list.
- Report progress only for tools that actually execute, excluding calls skipped by
  the per-round execution limit.
- Added regression coverage for the artifact-directory policy and English-only
  maintained project content.

## 0.3.0 - 2026-11-05

- Made a local endpoint the default and required `--allow-remote` for external APIs.
- Added `--deny` and `--allow-file`, plus more sensitive-configuration blocks.
- Added directory-scoped search/listing, correct globstar behavior, and root-only
  handling for common build directory names.
- Paired excess tool calls with errors while limiting execution to eight per round.
- Normalized equivalent E05 paths and packaged skill resources in the wheel.
- Added strict typing, a standalone wheel smoke test, release documentation, and
  current GitHub Actions versions.

Compatibility change: external providers must set `SSE_BASE_URL`, `SSE_MODEL`,
and a key, then opt in with `--allow-remote`.

## 0.2.0 - 2026-11-05

- Added text search, ranged reads, focused edits, and CRLF preservation.
- Added an evaluation harness, context compaction, and editable installation.
- Bounded UTF-8 replacement expansion before allocation and made retries opt-in.
