import hashlib
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import threading
import unittest
from unittest.mock import patch

from sse_agent.agent import AgentError, Client, run
from sse_agent.tools import Workspace


class WorkspaceTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name)
        (self.root / 'sample.py').write_text('original\n')
        self.workspace = Workspace(self.root, allow_write=True)

    def test_read_write_and_stale_hash(self):
        original = self.workspace.read_file('sample.py')
        self.workspace.write_file('sample.py', 'modified\n', original['sha256'])
        with self.assertRaises(ValueError):
            self.workspace.write_file('sample.py', 'stale', original['sha256'])
        self.assertEqual((self.root / 'sample.py').read_text(), 'modified\n')

    def test_new_file_cannot_overwrite_without_reading(self):
        self.workspace.write_file('new.py', 'new\n', None)
        with self.assertRaises(ValueError):
            self.workspace.write_file('new.py', 'overwrite', None)
        self.assertEqual((self.root / 'new.py').read_text(), 'new\n')

    def test_read_only_denies_write(self):
        workspace = Workspace(self.root)
        result = workspace.execute('write_file', {'path': 'sample.py', 'content': 'bad',
                                                  'expected_sha256': None})
        self.assertIn('error', result)
        self.assertEqual((self.root / 'sample.py').read_text(), 'original\n')

    def test_boundaries_secrets_and_symlinks(self):
        (self.root / 'link').symlink_to(self.root / 'sample.py')
        for path in ('../outside', '/etc/passwd', '.git/config', '.env', '.env.local',
                     'credentials.json', 'private.key', 'link'):
            with self.subTest(path=path), self.assertRaises(ValueError):
                self.workspace.read_file(path)

    def test_listing_omits_protected_files(self):
        (self.root / '.env').write_text('not-for-the-model')
        (self.root / '.git').mkdir()
        (self.root / '.git' / 'config').write_text('private')
        self.assertEqual(self.workspace.list_files()['files'], ['sample.py'])

    def test_rejects_large_and_non_utf8_files(self):
        for data in (b'a' * 64_001, b'\xff'):
            (self.root / 'bad').write_bytes(data)
            with self.assertRaises(ValueError):
                self.workspace.read_file('bad')

    def test_check_exit_status_and_api_key_environment(self):
        command = [sys.executable, '-c',
                   'import os,sys; print("clean" if "SSE_API_KEY" not in os.environ '
                   'and "OPENAI_API_KEY" not in os.environ else "leaked"); sys.exit(7)']
        workspace = Workspace(self.root, checks={'tests': command})
        with patch.dict(os.environ, {'SSE_API_KEY': 'test', 'OPENAI_API_KEY': 'test'}):
            result = workspace.run_check('tests')
        self.assertEqual(result['exit_code'], 7)
        self.assertEqual(result['output'].strip(), 'clean')
        self.assertFalse(result['timed_out'])
        self.assertIn('error', workspace.execute('run_check', {'name': 'unapproved'}))

    def test_check_timeout(self):
        workspace = Workspace(self.root, checks={'slow': [sys.executable, '-c',
                                                        'import time; time.sleep(10)']}, timeout=0.1)
        result = workspace.run_check('slow')
        self.assertTrue(result['timed_out'])
        self.assertNotEqual(result['exit_code'], 0)


