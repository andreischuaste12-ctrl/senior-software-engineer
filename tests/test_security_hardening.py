"""Regression tests for the adversarial-audit hardening.

Credential samples are assembled at run time so this file never contains a contiguous
signature: the agent must remain able to read its own test sources.
"""

import contextlib
import io
import json
import os
from pathlib import Path
import sys
import tempfile
import threading
import unittest
from unittest.mock import patch

from sse_agent import agent as agent_module
from sse_agent.__main__ import main, risk_notices
from sse_agent.agent import AgentError, Client, run
from sse_agent.sensitive import contains_sensitive_content, redact_sensitive_text
from sse_agent.surfaces import execution_surface
from sse_agent.tools import Workspace


def join(*parts):
    return ''.join(parts)


BODY = 'MIIEvgIBADANBgkqhkiG9w0BAQEFAASCBKgwggSkAgEAAoIBAQC7VJTUt9Us'
TOKEN36 = 'aB3dE5gH7jK9mN1pQ3sT5vW7yZ9bD2fH4jL6'
DETECTED = {
    'pem': join('-----BEGIN ', 'RSA PRIVATE KEY-----\n', BODY, '\n-----END ', 'RSA PRIVATE KEY-----\n'),
    'openssh': join('-----BEGIN ', 'OPENSSH PRIVATE KEY-----\n', BODY, '\n'),
    'pgp': join('-----BEGIN ', 'PGP PRIVATE KEY BLOCK-----\nVersion: x\n\n', BODY, '\n'),
    'aws-access': join('AKIA', 'QWERTYUIOPASDFGH'),
    'aws-secret': join('aws_secret_access_key = ', 'wJalrXUtnFEMI/K7MDENG/bPxRf', 'iCYzQ8vN3pLkZ'),
    'github': join('gh', 'p_', TOKEN36),
    'github-pat': join('github', '_pat_', '11AB3DE5GH7JK9MN1PQ3ST5VW7YZ9bD2fH4jL6nP8rT0'),
    'slack': join('xox', 'b-', '1234567890-abcdefghijklmnopqrst'),
    'openai': join('sk-', 'proj-', TOKEN36),
    'anthropic': join('sk-', 'ant-', 'api03-', TOKEN36),
    'stripe': join('sk', '_live_', 'aB3dE5gH7jK9mN1pQ3sT5vW7'),
    'google': join('AI', 'za', TOKEN36[:35]),
    'jwt': join('eyJhbGciOiJIUzI1NiJ9', '.', 'eyJzdWIiOiIxMjM0NTY3ODkwIn0', '.', 'dozjgNryP4J3jVmN'),
    'database': join('postgres', '://admin:', 'S3cretPassw0rd', '@db.internal:5432/app'),
    'npm': join('npm', '_', TOKEN36),
    'gitlab': join('glpat', '-', 'aB3dE5gH7jK9mN1pQ3sT5v'),
    'sendgrid': join('SG', '.', 'aB3dE5gH7jK9mN1pQ3', '.', 'sT5vW7yZ9bD2fH4jL6mN1pQ3sT5v'),
    'azure': join('AccountKey', '=', 'aB3dE5gH7jK9mN1pQ3sT5vW7yZ9bD2fH4jL6mN1p', '=='),
    'woocommerce': join('ck', '_', 'a1b2c3d4e5f60718293a4b5c6d7e8f9012345678'),
    'shopify': join('shp', 'at_', 'a1b2c3d4e5f60718293a4b5c6d7e8f90'),
    'mercadopago': join('APP', '_USR-', '1234567890123456-123456-', 'a1b2c3d4e5f60718293a4b5c6d7e8f90', '-123456789'),
}
PLACEHOLDERS = {
    'aws documentation example': 'AKIAIOSFODNN7EXAMPLE',
    'repeated token body': join('gh', 'p_', 'a' * 36),
    'private-key header without a body': join('-----BEGIN ', 'PRIVATE KEY-----'),
    'public key': join('-----BEGIN ', 'PUBLIC KEY-----\n', BODY, '\n'),
    'weak database password': join('postgres', '://user:', 'password', '@localhost/db'),
    'templated database password': join('postgres', '://app:', '${DB_PASSWORD}', '@db/app'),
    'ordinary code': 'def hello():\n    return "hello"\n',
}


