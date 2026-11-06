"""Tests for the read-only inventory, log reading, references, loop guard, and trace.

Credential samples are assembled at run time so this file never holds a contiguous
signature and stays readable by the agent itself.
"""

import contextlib
import io
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

from sse_agent import tools as tools_module
from sse_agent.__main__ import main
from sse_agent.agent import AgentError, instructions, run
from sse_agent.references import REFERENCE_NAMES, reference_text, skill_package
from sse_agent.tools import Workspace, log_like
from sse_agent.trace import JsonlTrace

TOKEN36 = 'aB3dE5gH7jK9mN1pQ3sT5vW7yZ9bD2fH4jL6'
SECRET = ''.join(['gh', 'p_', TOKEN36])
KEY_BODY = 'MIIEvgIBADANBgkqhkiG9w0BAQEFAASCBKgwggSkAgEAAoIBAQC7VJTUt9Us'


class Case(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name)

    def write(self, name, data='x'):
        target = self.root / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data if isinstance(data, bytes) else data.encode('utf-8'))
        return target


class ReferenceTests(Case):
    def test_every_listed_reference_exists_and_is_readable(self):
        for name in REFERENCE_NAMES:
            with self.subTest(name=name):
                self.assertTrue((skill_package() / 'references' / f'{name}.md').is_file())
                self.assertGreater(len(reference_text(name)), 200)

    def test_only_allowlisted_names_are_accepted(self):
        for bad in ('../SKILL', 'SKILL', 'ecosystems.md', 'ecosystems/../audit', '/etc/passwd', '', None, 3,
                    'Debugging'):
            with self.subTest(name=bad), self.assertRaisesRegex(ValueError, 'Unknown reference'):
                reference_text(bad)

    def test_tool_returns_the_reference_and_rejects_unknown_names(self):
        workspace = Workspace(self.root)
        result = workspace.execute('read_reference', {'name': 'debugging'})
        self.assertEqual(result['name'], 'debugging')
        self.assertIn('Intermittent failures', result['content'])
        self.assertIn('Unknown reference', workspace.execute('read_reference', {'name': 'x'})['error'])
        enum = [t for t in workspace.definitions() if t['function']['name'] == 'read_reference'][0][
            'function']['parameters']['properties']['name']['enum']
        self.assertEqual(enum, list(REFERENCE_NAMES))

    def test_prompt_points_to_the_new_tools_and_the_skill_links_resolve(self):
        prompt = instructions(Workspace(self.root))
        for phrase in ('project_overview', 'read_log', 'read_reference', 'identical tool call'):
            self.assertIn(phrase, prompt)
        skill = (skill_package() / 'SKILL.md').read_text(encoding='utf-8')
        for name in ('debugging', 'audit', 'agents', 'ecosystems'):
            self.assertIn(f'references/{name}.md', skill)


class LogLikeTests(unittest.TestCase):
    def test_classification(self):
        for name in ('debug.log', 'wp-content/debug.log', 'error_log', 'access.log.1', 'npm-debug.log',
                     'logs/app.txt', 'var/log/syslog', 'run.out', 'trace.jsonl', 'Logs/x.dat'):
            with self.subTest(name=name):
                self.assertTrue(log_like(name))
        for name in ('src/catalog.py', 'README.md', 'dialog.php', 'src/app.py', 'blog/post.md', 'login.php'):
            with self.subTest(name=name):
                self.assertFalse(log_like(name))


