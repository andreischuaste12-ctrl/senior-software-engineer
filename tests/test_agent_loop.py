import argparse
import contextlib
import io
import json
import sys
import tempfile
import unittest
from unittest.mock import MagicMock, patch
from urllib.error import HTTPError, URLError

from sse_agent.__main__ import main, parse_checks, positive_float
from sse_agent.agent import AgentError, Client, compact_history, payload_size, retry_delay, run
from sse_agent.tools import Workspace

REPLY = json.dumps({'choices': [{'message': {'role': 'assistant', 'content': 'ok'},
                                 'finish_reason': 'stop'}]}).encode()


def success():
    response = MagicMock()
    response.__enter__.return_value.read.return_value = REPLY
    return response


def failure(status, retry_after=None):
    headers = {'Retry-After': retry_after} if retry_after else {}
    return HTTPError('http://x/v1/chat/completions', status, 'body-not-printed', headers, None)


class RetryTests(unittest.TestCase):
    def test_default_never_retries_rate_limit_or_server_errors(self):
        for status in (429, 500, 502, 503, 504):
            with self.subTest(status=status), patch('sse_agent.agent.request.build_opener') as opener:
                opener.return_value.open.side_effect = failure(status)
                sleeps = []
                client = Client('key', 'model', sleep=sleeps.append)
                with self.assertRaisesRegex(AgentError, f'HTTP {status}'):
                    client.complete([], [])
                self.assertEqual(opener.return_value.open.call_count, 1)
                self.assertEqual(sleeps, [])

    def test_retry_budget_is_validated(self):
        for retries in (-1, 4, True):
            with self.subTest(retries=retries), self.assertRaises(AgentError):
                Client('key', 'model', retries=retries)

    def client(self, retries=3):
        self.sleeps = []
        return Client('key', 'model', retries=retries, sleep=self.sleeps.append)

    def test_retries_rate_limit_and_server_errors_with_backoff(self):
        client = self.client()
        with patch('sse_agent.agent.request.build_opener') as opener:
            opener.return_value.open.side_effect = [failure(429, '5'), failure(503), success()]
            self.assertEqual(client.complete([], [])['content'], 'ok')
        self.assertEqual(self.sleeps, [5.0, 2.0])

    def test_gives_up_after_the_retry_budget(self):
        client = self.client(retries=2)
        with patch('sse_agent.agent.request.build_opener') as opener:
            opener.return_value.open.side_effect = [failure(502)] * 3
            with self.assertRaisesRegex(AgentError, 'HTTP 502') as caught:
                client.complete([], [])
            self.assertEqual(opener.return_value.open.call_count, 3)
        self.assertNotIn('body-not-printed', str(caught.exception))
        self.assertEqual(self.sleeps, [1.0, 2.0])

    def test_client_errors_and_connection_failures_are_not_retried(self):
        for side_effect, pattern in ((failure(400), 'HTTP 400'), (failure(401), 'HTTP 401'),
                                     (URLError('down'), 'conexão'), (TimeoutError(), 'timeout')):
            client = self.client()
            with self.subTest(pattern=pattern), patch('sse_agent.agent.request.build_opener') as opener:
                opener.return_value.open.side_effect = side_effect
                with self.assertRaisesRegex(AgentError, pattern):
                    client.complete([], [])
                self.assertEqual(opener.return_value.open.call_count, 1)
            self.assertEqual(self.sleeps, [])

    def test_retry_delay_is_bounded_and_tolerates_bad_headers(self):
        self.assertEqual(retry_delay(0, '999'), 30.0)
        self.assertEqual(retry_delay(3, None), 8.0)
        self.assertEqual(retry_delay(2, 'Wed, 21 Oct 2026 07:28:00 GMT'), 4.0)
        self.assertEqual(retry_delay(1, '-3'), 2.0)


