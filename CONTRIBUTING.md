# Contributing guidelines

Participation is governed by the [Code of Conduct](CODE_OF_CONDUCT.md). Security
reports follow [SECURITY.md](SECURITY.md) and must not be disclosed in public
issues before a fix is available.

## How to participate

Contributors of every experience level are welcome. Contributions may include
ideas, bug reports, documentation, validation proposals, agent code, and skill
evaluation scenarios.

Open an issue to describe a problem or discuss a proposal. For a change, fork the
repository, work on a branch, and open a pull request against `main`. Explain the
goal and the evidence used to validate it. Keep each pull request focused.

## Original work and external references

Study concepts and methods from external references, then write original
instructions and implementations. Do not run `npx skills add`, import dependencies
from a reference merely to copy its behavior, or copy its files, prose, or code.

Never present third-party material as original work. Before reusing or adapting any
passage, review its license, permission to reuse it, attribution duties, and notice
requirements. This project's Apache-2.0 license does not replace an external
source's license.

Submit only material you have the right to contribute. Unless explicitly stated
otherwise, intentional contributions submitted for inclusion are licensed under
Apache-2.0 as described in section 5 of that license.

## Study record

For every external reference, record:

- Source URL and the revision or access date.
- Status and the exact scope that was read.
- License and notices that were actually verified.
- An original summary of the concepts studied.
- The project problem those concepts may address.
- Evidence needed to evaluate an original implementation.

Separate observations about a source from hypotheses for this project. A proposal
does not demonstrate effectiveness until it is implemented and validated.

## Architecture reference

- Source: <https://github.com/mattpocock/skills>, skill
  `improve-codebase-architecture`.
- Status on November 6, 2026: documentation, skill instructions, and license
  reviewed at commit `4ae2317ddb22b046e26455e4f9c9b3aaaf62212d` without installing them.
- License observed: MIT, copyright Matt Pocock (2026). No source material was
  incorporated into this project.
- Original synthesis and proposed applications:
  [architecture reference review](docs/reference-reviews/improve-codebase-architecture.md).
- Proposed validation: define representative cases and acceptance criteria before
  implementing any original approach. No real-model validation has occurred.

## Review and validation

Check content provenance, scope, documentation links, and license integrity. For
executable changes, run:

```text
python -m unittest discover -s tests
python -m ruff check .
python -m mypy --strict
python scripts/verify_wheel.py
```

Report passes, failures, skips, and checks that were not run. Behavioral fixes
should include a regression test that fails without the fix. Documentation-only
changes require a careful diff and link review rather than artificial app tests.