class WorkspaceCase(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name)

    def write(self, name, data='x'):
        target = self.root / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data if isinstance(data, bytes) else data.encode('utf-8'))
        return target

    def readable(self, workspace, name):
        return 'error' not in workspace.execute('read_file', {'path': name})


@unittest.skipUnless(hasattr(os, 'mkfifo'), 'POSIX FIFOs')
class FifoTests(WorkspaceCase):
    def setUp(self):
        super().setUp()
        os.mkfifo(self.root / 'pipe')
        self.write('a.txt', 'needle')
        self.workspace = Workspace(self.root, allow_write=True)

    def call(self, name, arguments):
        result = []
        thread = threading.Thread(target=lambda: result.append(self.workspace.execute(name, arguments)),
                                  daemon=True)
        thread.start()
        thread.join(5)
        self.assertFalse(thread.is_alive(), f'{name} blocked on a FIFO')
        return result[0]

    def test_direct_access_to_a_fifo_is_refused_without_blocking(self):
        for name, arguments in (
                ('read_file', {'path': 'pipe'}),
                ('write_file', {'path': 'pipe', 'content': 'x', 'expected_sha256': 'a' * 64}),
                ('replace_in_file', {'path': 'pipe', 'old': 'a', 'new': 'b', 'expected_sha256': 'a' * 64})):
            with self.subTest(tool=name):
                self.assertIn('regular files', self.call(name, arguments)['error'])

    def test_search_and_listing_skip_the_fifo(self):
        self.assertNotIn('pipe', self.workspace.list_files()['files'])
        result = self.call('search_text', {'query': 'needle'})
        self.assertEqual([m['path'] for m in result['matches']], ['a.txt'])


