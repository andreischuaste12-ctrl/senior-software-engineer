# Security Policy

## Supported versions

Security fixes are applied to the latest commit on `main`. The project does not
currently maintain older release branches.

| Version | Supported |
| --- | --- |
| Latest `main` | Yes |
| Older commits or forks | No |

## Report a vulnerability

Use GitHub's private
[vulnerability report](https://github.com/andreischuaste12-ctrl/senior-software-engineer-konvert/security/advisories/new).
Include the affected version or commit, prerequisites, reproduction steps,
impact, and a suggested fix when available.

Do not include credentials, personal data, production data, or an active exploit
in a public issue. If private vulnerability reporting is unavailable, open a
minimal public issue asking the maintainer to provide a private contact channel;
do not disclose the vulnerability details there.

The maintainer will acknowledge a usable report, assess its scope, prepare and
validate a correction, and coordinate disclosure. Timelines depend on severity
and project capacity. Good-faith research that avoids privacy violations, data
destruction, persistence, service disruption, and access beyond what was
authorized is welcome.

## Privacy and risk checklist

- External providers receive data only after `--allow-remote`, and then they may receive
  the task, instructions, files the agent reads, and check output.
- Prefer a local model, and confirm that the local server does not forward data or collect
  telemetry.
- Restrict access with `--allow-file` and `--deny`; keep secrets out of prompts, files, and
  check output. File filters and content signatures are defense in depth, not complete
  secret detection.
- Checks are OS processes with your permissions, not a sandbox. Do not authorize checks or
  automation-file writes on untrusted code.

## Security boundary

The CLI is a local development tool, not a sandbox. Its file filters reduce
accidental exposure but cannot identify every secret. External providers receive
authorized task and file content only after `--allow-remote`. Checks execute with
the current user's OS permissions. During a write-enabled session, checks remain
disabled unless the operator also supplies `--allow-check-after-write`.
