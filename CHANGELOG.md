# Changelog

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