class ReadLogTests(Case):
    def read(self, workspace=None, **arguments):
        return (workspace or Workspace(self.root)).execute('read_log', arguments)

    def test_default_is_the_tail_and_ranges_use_the_returned_view(self):
        self.write('logs/app.log', ''.join(f'line {number}\n' for number in range(1, 501)))
        tail = self.read(path='logs/app.log')
        self.assertEqual(tail['end_line'], 500)
        self.assertEqual(tail['start_line'], 301)
        self.assertTrue(tail['content'].endswith('line 500\n'))
        self.assertNotIn('sha256', tail)
        ranged = self.read(path='logs/app.log', start_line=2, end_line=4)
        self.assertEqual(ranged['content'], 'line 2\nline 3\nline 4\n')
        self.assertEqual(self.read(path='logs/app.log', tail_lines=2)['content'], 'line 499\nline 500\n')

    def test_credentials_are_redacted_and_the_file_is_still_useful(self):
        self.write('app.log', f'start\ntoken={SECRET}\nERROR E_TIMEOUT order=7\n')
        self.assertEqual(Workspace(self.root).execute('read_file', {'path': 'app.log'})['error'],
                         'File content resembles a credential and cannot be read or edited.')
        result = self.read(path='app.log')
        self.assertTrue(result['redacted'])
        self.assertIn('E_TIMEOUT', result['content'])
        self.assertNotIn(TOKEN36, result['content'])

    def test_a_multi_line_key_cannot_be_split_by_the_tail_window(self):
        header = ''.join(['-----BEGIN ', 'RSA PRIVATE KEY-----'])
        footer = ''.join(['-----END ', 'RSA PRIVATE KEY-----'])
        body = ''.join(f'{KEY_BODY}\n' for _ in range(6))
        self.write('debug.log', ''.join(f'noise {n}\n' for n in range(40)) + f'{header}\n{body}{footer}\ndone\n')
        result = self.read(path='debug.log', tail_lines=5)
        self.assertNotIn(KEY_BODY, result['content'])
        self.assertTrue(result['redacted'])

    def test_non_log_files_binary_files_and_protected_names_are_refused(self):
        self.write('src/app.py', 'print(1)\n')
        self.write('bin.log', b'\x00\x01\x02')
        self.write('.env', 'x')
        self.write('private/error.log', 'secret\n')
        workspace = Workspace(self.root, deny=['private/**'])
        self.assertIn('log-like', self.read(workspace, path='src/app.py')['error'])
        self.assertIn('binary', self.read(workspace, path='bin.log')['error'])
        self.assertIn('error', self.read(workspace, path='.env'))
        self.assertIn('denied', self.read(workspace, path='private/error.log')['error'])
        self.assertIn('allowlist', self.read(Workspace(self.root, allow_files=['src/**']),
                                             path='bin.log')['error'])

    def test_a_log_larger_than_the_read_limit_returns_its_end(self):
        size_line = 'x' * 99 + '\n'
        self.write('big.log', size_line * 30_000 + 'LAST LINE\n')  # about 3 MB
        result = self.read(path='big.log', tail_lines=2)
        self.assertTrue(result['content'].endswith('LAST LINE\n'))
        self.assertGreater(result['earlier_bytes_omitted'], 0)

    def test_invalid_arguments_are_rejected(self):
        self.write('a.log', 'one\n')
        for arguments in ({'tail_lines': 0}, {'tail_lines': True}, {'start_line': 3, 'end_line': 2}):
            with self.subTest(arguments=arguments):
                self.assertIn('error', self.read(path='a.log', **arguments))


