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

## Original work

Write original instructions and implementations. Do not copy files, prose, or code
from other projects, and never present third-party material as original work.

Submit only material you have the right to contribute. Unless explicitly stated
otherwise, intentional contributions submitted for inclusion are licensed under
Apache-2.0 as described in section 5 of that license.

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
