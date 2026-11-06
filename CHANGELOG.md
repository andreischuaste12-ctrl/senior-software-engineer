# Changelog

## 0.7.0 - 2026-11-06

- Fixed a regression where `read_file`, `write_file`, and `replace_in_file` blocked
  forever on a FIFO: files are now opened non-blocking and refused unless regular.
- Normalized the path before classifying execution surfaces (closing a `.github//workflows`
  bypass), widened the list of automation files and scripts, and required the opt-in for
  files that start with an interpreter line. File mode is deliberately not used because
  NTFS mounts report every file as executable.
- Broadened credential defenses: more provider and framework signatures (including
  OpenAI, Anthropic, Stripe, Google, JWT, database URLs, Shopify, WooCommerce, and Mercado
  Pago), documentation placeholders ignored, check output redacted, and `search_text`
  reports files it skipped instead of a false "no match". Protected relative paths and
  name patterns now match at any depth.
- Rejected system directories, home directories and their parents, and workspaces inside
  credential or dependency folders. The 8.3 alias rule applies on Windows only.
- Tool results that changed something are never replaced by the per-round limit message;
  the budget now follows `--max-context-bytes`, so a small limit no longer fails after a
  paid call.
- Tolerated missing call ids and non-text content parts. Distinct file errors no longer
  expose host paths.
- Added risk notices naming the endpoint and the enabled write and check risks, refused
  credential-like task text for external endpoints, and documented a privacy checklist.
- Hardened the E05 canary (now in a readable file) and E06 (rejects denials of the failure).

## 0.6.0 - 2026-11-06

- Separated write authorization from the higher-risk authorization to change
  automation files or execute checks after model edits.
- Expanded credential filename and content defenses; rejected hardlinks, FIFOs,
  devices, filesystem roots, and home-directory roots.
- Added bounded searches, UTF-8 BOM preservation, generic OS errors, recursion-safe
  protocol handling, common multipart content, and explicit per-round result limits.
- Corrected evaluator call accounting, path normalization, decimal-contract
  coverage, evaluation schema metadata, and knowledge-base provenance hashes.
- Added a security policy, code of conduct, issue forms, pull-request template,
  CODEOWNERS, and an original review of the external architecture reference.

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