class ProjectOverviewTests(Case):
    def overview(self, **options):
        return Workspace(self.root, **options).execute('project_overview', {})

    def commands(self, result):
        return {item['command']: item for item in result['candidate_commands']}

    def test_python_project_with_pytest_and_ruff(self):
        self.write('pyproject.toml', '[tool.pytest.ini_options]\naddopts = "-q"\n[tool.ruff]\n')
        self.write('uv.lock')
        self.write('.python-version', '3.12\n')
        self.write('src/app.py')
        self.write('.github/workflows/ci.yml')
        result = self.overview()
        self.assertIn('python', result['ecosystems'])
        self.assertIn('uv.lock', result['lockfiles'])
        self.assertIn('.python-version', result['runtime_pins'])
        self.assertIn('.github/workflows/ci.yml', result['ci'])
        self.assertEqual(result['languages'], {'python': 1})
        commands = self.commands(result)
        self.assertEqual(set(commands), {'python -m pytest', 'python -m ruff check .'})
        self.assertTrue(all(c['status'] == 'candidate' for c in commands.values()))
        self.assertFalse(result['partial'])

    def test_unittest_is_proposed_when_tests_exist_even_if_linters_are_configured(self):
        self.write('pyproject.toml', '[tool.ruff]\n[tool.mypy]\n')
        self.write('tests/test_app.py')
        commands = self.commands(self.overview())
        self.assertIn('python -m unittest discover', commands)
        self.assertIn('low confidence', commands['python -m unittest discover']['basis'])
        self.assertIn('python -m ruff check .', commands)
        self.write('pytest.ini')
        self.assertNotIn('python -m unittest discover', self.commands(self.overview()))

    def test_node_commands_follow_declared_scripts_and_the_lockfile(self):
        self.write('package.json', json.dumps({'scripts': {'test': 'jest', 'lint': 'eslint .', 'start': 'x'}}))
        self.write('yarn.lock')
        self.write('jest.config.js')
        commands = self.commands(self.overview())
        self.assertEqual(set(commands), {'yarn test', 'yarn run lint'})
        self.assertIn('"test" script', commands['yarn test']['basis'])

    def test_wordpress_woocommerce_and_composer_scripts(self):
        self.write('composer.json', json.dumps({'scripts': {'test': 'phpunit', 'phpcs': 'phpcs'}}))
        self.write('wp-content/plugins/woocommerce/woocommerce.php')
        self.write('wp-content/themes/shop/functions.php')
        self.write('wp-config.php', 'secret')
        result = self.overview()
        self.assertTrue({'php', 'wordpress', 'woocommerce'} <= set(result['ecosystems']))
        self.assertEqual(set(self.commands(result)), {'composer run test', 'composer run phpcs'})
        self.assertNotIn('wp-config.php', json.dumps(result))
        self.assertEqual(result['languages']['php'], 2)

    def test_other_ecosystems_and_makefile_target(self):
        self.write('go.mod', 'module x\n')
        self.write('Cargo.toml')
        self.write('app.csproj')
        self.write('Makefile', 'build:\n\tcc x\ntest:\n\t./run\n')
        commands = set(self.commands(self.overview()))
        self.assertTrue({'go test ./...', 'cargo test', 'dotnet test', 'make test'} <= commands)

    def test_instruction_files_are_ordered_from_root_to_nearest_scope(self):
        for name in ('AGENTS.md', 'README.md', 'packages/api/AGENTS.md', 'packages/api/README.md',
                     '.claude/rules/style.md', 'docs/CONTRIBUTING.md'):
            self.write(name)
        self.write('docs/agents.md')  # documentation about agents, not an instruction file
        self.write('docs/claude.md')
        entries = self.overview()['instructions']
        paths = [entry['path'] for entry in entries]
        self.assertEqual(paths[:2], ['AGENTS.md', 'README.md'])
        self.assertNotIn('packages/api/README.md', paths)  # only the root README is listed
        self.assertNotIn('docs/agents.md', paths)
        self.assertNotIn('docs/claude.md', paths)
        self.assertEqual(paths[-1], 'packages/api/AGENTS.md')
        self.assertEqual({e['scope'] for e in entries if e['path'].startswith('packages')}, {'packages/api'})

    def test_policy_still_applies_and_checks_follow_visibility(self):
        self.write('package.json', json.dumps({'scripts': {'test': 'x'}}))
        self.write('private/composer.json', '{}')
        checks = {'tests': [sys.executable, '-c', '1']}
        visible = self.overview(checks=checks, deny=['private/**'])
        self.assertNotIn('private/composer.json', json.dumps(visible))
        self.assertEqual(visible['configured_checks'], ['tests'])
        hidden = self.overview(checks=checks, allow_write=True)
        self.assertEqual(hidden['configured_checks'], [])
        self.assertTrue(hidden['checks_hidden'])
        shown = self.overview(checks=checks, allow_write=True, allow_check_after_write=True)
        self.assertEqual(shown['configured_checks'], ['tests'])

    def test_manifests_that_look_like_credentials_are_skipped_not_fatal(self):
        self.write('package.json', json.dumps({'scripts': {'test': 'x'}, 'note': SECRET}))
        result = self.overview()
        self.assertIn('package.json', result['manifests'])
        self.assertEqual(result['candidate_commands'], [])

    def test_partial_and_truncation_are_signaled(self):
        for number in range(45):
            self.write(f'pkg{number:02d}/package.json', '{}')
        self.assertTrue(self.overview()['lists_truncated'])
        with patch.object(tools_module, 'MAX_SCANNED_FILES', 10):
            result = self.overview()
        self.assertTrue(result['partial'])
        self.assertIn('partial', result['note'])


def tool_call(index, tool, **arguments):
    return {'id': str(index), 'type': 'function',
            'function': {'name': tool, 'arguments': json.dumps(arguments)}}


class Script:
    def __init__(self, *rounds):
        self.rounds = list(rounds)
        self.seen = []
        self.max_payload = 250_000

    def complete(self, messages, tools):
        self.seen.append(json.loads(json.dumps(messages)))
        step = self.rounds.pop(0)
        if isinstance(step, str):
            return {'role': 'assistant', 'content': step}
        return {'role': 'assistant', 'content': None, 'tool_calls': step}