class AgentTests(unittest.TestCase):
    def test_model_requires_config_and_secure_endpoint(self):
        for base in ('http://example.com/v1', 'https://user:password@example.com/v1',
                     'https://example.com/v1?token=value'):
            with self.subTest(base=base), self.assertRaises(AgentError):
                Client('test', 'model', base)
        with self.assertRaises(AgentError):
            Client(None, 'model')

    def test_round_limit_and_malformed_call_before_effects(self):
        with tempfile.TemporaryDirectory() as directory:
            workspace = Workspace(directory, allow_write=True)
            call = {'id': '1', 'type': 'function', 'function': {'name': 'write_file',
                    'arguments': json.dumps({'path': 'new', 'content': 'unexpected',
                                             'expected_sha256': None})}}
            class Malformed:
                def complete(self, messages, tools):
                    return {'tool_calls': [call, {'invalid': True}]}
            with self.assertRaises(AgentError):
                run(Malformed(), workspace, 'task')
            self.assertFalse((Path(directory) / 'new').exists())
            class Endless:
                def complete(self, messages, tools):
                    return {'tool_calls': [{'id': '1', 'type': 'function',
                            'function': {'name': 'list_files', 'arguments': '{}'}}]}
            with self.assertRaisesRegex(AgentError, 'Limite'):
                run(Endless(), workspace, 'task', max_steps=1)

    def test_cli_full_http_tool_cycle(self):
        requests = []
        failures = []
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / 'example.py').write_text('before\n')
            original_hash = hashlib.sha256(b'before\n').hexdigest()
            actions = [('list_files', {}), ('read_file', {'path': 'example.py'}),
                       ('write_file', {'path': 'example.py', 'content': 'after\n',
                                       'expected_sha256': original_hash}),
                       ('run_check', {'name': 'verify'})]
            class Handler(BaseHTTPRequestHandler):
                def log_message(self, *args):
                    pass

                def do_POST(self):
                    try:
                        payload = json.loads(self.rfile.read(int(self.headers['Content-Length'])))
                        requests.append(payload)
                        index = len(requests) - 1
                        message = {'role': 'assistant', 'content': 'Concluído com check aprovado.'}
                        if index < len(actions):
                            name, arguments = actions[index]
                            message = {'role': 'assistant', 'content': None, 'tool_calls': [
                                {'id': str(index), 'type': 'function', 'function': {
                                    'name': name, 'arguments': json.dumps(arguments)}}]}
                        response = {'choices': [{'message': message,
                                    'finish_reason': 'tool_calls' if index < len(actions) else 'stop'}]}
                        data = json.dumps(response).encode()
                        self.send_response(200)
                        self.send_header('Content-Type', 'application/json')
                        self.send_header('Content-Length', str(len(data)))
                        self.end_headers()
                        self.wfile.write(data)
                    except Exception as error:
                        failures.append(str(error))
                        self.send_error(500)
            server = ThreadingHTTPServer(('127.0.0.1', 0), Handler)
            thread = threading.Thread(target=server.serve_forever, daemon=True)
            thread.start()
            try:
                environment = dict(os.environ, SSE_API_KEY='fake-test-key', SSE_MODEL='fake-model',
                                   SSE_BASE_URL=f'http://127.0.0.1:{server.server_port}/v1')
                command = [sys.executable, '-m', 'sse_agent', '--workspace', directory,
                           '--allow-write', '--check', f'verify={sys.executable} -c "print(123)"',
                           'Altere example.py e valide.']
                result = subprocess.run(command, cwd=Path(__file__).resolve().parent.parent,
                                        env=environment, capture_output=True, text=True, timeout=15)
            finally:
                server.shutdown()
                server.server_close()
                thread.join()
            self.assertFalse(failures)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual((root / 'example.py').read_text(), 'after\n')
            self.assertIn('Concluído', result.stdout)
            self.assertEqual(len(requests), 5)
            prompt = requests[0]['messages'][0]['content']
            self.assertIn('# Senior Software Engineer', prompt)
            self.assertIn('[S1]', prompt)
            self.assertNotIn('3.15.2', prompt)
            outputs = [json.loads(message['content']) for message in requests[-1]['messages']
                       if message['role'] == 'tool']
            self.assertEqual(outputs[-1]['exit_code'], 0)
            self.assertEqual(outputs[-1]['output'].strip(), '123')

    def test_http_failure_and_invalid_response(self):
        client = Client('not-to-be-printed', 'model')
        from urllib.error import HTTPError
        with patch('sse_agent.agent.request.build_opener') as opener:
            opener.return_value.open.side_effect = HTTPError(client.endpoint, 401, 'private-body', {}, None)
            with self.assertRaisesRegex(AgentError, 'HTTP 401') as caught:
                client.complete([], [])
            self.assertNotIn('private-body', str(caught.exception))
            opener.return_value.open.side_effect = None
            opener.return_value.open.return_value.__enter__.return_value.read.return_value = b'{}'
            with self.assertRaisesRegex(AgentError, 'Resposta inválida'):
                client.complete([], [])


if __name__ == '__main__':
    unittest.main()
