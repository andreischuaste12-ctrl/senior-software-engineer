"""Run with python -m sse_agent --help."""

import argparse
import json
import os
import sys
from urllib import parse

from . import __version__
from .agent import DEFAULT_BASE_URL, MAX_PAYLOAD, AgentError, Client, run
from .arguments import positive, positive_float
from .platforms import split_command
from .sensitive import contains_sensitive_content
from .tools import Workspace
from .trace import JsonlTrace


def parse_checks(shell_style: list[str], json_style: list[str]) -> dict[str, list[str]]:
    """Convert --check NAME=COMMAND and --check-json NAME=ARRAY into {name: argv}."""
    checks: dict[str, list[str]] = {}
    for item, as_json in [(item, False) for item in shell_style] + [
            (item, True) for item in json_style]:
        name, separator, command = item.partition('=')
        try:
            parts = json.loads(command) if as_json else split_command(command)
        except ValueError:
            raise AgentError('--check/--check-json contains an unreadable command (invalid quotes or JSON).') from None
        if (not separator or not name.strip() or name in checks or
                not isinstance(parts, list) or not parts or
                any(not isinstance(part, str) or '\x00' in part for part in parts) or not parts[0]):
            raise AgentError('--check requires NAME=COMMAND with a unique name and a non-empty command.')
        checks[name] = parts
    return checks


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description='Software engineering agent guided by the project skill.')
    parser.add_argument('task', help='Task to execute; enclose it in quotes.')
    parser.add_argument('--version', action='version', version=f'sse_agent {__version__}')
    parser.add_argument('--workspace', default='.', help='Authorized repository (default: current directory).')
    parser.add_argument('--allow-write', action='store_true', help='Allow creating or replacing text files.')
    parser.add_argument('--allow-executable-write', action='store_true',
                        help='Allow writes to automation and executable surfaces. Requires --allow-write.')
    parser.add_argument('--allow-check-after-write', action='store_true',
                        help='Allow checks to execute after model writes. Requires --allow-write and '
                             'trust in the configured checks and edited code.')
    parser.add_argument('--allow-remote', action='store_true',
                        help='Allow sending content to the configured external API.')
    parser.add_argument('--deny', action='append', default=[], metavar='GLOB', help='Deny paths; repeatable.')
    parser.add_argument('--allow-file', action='append', default=[], metavar='GLOB',
                        help='Restrict files to these patterns; repeatable. Denials still take precedence.')
    parser.add_argument('--check', action='append', default=[], metavar='NAME=COMMAND',
                        help='Authorize a shell-free command, for example tests=python -m unittest discover.')
    parser.add_argument('--check-json', action='append', default=[], metavar='NAME=JSON',
                        help='Authorize a JSON argument array, preserving paths that contain spaces.')
    parser.add_argument('--check-env', action='append', default=[], metavar='VARIABLE',
                        help='Pass this environment variable to checks (only a minimal, secret-free '
                             'set is passed by default). Repeatable.')
    parser.add_argument('--trace', metavar='FILE',
                        help='Write a content-free JSONL trace (tool names, sizes, durations, outcomes) to FILE.')
    parser.add_argument('--max-steps', type=positive, default=12)
    parser.add_argument('--timeout', type=positive_float, default=60,
                        help='Timeout for each check, in seconds.')
    parser.add_argument('--api-timeout', type=positive_float, default=120,
                        help='Timeout for each API call, in seconds.')
    parser.add_argument('--api-retries', type=int, choices=range(4), default=0,
                        help='Extra retries for HTTP 429/5xx (default: 0). '
                             'They may cause duplicate processing and charges.')
    parser.add_argument('--max-context-bytes', type=positive, default=MAX_PAYLOAD,
                        help='Maximum API payload size; old tool results are compacted to fit.')
    return parser


def risk_notices(workspace: Workspace, client: Client) -> list[str]:
    """Explain, before any data is sent, what this particular run authorizes."""
    host = parse.urlsplit(client.endpoint).hostname
    if client.local:
        notices = [f'Read files and the task will be sent to the local endpoint {host}. Confirm that '
                   'the server does not forward data or collect telemetry.']
    else:
        notices = [f'EXTERNAL ENDPOINT {host}: the task, instructions, every file the agent reads, and '
                   'check output may be sent to this provider and may incur charges. Filters cannot '
                   'detect every secret.']
        if not workspace.allow_files and not workspace.deny:
            notices.append('No --allow-file or --deny filter is configured; consider limiting file access.')
    if workspace.checks:
        if workspace.allow_write and not workspace.allow_check_after_write:
            notices.append('Checks are disabled in this write session unless --allow-check-after-write is set.')
        else:
            notices.append('Authorized checks execute local code with your permissions; they are not a sandbox.')
    if workspace.allow_check_after_write:
        notices.append('WARNING: checks may execute code written by the model.')
    if workspace.allow_executable_write:
        notices.append('WARNING: the model may change automation files, scripts, and build manifests.')
    return notices


def main(argv: list[str] | None = None) -> int:
    # Normal CLI invocation, including the installed sse-agent entry point.
    if argv is None:
        for stream in (sys.stdout, sys.stderr):
            if hasattr(stream, 'reconfigure'):
                stream.reconfigure(encoding='utf-8', errors='replace')
    args = build_parser().parse_args(argv)
    try:
        if not args.task.strip():
            raise AgentError('Provide a non-empty task.')
        checks = parse_checks(args.check, args.check_json)
        if (args.allow_executable_write or args.allow_check_after_write) and not args.allow_write:
            raise AgentError('The write-risk options require --allow-write.')
        workspace = Workspace(args.workspace, args.allow_write, checks, args.timeout,
                              pass_env=args.check_env, deny=args.deny, allow_files=args.allow_file,
                              allow_executable_write=args.allow_executable_write,
                              allow_check_after_write=args.allow_check_after_write)
        client = Client(os.environ.get('SSE_API_KEY') or os.environ.get('OPENAI_API_KEY'),
                        os.environ.get('SSE_MODEL'),
                        os.environ.get('SSE_BASE_URL', DEFAULT_BASE_URL),
                        args.api_timeout, args.max_context_bytes, retries=args.api_retries,
                        allow_remote=args.allow_remote)
        if contains_sensitive_content(args.task.encode('utf-8')):
            if not client.local:
                raise AgentError('The task text contains credential-like content. Remove it before '
                                 'sending the task to an external API.')
            print('Warning: the task text contains credential-like content.', file=sys.stderr)
        for notice in risk_notices(workspace, client):
            print(notice, file=sys.stderr)
        trace = JsonlTrace(args.trace) if args.trace else None
        try:
            result = run(client, workspace, args.task, args.max_steps,
                         notify=lambda name: print(f'Tool: {name}', file=sys.stderr), trace=trace)
        finally:
            if trace:
                trace.close()
        print(result)
        return 0
    except (AgentError, OSError, ValueError) as exc:
        print(f'Error: {exc}', file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        print('Interrupted; review any local changes.', file=sys.stderr)
        return 130


if __name__ == '__main__':
    raise SystemExit(main())