class LoopGuardTests(Case):
    def results(self, client):
        return [json.loads(m['content']) for m in client.seen[-1] if m['role'] == 'tool']

    def test_third_identical_call_and_result_gets_a_corrective_error(self):
        self.write('a.txt')
        client = Script(*([[tool_call(i, 'list_files')] for i in range(3)] + ['done']))
        self.assertEqual(run(client, Workspace(self.root), 'task', 6), 'done')
        first, second, third = self.results(client)
        self.assertIn('files', first)
        self.assertEqual(first, second)
        self.assertIn('Repeated identical call', third['error'])

    def test_the_fifth_repetition_aborts_the_run(self):
        self.write('a.txt')
        client = Script(*([[tool_call(i, 'list_files')] for i in range(8)] + ['done']))
        with self.assertRaisesRegex(AgentError, 'repeating the same tool call'):
            run(client, Workspace(self.root), 'task', 10)
        self.assertEqual(len(client.seen), 5)

    def test_a_changed_result_resets_the_count(self):
        self.write('a.txt')
        rounds = [[tool_call(1, 'list_files')], [tool_call(2, 'list_files')],
                  [tool_call(3, 'write_file', path='b.txt', content='y', expected_sha256=None)],
                  [tool_call(4, 'list_files')], [tool_call(5, 'list_files')], 'done']
        self.assertEqual(run(Script(*rounds), Workspace(self.root, allow_write=True), 'task', 8), 'done')

    def test_alternating_calls_are_still_detected(self):
        self.write('a.txt')
        pattern = [('list_files', {}), ('read_file', {'path': 'a.txt'})]
        rounds = [[tool_call(i, pattern[i % 2][0], **pattern[i % 2][1])] for i in range(5)]
        client = Script(*rounds, 'done')
        run(client, Workspace(self.root), 'task', 8)
        self.assertIn('Repeated identical call', self.results(client)[4]['error'])

    def test_spaced_rereads_are_not_flagged(self):
        self.write('a.txt')
        rounds = []
        for block in range(3):
            rounds.append([tool_call(f'a{block}', 'list_files')])
            rounds += [[tool_call(f'q{block}{n}', 'search_text', query=f'q{block}{n}')] for n in range(5)]
        client = Script(*rounds, 'done')
        self.assertEqual(run(client, Workspace(self.root), 'task', 30), 'done')
        self.assertNotIn('Repeated identical call', json.dumps(self.results(client)))


class TraceTests(Case):
    def test_events_describe_the_run_without_any_content(self):
        self.write('notes.txt', 'UNIQUE-CONTENT-MARKER')
        events = []
        client = Script([tool_call(1, 'read_file', path='notes.txt'), tool_call(2, 'read_file', path='nope.txt')],
                        'done')
        run(client, Workspace(self.root), 'task', 4, trace=events.append)
        kinds = [event['event'] for event in events]
        self.assertEqual(kinds, ['round', 'tool', 'tool', 'round', 'finish'])
        ok, failed = events[1], events[2]
        self.assertEqual((ok['tool'], ok['outcome'], failed['outcome']), ('read_file', 'ok', 'error'))
        self.assertEqual(failed['error'], 'File not found.')
        self.assertGreater(ok['result_bytes'], 0)
        self.assertNotIn('UNIQUE-CONTENT-MARKER', json.dumps(events))
        self.assertNotIn('notes.txt', json.dumps(events))

    def test_writer_appends_json_lines_and_restricts_permissions(self):
        target = self.root / 'trace.jsonl'
        with JsonlTrace(target) as trace:
            trace({'event': 'a', 'n': 1})
            trace({'event': 'b'})
        lines = [json.loads(line) for line in target.read_text().splitlines()]
        self.assertEqual([line['event'] for line in lines], ['a', 'b'])
        self.assertIn('time', lines[0])
        if os.name != 'nt':
            self.assertEqual(target.stat().st_mode & 0o777, 0o600)

    def test_writer_refuses_a_directory_and_a_missing_parent(self):
        with self.assertRaisesRegex(ValueError, 'directory'):
            JsonlTrace(self.root)
        with self.assertRaisesRegex(ValueError, 'does not exist'):
            JsonlTrace(self.root / 'missing' / 'trace.jsonl')

    def test_cli_option_passes_a_trace_and_closes_it(self):
        target = self.root / 'out.jsonl'
        seen = {}

        def fake_run(client, workspace, task, max_steps, notify=None, trace=None):
            seen['trace'] = trace
            trace({'event': 'probe'})
            return 'ok'

        with patch.dict(os.environ, {'SSE_MODEL': 'model'}, clear=True), patch('sse_agent.__main__.run', fake_run), \
                contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            code = main(['--workspace', str(self.root), '--trace', str(target), 'task'])
        self.assertEqual(code, 0)
        self.assertTrue(seen['trace'].stream.closed)
        self.assertEqual(json.loads(target.read_text())['event'], 'probe')


if __name__ == '__main__':
    unittest.main()