class ExecutionSurfaceTests(WorkspaceCase):
    BLOCKED = [
        'conftest.py', 'sub/conftest.py', 'Makefile', 'MAKEFILE', 'build.rs', 'build.gradle', 'pom.xml',
        'CMakeLists.txt', 'Rakefile', 'webpack.config.js', 'Jenkinsfile', '.gitlab-ci.yml', 'tox.ini',
        'setup.cfg', 'pytest.ini', 'usercustomize.py', '.github/actions/x/action.yml', '.githooks/pre-commit',
        '.circleci/config.yml', '.bashrc', 'x.bash', 'x.zsh', 'x.pth', 'bin/deploy', 'hack/run', 'Procfile',
        'justfile', 'Cargo.toml', 'docker-compose.yml', 'scripts/build.sh', '.vscode/tasks.json',
        '.github/workflows/ci.yml', '.github//workflows/ci.yml', '.github/./workflows/ci.yml',
        './.vscode/tasks.json', '.vscode\\tasks.json', '.GITHUB/Workflows/ci.yml',
    ]
    ALLOWED = ['src/app.py', 'README.md', 'src/vendor/model.py', 'docs/guide.md', 'tests/test_x.py',
               'src/config.json', 'binary_search.py', 'src/robin/notes.md']

    def test_classification_uses_the_normalized_path(self):
        for path in self.BLOCKED:
            with self.subTest(path=path):
                self.assertTrue(execution_surface(path))
        for path in self.ALLOWED:
            with self.subTest(path=path):
                self.assertFalse(execution_surface(path))

    def test_file_tools_enforce_the_rule_and_the_flag_lifts_it(self):
        for path in self.BLOCKED:
            parent = Path(path.replace('\\', '/')).parent
            (self.root / parent).mkdir(parents=True, exist_ok=True)
        restricted = Workspace(self.root, allow_write=True)
        permitted = Workspace(self.root, allow_write=True, allow_executable_write=True)
        for path in self.BLOCKED:
            with self.subTest(path=path):
                request = {'path': path, 'content': 'echo x\n', 'expected_sha256': None}
                self.assertIn('allow-executable-write', restricted.execute('write_file', request)['error'])
                self.assertNotIn('error', permitted.execute('write_file', request))
                (self.root / path.replace('\\', '/')).unlink()

    def test_interpreter_lines_require_the_flag_even_on_ordinary_names(self):
        workspace = Workspace(self.root, allow_write=True)
        new = workspace.execute('write_file', {'path': 'tool', 'content': '#!/bin/sh\necho x\n',
                                               'expected_sha256': None})
        self.assertIn('allow-executable-write', new['error'])
        self.write('notes.txt', 'plain\n')
        digest = workspace.read_file('notes.txt')['sha256']
        promoted = workspace.execute('replace_in_file', {'path': 'notes.txt', 'old': 'plain',
                                                         'new': '#!/bin/sh', 'expected_sha256': digest})
        self.assertIn('allow-executable-write', promoted['error'])
        self.write('script', '#!/bin/sh\necho x\n')
        digest = workspace.read_file('script')['sha256']
        edit = workspace.execute('replace_in_file', {'path': 'script', 'old': 'echo x', 'new': 'echo y',
                                                     'expected_sha256': digest})
        self.assertIn('allow-executable-write', edit['error'])
        self.assertEqual((self.root / 'script').read_text(), '#!/bin/sh\necho x\n')

    def test_file_mode_is_not_used_so_ntfs_mounts_remain_usable(self):
        target = self.write('plain.txt', 'a\n')
        if os.name != 'nt':
            target.chmod(0o777)  # NTFS/drvfs mounts report every file like this
        workspace = Workspace(self.root, allow_write=True)
        digest = workspace.read_file('plain.txt')['sha256']
        self.assertNotIn('error', workspace.execute('replace_in_file', {
            'path': 'plain.txt', 'old': 'a', 'new': 'b', 'expected_sha256': digest}))


class SensitiveContentTests(WorkspaceCase):
    def test_every_signature_is_detected_and_redacted(self):
        for name, sample in DETECTED.items():
            with self.subTest(sample=name):
                self.assertTrue(contains_sensitive_content(sample.encode()), name)
                redacted, changed = redact_sensitive_text(f'before\n{sample}\nafter')
                self.assertTrue(changed)
                self.assertIn('[REDACTED:', redacted)
                self.assertNotIn(BODY, redacted)
                self.assertNotIn(TOKEN36, redacted)

    def test_documentation_placeholders_are_not_flagged(self):
        for name, sample in PLACEHOLDERS.items():
            with self.subTest(sample=name):
                self.assertFalse(contains_sensitive_content(sample.encode()), name)

    def test_files_with_credentials_are_refused_but_placeholder_files_are_readable(self):
        workspace = Workspace(self.root, allow_write=True)
        self.write('deploy.txt', DETECTED['openai'])
        self.write('README.md', PLACEHOLDERS['aws documentation example'])
        self.assertIn('credential', workspace.execute('read_file', {'path': 'deploy.txt'})['error'])
        self.assertTrue(self.readable(workspace, 'README.md'))

    def test_search_reports_skipped_files_instead_of_a_false_no_match(self):
        self.write('src/mod.py', 'def unique_symbol():\n    pass\n')
        self.write('docs/leaky.md', f'{DETECTED["github"]}\nunique_symbol\n')
        self.write('data.bin', b'\x00\x01unique_symbol')
        result = Workspace(self.root).execute('search_text', {'query': 'unique_symbol'})
        self.assertEqual([m['path'] for m in result['matches']], ['src/mod.py'])
        self.assertEqual(result['skipped'], 2)
        self.assertFalse(result['truncated'])

    def test_check_output_is_redacted_before_it_reaches_the_model(self):
        code = f'print({DETECTED["github"]!r}); print("kept line")'
        workspace = Workspace(self.root, checks={'t': [sys.executable, '-c', code]})
        result = workspace.run_check('t')
        self.assertTrue(result['redacted'])
        self.assertIn('[REDACTED:github-token]', result['output'])
        self.assertIn('kept line', result['output'])
        self.assertNotIn(TOKEN36, result['output'])
        self.assertFalse(Workspace(self.root, checks={'t': [sys.executable, '-c', 'print(1)']})
                         .run_check('t')['redacted'])


