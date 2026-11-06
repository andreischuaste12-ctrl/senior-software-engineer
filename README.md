# senior-software-engineer

Created by **[Andrei Schuaste](https://github.com/andreischuaste12-ctrl)**.
This is an open-source project developed with community participation.

The project develops a software engineering agent that can build, analyze,
optimize, and refactor code across programming languages. Effectiveness must be
demonstrated for each task through relevant tests, compilation, static analysis,
performance measurements, or other appropriate evidence.

## Current status

The repository contains a Python CLI agent, a self-contained `SKILL.md` package,
reviewed knowledge references, and eight deterministic evaluation fixtures. The agent
uses a tool-capable AI API and local tools controlled by the operator. Real-model
effectiveness has not yet been measured; scripted integration tests do not prove it.

## Run the agent

Python 3.11 or newer is required on Windows, Linux, or macOS. The default endpoint
is local (`http://127.0.0.1:1234/v1`). Start a compatible Chat Completions server
separately and set `SSE_MODEL` to an available model. The agent does not download
or start models. External APIs require an HTTPS URL, credentials, and the explicit
`--allow-remote` option.

On Windows, open PowerShell in this repository:

```powershell
$env:SSE_MODEL = "LOCAL_MODEL_ID"
py -3 -m sse_agent --workspace "C:\Projects\My Project" "Analyze this project and propose improvements"
```

On Linux or macOS, use `python -m sse_agent` and a local project path. File tools
are read-only by default. See the [CLI guide](docs/cli-agent.md) for writing,
checks, privacy controls, provider selection, and execution limits.

Run local validation without credentials or real-model calls:

```powershell
py -3 -m unittest discover -s tests -v
py -3 -m ruff check .
py -3 -m mypy --strict
py -3 scripts/verify_wheel.py
```

The CI matrix covers Windows, Ubuntu, and macOS. Install the standalone CLI with
`py -3 -m pip install .`. The skill and its references are included in the wheel.
See the [changelog](CHANGELOG.md) and [release process](docs/releases.md).

## Use the skill

The [senior-software-engineer skill](skills/senior-software-engineer/SKILL.md)
guides bug fixes, features, refactoring, architecture analysis, and performance
work. Copy the entire `skills/senior-software-engineer/` directory into a host
that supports `SKILL.md` packages and follow that host's activation mechanism.
Installation paths and invocation rules vary by host.

Review the [evaluation scenarios](skills/senior-software-engineer/evals/scenarios.md)
before making effectiveness claims. The skill does not install compilers,
services, or integrations, train a model, or guarantee universal language support.

## Knowledge base

The [foundational knowledge](docs/foundational-knowledge.md) covers engineering
principles, architecture, testing, security, performance, and evidence-based API
use. The [operating guidelines](docs/operating-guidelines.md) turn those concepts
into a practical workflow. Initial ecosystem coverage includes Python,
JavaScript/TypeScript, Go, Rust, Java, and C#/.NET.

The [supplemental knowledge](docs/supplemental-knowledge.md),
[API currency review](docs/knowledge-base-v2-review.md), and
[URL matrix](skills/senior-software-engineer/references/url-matrix.md) record
additional material supplied by the project owner and the project's reviewed
conclusions. Submitted Portuguese material was converted into English project
editions; source hashes remain recorded for provenance. Version claims and remote
endpoints must still be checked when used.

## Contributions

Everyone is welcome to contribute ideas, bug reports, documentation, evaluation
cases, and code. Read [CONTRIBUTING.md](CONTRIBUTING.md) before opening a pull
request. External references may inform original work, but third-party text and
code must not be copied without a license review.

## License

Copyright 2026 Andrei Schuaste. See [NOTICE](NOTICE).

Original content that its copyright holders can license is available under the
[Apache License 2.0](LICENSE) (`Apache-2.0`). This license does not change the
rights or licenses of cited external material.