class ContextTests(unittest.TestCase):
    @staticmethod
    def round_of(index, size):
        call = {'id': str(index), 'type': 'function', 'function': {
            'name': 'write_file', 'arguments': json.dumps({'path': 'f', 'content': 'c' * size,
                                                           'expected_sha256': None})}}
        return [{'role': 'assistant', 'content': None, 'tool_calls': [call]},
                {'role': 'tool', 'tool_call_id': str(index), 'content': json.dumps(
                    {'path': 'f', 'sha256': 'h' * 64, 'content': 'x' * size})}]

    def test_compaction_empties_old_rounds_first_and_protects_the_latest(self):
        messages = [{'role': 'system', 'content': 's'}, {'role': 'user', 'content': 'task'}]
        for index in range(3):
            messages += self.round_of(index, 20_000)
        protected_from = len(messages) - 2
        latest = json.dumps(messages[-1])
        budget = payload_size(messages, []) - 45_000
        compact_history(messages, [], budget, protected_from)
        self.assertLessEqual(payload_size(messages, []), budget)
        self.assertEqual(json.dumps(messages[-1]), latest)
        first = json.loads(messages[3]['content'])
        self.assertIn('omitted', first)
        self.assertEqual(first['sha256'], 'h' * 64)
        self.assertNotIn('content', first)
        self.assertEqual([m['role'] for m in messages], ['system', 'user'] + ['assistant', 'tool'] * 3)
        self.assertEqual(messages[2]['tool_calls'][0]['id'], messages[3]['tool_call_id'])
        json.loads(messages[2]['tool_calls'][0]['function']['arguments'])

    def test_run_keeps_every_request_within_the_payload_limit(self):
        with tempfile.TemporaryDirectory() as directory:
            for name in 'abcd':
                with open(f'{directory}/{name}.txt', 'w') as stream:
                    stream.write(name * 20_000)
            workspace = Workspace(directory)
            sizes = []

            class Reader:
                max_payload = 70_000
                step = 0

                def complete(self, messages, tools):
                    sizes.append(payload_size(messages, tools))
                    if self.step == 4:
                        return {'role': 'assistant', 'content': 'feito'}
                    name = 'abcd'[self.step]
                    self.step += 1
                    return {'role': 'assistant', 'content': None, 'tool_calls': [{
                        'id': str(self.step), 'type': 'function', 'function': {
                            'name': 'read_file', 'arguments': json.dumps({'path': f'{name}.txt'})}}]}

            self.assertEqual(run(Reader(), workspace, 'leia tudo', max_steps=6), 'feito')
        self.assertEqual(len(sizes), 5)
        self.assertLessEqual(max(sizes), Reader.max_payload)


class CliTests(unittest.TestCase):
    def test_parse_checks(self):
        checks = parse_checks(['tests=python -m unittest', 'lint=ruff check .'], ['json=["a b", "c"]'])
        self.assertEqual(checks, {'tests': ['python', '-m', 'unittest'], 'lint': ['ruff', 'check', '.'],
                                  'json': ['a b', 'c']})

    def test_parse_checks_rejects_invalid_definitions(self):
        invalid = [(['noequals'], []), (['=cmd'], []), (['a='], []),
                   (['a=x', 'a=y'], []), (['a=x'], ['a=["y"]']),
                   ([], ['a=not-json']), ([], ['a={"x": 1}']), ([], ['a=[1]']), ([], ['a=[""]'])]
        if sys.platform != 'win32':
            # CommandLineToArgvW (Windows) aceita aspas sem fechamento; só o shlex as recusa.
            invalid.append((['a="unterminated'], []))
        for shell, json_style in invalid:
            with self.subTest(shell=shell, json=json_style), self.assertRaises(AgentError):
                parse_checks(shell, json_style)

    @unittest.skipIf(sys.platform == 'win32', 'Regra do shlex (POSIX).')
    def test_unterminated_quote_is_reported_as_a_clear_error(self):
        with self.assertRaisesRegex(AgentError, 'ilegível'):
            parse_checks(['a="unterminated'], [])

    @unittest.skipUnless(sys.platform == 'win32', 'Semântica do parser nativo Windows.')
    def test_windows_accepts_unterminated_quote_as_one_argument(self):
        self.assertEqual(parse_checks(['a="unterminated'], []), {'a': ['unterminated']})

    def test_cli_retry_is_opt_in_and_passed_to_client(self):
        for option, expected in (([], 0), (['--api-retries', '2'], 2)):
            with self.subTest(option=option), patch('sse_agent.__main__.Client') as client, \
                    patch('sse_agent.__main__.run', return_value='ok'), \
                    contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
                self.assertEqual(main(['tarefa', *option]), 0)
                self.assertEqual(client.call_args.kwargs['retries'], expected)

    def test_version_flag_and_timeouts(self):
        output = io.StringIO()
        with contextlib.redirect_stdout(output), self.assertRaises(SystemExit) as caught:
            main(['--version'])
        self.assertEqual(caught.exception.code, 0)
        self.assertRegex(output.getvalue(), r'sse_agent \d+\.\d+\.\d+')
        self.assertEqual(positive_float('0.5'), 0.5)
        for bad in ('0', '-1', 'nan', 'inf', '-inf'):
            with self.assertRaises(argparse.ArgumentTypeError):
                positive_float(bad)

    def test_main_reports_configuration_errors_without_traceback(self):
        errors = io.StringIO()
        with contextlib.redirect_stderr(errors), patch.dict('os.environ', {}, clear=True):
            self.assertEqual(main(['tarefa']), 1)
        self.assertIn('SSE_API_KEY', errors.getvalue())


if __name__ == '__main__':
    unittest.main()