class ProtectedNameTests(WorkspaceCase):
    BLOCKED = ['wp-config-local.php', 'app/etc/env.php', 'sites/default/settings.php', 'LocalSettings.php',
               '.terraformrc', '.azure/accessTokens.json', 'sftp-config.json', 'parameters.yml',
               'config.inc.php', '.config/rclone/rclone.conf', 'secrets.toml', '.secrets',
               'sub/.cargo/credentials.toml', 'sub/.config/gh/hosts.yml', '.config/gcloud/credentials.db',
               'service-account-prod.json', 'client_secret_123.json', 'deploy.secret', 'id_rsa_deploy',
               'id_ed25519_ci', 'shop/app/etc/env.php']
    ALLOWED = ['id_rsa.pub', 'src/settings.php', 'app/etc/config.php', 'sites/default/default.settings.php',
               'wp-config-sample.php', '.cargo/config.toml']

    def test_names_and_relative_paths_are_protected_at_any_depth(self):
        for name in self.BLOCKED + self.ALLOWED:
            self.write(name)
        workspace = Workspace(self.root)
        for name in self.BLOCKED:
            with self.subTest(name=name):
                self.assertFalse(self.readable(workspace, name))
                self.assertNotIn(name, workspace.list_files()['files'])
        for name in self.ALLOWED:
            with self.subTest(name=name):
                self.assertTrue(self.readable(workspace, name))

    def test_windows_aliases_are_rejected_only_on_windows(self):
        self.write('GIT~1/config')
        workspace = Workspace(self.root)
        self.assertTrue(self.readable(workspace, 'GIT~1/config'))
        with patch('sse_agent.tools.WINDOWS', True):
            self.assertFalse(self.readable(workspace, 'GIT~1/config'))


class WorkspaceRootTests(WorkspaceCase):
    @unittest.skipIf(os.name == 'nt', 'POSIX system directories')
    def test_system_directories_are_rejected(self):
        for root in ('/etc', '/usr', '/var', '/home', '/proc', '/tmp', '/opt'):
            if Path(root).is_dir():
                with self.subTest(root=root), self.assertRaisesRegex(ValueError, 'project directory'):
                    Workspace(root)

    def test_home_and_its_parents_are_rejected_but_siblings_are_not(self):
        home = self.root / 'people' / 'ana'
        home.mkdir(parents=True)
        (self.root / 'projects').mkdir()
        with patch.object(Path, 'home', return_value=home):
            for rejected in (home, home.parent, self.root):
                with self.subTest(root=str(rejected)), self.assertRaisesRegex(ValueError, 'project directory'):
                    Workspace(rejected)
            self.assertEqual(Workspace(self.root / 'projects').root, (self.root / 'projects').resolve())

    def test_roots_inside_credential_directories_are_rejected(self):
        for name in ('.ssh', '.git', '.aws', 'node_modules'):
            (self.root / name).mkdir()
            with self.subTest(root=name), self.assertRaisesRegex(ValueError, 'protected'):
                Workspace(self.root / name)

    def test_unavailable_home_directory_does_not_block_a_valid_project(self):
        with patch.object(Path, 'home', side_effect=RuntimeError('no home')):
            self.assertEqual(Workspace(self.root).root, self.root.resolve())


