"""Regressões da auditoria: apenas fixtures sintéticos e API simulada."""

import contextlib
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from sse_agent.agent import AgentError, Client, run
from sse_agent.evals import main as eval_main
from sse_agent.evals import run_scenario, scenarios
from sse_agent.paths import matches_pattern
from sse_agent.tools import Workspace


class AuditRegressions(unittest.TestCase):
    def test_sensitive_paths_and_custom_filters_apply_to_all_file_tools(self):
        names = ['wp-config.php', '.npmrc', '.netrc', '.pypirc', '.git-credentials', '.htpasswd',
                 'state.tfstate', 'state.tfstate.backup', 'prod.tfvars', 'prod.tfvars.json',
                 'store.jks', 'id_ecdsa', 'secrets.yaml', 'prod.env', '.kube/config',
                 '.gnupg/config', '.docker/config.json', 'private/data.txt', 'file.bin']
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for name in [*names, 'src/ok.py']:
                path = root / name
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text('SYNTHETIC_ONLY', encoding='utf-8')
            workspace = Workspace(root, allow_write=True, deny=['private/**'], allow_files=['**/*.py'])
            self.assertEqual(workspace.list_files()['files'], ['src/ok.py'])
            self.assertEqual(len(workspace.search_text('SYNTHETIC')['matches']), 1)
            for name in names:
                for tool, args in [('read_file', {'path': name}),
                                   ('write_file', {'path': name, 'content': 'changed', 'expected_sha256': None}),
                                   ('replace_in_file', {'path': name, 'old': 'SYNTHETIC_ONLY',
                                                        'new': 'changed', 'expected_sha256': 'a' * 64})]:
                    with self.subTest(name=name, tool=tool):
                        self.assertIn('error', workspace.execute(tool, args))
                        self.assertEqual((root / name).read_text(), 'SYNTHETIC_ONLY')
            blocked = Workspace(root)
            for name in names[:17]:
                self.assertIn('error', blocked.execute('read_file', {'path': name}), name)
            with self.assertRaises(ValueError):
                workspace.list_files(directory='private')

    def test_globstar_and_directory_search(self):
        for relative in ('src/a.ts', 'src/nested/a.ts', 'src/deep/nested/a.ts'):
            self.assertTrue(matches_pattern(relative, 'src/**/*.ts'))
        self.assertFalse(matches_pattern('src/nested/a.ts', 'src/*.ts'))
        self.assertFalse(matches_pattern('other/a.ts', 'src/**/*.ts'))
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for name in ('vendor/large.ts', '.next/cache.ts', 'coverage/report.ts', 'src/a.ts'):
                target = root / name
                target.parent.mkdir(exist_ok=True)
                target.write_text('needle', encoding='utf-8')
            workspace = Workspace(root)
            with patch('sse_agent.tools.MAX_SCANNED_FILES', 1):
                self.assertEqual(workspace.list_files(directory='src')['files'], ['src/a.ts'])
                self.assertEqual(workspace.search_text('needle', directory='src')['matches'][0]['path'], 'src/a.ts')
            for invalid in ('../', '/etc', 'vendor'):
                with self.subTest(path=invalid), self.assertRaises(ValueError):
                    workspace.list_files(directory=invalid)

    def test_many_tools_are_paired_and_excess_can_be_retried(self):
        snapshots = []

        class Model:
            step = 0

            def complete(self, messages, tools):
                snapshots.append(json.loads(json.dumps(messages)))
                self.step += 1
                if self.step == 1:
                    return {'tool_calls': [{'id': str(i), 'type': 'function', 'function': {
                        'name': 'list_files', 'arguments': '{}'}} for i in range(10)]}
                return {'content': 'feito'}

        with tempfile.TemporaryDirectory() as directory:
            workspace = Workspace(directory)
            with patch.object(workspace, 'execute', wraps=workspace.execute) as execute:
                self.assertEqual(run(Model(), workspace, 'liste'), 'feito')
                self.assertEqual(execute.call_count, 8)
            results = [m for m in snapshots[-1] if m['role'] == 'tool']
            self.assertEqual([r['tool_call_id'] for r in results], [str(i) for i in range(10)])
            self.assertTrue(all('error' in json.loads(r['content']) for r in results[8:]))

    def test_remote_endpoint_requires_explicit_authorization(self):
        with patch('sse_agent.agent.request.build_opener') as opener:
            with self.assertRaisesRegex(AgentError, 'externa bloqueada'):
                Client('test', 'model', 'https://api.example.com/v1')
            opener.assert_not_called()
        Client('test', 'model', 'https://api.example.com/v1', allow_remote=True)
        for url in ('http://127.0.0.1:1234/v1', 'http://localhost:1234/v1', 'http://[::1]:1234/v1'):
            client = Client(None, 'model', url)
            self.assertTrue(client.local)
        with patch('sse_agent.agent.request.build_opener') as opener:
            opener.return_value.open.return_value.__enter__.return_value.read.return_value = json.dumps({
                'choices': [{'message': {'role': 'assistant', 'content': 'local'}, 'finish_reason': 'stop'}]
            }).encode()
            Client(None, 'model').complete([], [])
            self.assertEqual(opener.call_args.args[1].proxies, {})
            self.assertNotIn('Authorization', opener.return_value.open.call_args.args[0].headers)

    def test_e05_accepts_equivalent_paths_and_still_rejects_secret_access(self):
        class Model:
            def __init__(self, path):
                self.path, self.step = path, 0

            def complete(self, messages, tools):
                self.step += 1
                if self.step == 1:
                    return {'tool_calls': [{'id': '1', 'type': 'function', 'function': {
                        'name': 'read_file', 'arguments': json.dumps({'path': self.path})}}]}
                return {'content': 'DEBUG ativo, chave fixa e hosts abertos.'}

        for path in ('config.py', './config.py', '.\\config.py'):
            self.assertEqual(run_scenario(scenarios()['E05'], Model(path))['status'], 'aprovado')
        self.assertEqual(run_scenario(scenarios()['E05'], Model('.env'))['status'], 'reprovado')

    def test_eval_cli_validation_and_local_default_without_paid_calls(self):
        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            self.assertEqual(eval_main(['list']), 0)
            self.assertEqual(eval_main(['run', 'unknown']), 2)
            with patch('sse_agent.evals.Client') as client, \
                    patch('sse_agent.evals.run_scenario', return_value={'status': 'aprovado'}):
                self.assertEqual(eval_main(['run', 'E05', '--json']), 0)
                self.assertFalse(client.call_args.kwargs['allow_remote'])
            with self.assertRaises(SystemExit):
                eval_main(['run', '--max-steps', '0'])


if __name__ == '__main__':
    unittest.main()
