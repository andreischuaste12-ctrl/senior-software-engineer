# Terminal AI agent — 0.4.0

Python 3.11 or newer is required on Windows, Linux, or macOS. The wheel has no
runtime dependencies and includes the skill resources. Both `pip install .` and
`pip install -e .` are supported. The installed command is `sse-agent`.

## Windows

From PowerShell in the repository:

```powershell
py -3 --version
py -3 -m sse_agent --help
py -3 -m unittest discover -s tests -v
py -3 -m pip install .
sse-agent --version
```

If `py` is unavailable, verify the Python Launcher installation or use `python`
after checking its version. WSL, Bash, an activated virtual environment, and
ExecutionPolicy changes are not required. Quote paths that contain spaces.

## Local model by default

Start a compatible Chat Completions server with function calling separately. The
agent neither downloads nor starts a model. Confirm the server's hardware needs,
offline behavior, telemetry, and forwarding policy.

- `SSE_BASE_URL` defaults to `http://127.0.0.1:1234/v1`.
- `SSE_MODEL` is the exact available model ID and is required.
- `SSE_API_KEY` is optional for local servers that require authentication.

```powershell
$env:SSE_MODEL = "LOCAL_MODEL_ID"
py -3 -m sse_agent --workspace "C:\Projects\My Project" --deny "private/**" --allow-file "**/*.py" "Review the authorized code"
```

Loopback calls ignore environment proxies and reject redirects. This constrains the
client; it does not isolate the local server or checks. For strict confidentiality,
use OS-level isolation and a trusted local server. No software can guarantee zero risk.

## External API opt-in

External URLs are rejected before a request unless `--allow-remote` is present.
Set `SSE_BASE_URL` to an HTTPS provider URL, set `SSE_MODEL`, and provide a key
through `SSE_API_KEY` or `OPENAI_API_KEY`. The CLI does not load `.env` files.

With opt-in, the task, instructions, read files, and check results may be sent to
the provider and may incur charges. File filters cannot identify every embedded
secret. Review the provider's terms and the selected data before enabling transfer.

## File access

- `--deny GLOB` excludes matching paths from every file tool.
- `--allow-file GLOB` limits access to matching files. Built-in protection and
  `--deny` still take precedence.
- Both `/` and `\` are accepted. `**` matches zero or more directories.
  Access filters are case-insensitive for consistent Windows and POSIX protection.
- Known credential files, private-key formats, Terraform state/variable files,
  and `.git`, `.aws`, `.ssh`, `.kube`, `.gnupg`, and `.docker` are blocked.
- `.env.example`, `.env.sample`, and `.env.template` are readable; verify that
  templates contain no real secrets.
- `node_modules`, virtual environments, and tool caches are always blocked.
  Root-level `build`, `dist`, `target`, `vendor`, `.next`, and `coverage`
  are omitted from recursive listing. Nested directories with those names remain
  accessible because they may represent source-domain concepts. Direct root paths
  remain accessible unless denied by the operator.
- Symlinks, junctions/reparse points, parent traversal, NTFS streams, and reserved
  Windows device names are rejected.

These rules do not sandbox checks, detect every hardlink race, or scan source text
for all secrets. Avoid concurrent modifications and use a narrow allowlist.

## Tools

| Tool | Contract |
| --- | --- |
| `list_files` | Optional `pattern` and `directory`; up to 1,000 results and 10,000 scanned files. |
| `search_text` | Literal query with optional pattern, directory, case folding, and a 200-result ceiling. |
| `read_file` | UTF-8, up to 64,000 response bytes; line ranges for files up to 2 MB; full-file SHA-256. |
| `replace_in_file` | Requires `--allow-write`, the read hash, and a unique old string unless `replace_all`; preserves CRLF. |
| `write_file` | Requires `--allow-write`; creates under an existing parent or replaces with a valid hash. |
| `run_check` | Runs only an operator-defined argument array; returns exit status, timeout, and bounded output. |

A response may request at most 128 tool calls. The first eight are executed
sequentially; excess calls receive paired errors and can be requested later. Each
round is fully validated before local effects begin.

## Checks and process limits

```powershell
py -3 -m sse_agent --workspace "C:\Projects\My Project" --allow-write --check "tests=py -3 -m unittest discover -s tests -v" "Fix the bug and validate it"
```

`--check` uses native Windows parsing or POSIX `shlex`, without a free shell.
`--check-json NAME=JSON_ARRAY` is available for exact programmatic arguments.
Checks run with their normal OS permissions and can write even without
`--allow-write`. They are not sandboxed. A minimal environment is passed;
`--check-env NAME` opts into another variable, but API keys are never forwarded.

Timeout termination uses a POSIX process group or `taskkill /T /F` on Windows.
Hostile detached processes may escape. Returned output is about 16 KB, while the
temporary log has no disk quota.

The defaults are 12 rounds, 120 seconds per API call, 60 seconds per check, a
250,000-byte request, and a 2,000,000-byte response. API retries are disabled.
`--api-retries N` (0–3) explicitly enables retries for 429/5xx. A retry can
duplicate processing or charges. Connection failures and timeouts are not retried.

## Evaluation and releases

```powershell
py -3 -m sse_agent.evals list
py -3 -m sse_agent.evals run E05 --json
```

The evaluation CLI uses the configured real model and requires `--allow-remote`
for an external API. E01, E03, E05, and E10 use synthetic fixtures and deterministic
graders. Scripted tests validate the graders; they do not measure a real model.

The CI matrix covers Windows, Ubuntu, and macOS on Python 3.11 and 3.14, including
a non-editable installation outside the checkout. Passing tests do not guarantee
security or broad effectiveness. See [releases](releases.md).