class ErrorMessageTests(WorkspaceCase):
    def test_file_errors_are_specific_but_never_expose_host_paths(self):
        workspace = Workspace(self.root)
        self.assertEqual(workspace.execute('read_file', {'path': 'missing.txt'}), {'error': 'File not found.'})
        too_long = workspace.execute('read_file', {'path': 'a' * 300})
        self.assertNotIn(str(self.root), json.dumps(too_long))
        self.write('dir/file.txt')
        self.assertIn('regular files', workspace.execute('read_file', {'path': 'dir'})['error'])


class Script:
    def __init__(self, *rounds, max_payload=250_000):
        self.rounds = list(rounds)
        self.max_payload = max_payload
        self.seen = []

    def complete(self, messages, tools):
        self.seen.append(json.loads(json.dumps(messages)))
        step = self.rounds.pop(0)
        if isinstance(step, str):
            return {'role': 'assistant', 'content': step}
        return {'role': 'assistant', 'content': None, 'tool_calls': step}


def tool_call(index, tool, **arguments):
    return {'id': str(index), 'type': 'function',
            'function': {'name': tool, 'arguments': json.dumps(arguments)}}


class RoundBudgetTests(WorkspaceCase):
    def test_effectful_results_are_never_replaced_once_the_tool_ran(self):
        self.write('big.txt', 'b' * 5000)
        self.write('w.txt', 'old\n')
        marker = self.root / 'ran.txt'
        digest = Workspace(self.root).read_file('w.txt')['sha256']
        code = f'import pathlib; pathlib.Path({str(marker)!r}).write_text("x"); print("FAIL " * 2000)'
        workspace = Workspace(self.root, allow_write=True, allow_check_after_write=True,
                              checks={'tests': [sys.executable, '-c', code]})
        client = Script([tool_call(1, 'read_file', path='big.txt'),
                         tool_call(2, 'write_file', path='w.txt', content='new\n', expected_sha256=digest),
                         tool_call(3, 'run_check', name='tests')], 'done')
        with patch.object(agent_module, 'MIN_ROUND_BUDGET', 150), \
                patch.object(agent_module, 'MAX_ROUND_TOOL_RESULT_BYTES', 150):
            run(client, workspace, 'task', 3)
        results = [json.loads(m['content']) for m in client.seen[-1] if m['role'] == 'tool']
        self.assertIn('limit', results[0]['error'])  # a read has no side effect: safe to refuse
        self.assertTrue(results[1]['written'])
        self.assertEqual((self.root / 'w.txt').read_text(), 'new\n')
        self.assertEqual(results[2]['exit_code'], 0)
        self.assertTrue(results[2]['truncated'])
        self.assertIn('shortened to fit', results[2]['output'])
        self.assertTrue(marker.exists())

    def test_small_context_limit_does_not_fail_after_a_paid_call(self):
        self.write('r60.txt', 'z' * 60000)
        client = Client('k', 'm', 'http://127.0.0.1:1/v1', max_payload=60000)
        replies = [
            {'choices': [{'message': {'role': 'assistant', 'content': None,
                                      'tool_calls': [tool_call(1, 'read_file', path='r60.txt')]},
                          'finish_reason': 'tool_calls'}]},
            {'choices': [{'message': {'role': 'assistant', 'content': 'done'}, 'finish_reason': 'stop'}]}]
        sent = []

        def fake_post(payload):
            sent.append(len(payload))
            return json.dumps(replies.pop(0)).encode()

        client._post = fake_post  # type: ignore[method-assign]
        self.assertEqual(run(client, Workspace(self.root), 'task', 3), 'done')
        self.assertLessEqual(max(sent), 60000)
        self.assertEqual(len(sent), 2)


