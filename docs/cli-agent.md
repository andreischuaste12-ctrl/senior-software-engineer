# Terminal AI agent — 0.7.0

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

Before any request, the CLI prints what the run authorizes: the endpoint host,
whether a file filter is configured, and any write or check risk you enabled. A task
text that contains a recognizable credential is refused for an external endpoint
(for a local endpoint it only warns).

## Privacy and risk checklist

- **Prefer a local model.** Confirm that the local server does not forward data or
  collect telemetry; the CLI cannot verify that.
- **Do not use `--allow-remote` with private code or confidential data** without
  reviewing the provider's retention, training, and transfer terms.
- **Limit what the agent can read.** Use `--allow-file` for an allowlist and `--deny`
  for sensitive directories (for example `--deny "private/**" --deny "secrets/"`).
  A trailing slash such as `secrets/` matches that directory at any depth; `./secrets/`
  matches only the workspace root.
- **Keep secrets out of prompts, files, and check output.** Built-in filters block many
  credential files and token formats, but no filter detects every secret.
- **Do not authorize checks on untrusted code.** Checks run with your permissions and are
  not a sandbox. Write sessions hide checks unless `--allow-check-after-write` is set, and
  `--allow-executable-write` lets the model change automation files and scripts. Enable
  them only for repositories and edits you trust.
- **Use OS-level isolation** (a container or VM without credentials) for untrusted projects.

## File access

- `--deny GLOB` excludes matching paths from every file tool.
- `--allow-file GLOB` limits access to matching files. Built-in protection and
  `--deny` still take precedence.
- Both `/` and `\` are accepted. `**` matches zero or more directories.
  Access filters are case-insensitive for consistent Windows and POSIX protection.
- Known credential files, key and keystore formats, Terraform state/variable files,
  CMS and framework configuration that holds database credentials (for example
  `wp-config*.php`, `app/etc/env.php`, `sites/default/settings.php`), and the
  `.git`, `.aws`, `.ssh`, `.kube`, `.gnupg`, `.docker`, and `.azure` directories are
  blocked. Relative credential paths such as `.config/gh/hosts.yml` match at any depth.
- Recognizable credential content causes the entire file to be refused: private keys
  (with a key body), AWS, GitHub, GitLab, Slack, OpenAI, Anthropic, Stripe, Google,
  npm, SendGrid, Azure storage, Shopify, WooCommerce, and Mercado Pago tokens, JWTs,
  and database URLs with real passwords. Obvious documentation placeholders (such as
  `AKIA...EXAMPLE` or a token made of one repeated character) are not flagged.
  `search_text` counts the files it could not search in `skipped`, and check output is
  redacted. This is defense in depth, not complete secret detection.
- A workspace must be a project directory: filesystem roots, system directories, a home
  directory or any of its parents, and directories inside credential or dependency
  folders (such as `.ssh` or `.git`) are rejected.
- `.env.example`, `.env.sample`, and `.env.template` are readable; verify that
  templates contain no real secrets.
- `node_modules`, `.next`, virtual environments, and tool caches are always blocked.
  Root-level `build`, `dist`, `target`, `vendor`, and `coverage` are omitted from
  recursive listing. Nested directories with those names remain accessible because
  they may represent source-domain concepts. On case-sensitive hosts, the artifact
  names are case-sensitive. Root artifact
  directories cannot be enumerated directly, although an explicitly named file
  remains readable unless denied by the operator.
- Symlinks, hardlinks, junctions/reparse points, FIFOs, device files, parent
  traversal, NTFS streams, and reserved Windows device names are rejected; opening
  is non-blocking, so a FIFO is refused instead of hanging the agent. Windows 8.3
  aliases such as `GIT~1` are rejected on Windows only.

These rules do not sandbox checks or scan source text for all secrets. Avoid
concurrent modifications and use a narrow allowlist.

## Tools

| Tool | Contract |
| --- | --- |
| `list_files` | Optional `pattern` and `directory`; patterns may be workspace-relative or directory-relative; up to 1,000 results and 10,000 scanned files. |
| `search_text` | Literal query with optional workspace-relative or directory-relative pattern, directory, case folding, a 200-result ceiling, a 32 MB scan budget, and a five-second scan budget. The result includes `skipped`, the number of matching files that could not be searched. |
| `read_file` | UTF-8, up to 64,000 response bytes; line ranges for files up to 2 MB; full-file SHA-256. |
| `replace_in_file` | Requires `--allow-write`, the read hash, and a unique old string unless `replace_all`; preserves CRLF and an existing UTF-8 BOM. |
| `write_file` | Requires `--allow-write`; creates under an existing parent or replaces with a valid hash. Automation files, scripts, and any file with an interpreter line require `--allow-executable-write`. |
| `run_check` | Runs only an operator-defined argument array; returns exit status, timeout, and bounded output with credential-like content redacted. Hidden during write sessions unless `--allow-check-after-write` is present. |

A response may request at most 128 tool calls. The first eight are executed
sequentially; excess calls receive paired errors and can be requested later. Each
round is fully validated before local effects begin. Tool results have a per-round
budget of at most 96 KB, reduced when `--max-context-bytes` is small. Excess read
results receive explicit errors and must be requested in smaller ranges. The outcome of
a tool that changed something (`write_file`, `replace_in_file`, `run_check`) is never
replaced by that error: bulky check output is shortened instead.

## Checks and process limits

```powershell
py -3 -m sse_agent --workspace "C:\Projects\My Project" --allow-write --allow-check-after-write --check "tests=py -3 -m unittest discover -s tests -v" "Fix the bug and validate it"
```

`--check` uses native Windows parsing or POSIX `shlex`, without a free shell.
`--check-json NAME=JSON_ARRAY` is available for exact programmatic arguments.
Checks run with their normal OS permissions and can write even without
`--allow-write`. They are not sandboxed. When writes are enabled, checks are hidden
unless `--allow-check-after-write` explicitly authorizes executing code after
model edits. Even ordinary source files can become executable through a configured
test or build command. Automation files and scripts (CI and editor configuration,
build manifests, test hooks, shell scripts, files under `scripts/`, `bin/`, and similar)
and any file that starts with an interpreter line also require `--allow-executable-write`
before the file tools can change them; the rule is applied to the normalized path, so
`.github//workflows/x.yml` is covered. File permissions are not used, because NTFS mounts
report every file as executable. A minimal environment is passed;
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
for an external API. E01, E02, E03, E05, E06, E07, E08, and E10 use synthetic
fixtures and deterministic graders. Scripted tests validate the graders; they do
not measure a real model.

The CI matrix covers Windows, Ubuntu, and macOS on Python 3.11 and 3.14, including
a non-editable installation outside the checkout. Passing tests do not guarantee
security or broad effectiveness. See [releases](releases.md).