class ProtocolToleranceTests(WorkspaceCase):
    def test_missing_call_ids_are_synthesized_and_paired(self):
        self.write('a.txt', 'a')
        client = Script([{'function': {'name': 'list_files', 'arguments': '{}'}},
                         {'type': 'function', 'function': {'name': 'list_files', 'arguments': '{}'}}], 'done')
        self.assertEqual(run(client, Workspace(self.root), 'task', 3), 'done')
        history = client.seen[-1]
        assistant = [m for m in history if m['role'] == 'assistant'][0]
        ids = [call['id'] for call in assistant['tool_calls']]
        self.assertEqual(ids, ['call_0', 'call_1'])
        self.assertEqual([m['tool_call_id'] for m in history if m['role'] == 'tool'], ids)

    def test_non_text_content_parts_are_ignored_instead_of_aborting(self):
        client = Client('k', 'm', 'http://127.0.0.1:1/v1')

        def reply(content):
            body = {'choices': [{'message': {'role': 'assistant', 'content': content},
                                 'finish_reason': 'stop'}]}
            return lambda payload: json.dumps(body).encode()

        client._post = reply([{'type': 'refusal', 'refusal': 'no'}, {'type': 'text', 'text': 'ok'}])  # type: ignore[method-assign]
        self.assertEqual(client.complete([], [])['content'], 'ok')
        client._post = reply([{'type': 'refusal', 'refusal': 'no'}])  # type: ignore[method-assign]
        with self.assertRaisesRegex(AgentError, 'final content'):
            run(client, Workspace(self.root), 'task', 1)


class RiskNoticeTests(WorkspaceCase):
    def notices(self, base_url='http://127.0.0.1:1234/v1', allow_remote=False, **workspace_options):
        workspace = Workspace(self.root, **workspace_options)
        client = Client('key', 'model', base_url, allow_remote=allow_remote)
        return '\n'.join(risk_notices(workspace, client))

    def test_local_endpoint_notice(self):
        text = self.notices()
        self.assertIn('local endpoint 127.0.0.1', text)
        self.assertNotIn('EXTERNAL', text)

    def test_external_endpoint_names_the_provider_and_recommends_filters(self):
        text = self.notices('https://api.example.com/v1', allow_remote=True)
        self.assertIn('EXTERNAL ENDPOINT api.example.com', text)
        self.assertIn('No --allow-file or --deny filter', text)
        self.assertNotIn('No --allow-file', self.notices('https://api.example.com/v1', allow_remote=True,
                                                         allow_files=['src/**']))

    def test_check_and_write_risks_are_spelled_out(self):
        checks = {'t': [sys.executable, '-c', '1']}
        self.assertIn('not a sandbox', self.notices(checks=checks))
        self.assertIn('disabled in this write session', self.notices(allow_write=True, checks=checks))
        text = self.notices(allow_write=True, allow_check_after_write=True,
                            allow_executable_write=True, checks=checks)
        self.assertIn('checks may execute code written by the model', text)
        self.assertIn('automation files', text)


class TaskCredentialTests(WorkspaceCase):
    def run_main(self, task, **environment):
        base = {'SSE_MODEL': 'model', 'SSE_API_KEY': 'key'}
        errors = io.StringIO()
        with patch.dict(os.environ, {**base, **environment}, clear=True), \
                patch('sse_agent.__main__.run', return_value='ok') as runner, \
                contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(errors):
            code = main(['--workspace', str(self.root), '--allow-remote', task])
        return code, errors.getvalue(), runner

    def test_external_api_refuses_a_task_that_contains_a_credential(self):
        code, errors, runner = self.run_main(f'deploy with {DETECTED["github"]}',
                                             SSE_BASE_URL='https://api.example.com/v1')
        self.assertEqual(code, 1)
        self.assertIn('credential-like', errors)
        runner.assert_not_called()

    def test_local_endpoint_only_warns(self):
        code, errors, runner = self.run_main(f'deploy with {DETECTED["github"]}')
        self.assertEqual(code, 0)
        self.assertIn('Warning: the task text contains credential-like content', errors)
        runner.assert_called_once()

    def test_clean_task_reaches_the_external_endpoint_with_the_provider_notice(self):
        code, errors, runner = self.run_main('Review the code', SSE_BASE_URL='https://api.example.com/v1')
        self.assertEqual(code, 0)
        self.assertIn('EXTERNAL ENDPOINT api.example.com', errors)
        runner.assert_called_once()


if __name__ == '__main__':
    unittest.main()
