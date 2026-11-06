import hashlib
import os
from pathlib import Path
import sys
import tempfile
import tracemalloc
import unittest
from unittest.mock import patch

from sse_agent.tools import Workspace


def sha(data):
    return hashlib.sha256(data).hexdigest()


class ToolsTestCase(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name)
        self.workspace = Workspace(self.root, allow_write=True)

    def write(self, relative, data):
        target = self.root / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data if isinstance(data, bytes) else data.encode('utf-8'))
        return target


class PathPolicyTests(ToolsTestCase):
    def test_nested_artifact_names_are_readable_and_listed(self):
        for name in ('build', 'target', 'dist', 'vendor', 'coverage'):
            self.write(f'src/{name}/module.py', 'x = 1\n')
        files = self.workspace.list_files()['files']
        for name in ('build', 'target', 'dist', 'vendor', 'coverage'):
            self.assertIn(f'src/{name}/module.py', files)
            self.assertEqual(self.workspace.read_file(f'src/{name}/module.py')['content'], 'x = 1\n')
        self.write('packages/web/.next/server.js', 'generated')
        self.assertNotIn('packages/web/.next/server.js', self.workspace.list_files()['files'])
        with self.assertRaises(ValueError):
            self.workspace.read_file('packages/web/.next/server.js')

    def test_root_artifact_directories_cannot_be_enumerated_directly(self):
        for name in ('build', 'target', 'dist', 'vendor', 'coverage'):
            self.write(f'{name}/out.js', 'compiled')
        self.write('app.py', 'x')
        self.assertEqual(self.workspace.list_files()['files'], ['app.py'])
        for name in ('build', 'target', 'dist', 'vendor', 'coverage'):
            with self.subTest(name=name), self.assertRaises(ValueError):
                self.workspace.list_files(directory=name)
            self.assertEqual(self.workspace.read_file(f'{name}/out.js')['content'], 'compiled')

    def test_root_artifact_names_follow_filesystem_case_rules(self):
        self.write('Build/source.py', 'x')
        try:
            case_insensitive = (self.root / 'Build').samefile(self.root / 'build')
        except OSError:
            case_insensitive = False
        assertion = self.assertNotIn if case_insensitive else self.assertIn
        assertion('Build/source.py', self.workspace.list_files()['files'])

    def test_env_lookalikes_and_templates_are_readable_but_secrets_are_not(self):
        for name in ('.environment.md', '.env.example', '.env.sample', '.env.template'):
            self.write(name, 'ok')
            self.assertEqual(self.workspace.read_file(name)['content'], 'ok')
        for name in ('.env', '.envrc', '.env.production', '.env.local'):
            self.write(name, 'secret')
            with self.subTest(name=name), self.assertRaises(ValueError):
                self.workspace.read_file(name)
            self.assertNotIn(name, self.workspace.list_files()['files'])

    def test_dependency_and_secret_directories_stay_blocked(self):
        for name in ('node_modules/pkg/index.js', '.venv/lib/x.py', '.git/config', '.ssh/id_rsa'):
            self.write(name, 'x')
            with self.subTest(name=name), self.assertRaises(ValueError):
                self.workspace.read_file(name)
        self.write('GIT~1/config', 'x')
        with self.assertRaises(ValueError):
            self.workspace.read_file('GIT~1/config')

    def test_filesystem_and_home_roots_are_rejected(self):
        with self.assertRaisesRegex(ValueError, 'project directory'):
            Workspace(Path(self.root.anchor))
        with self.assertRaisesRegex(ValueError, 'project directory'):
            Workspace(Path.home())

    def test_common_credential_names_and_secret_content_are_blocked(self):
        names = ('auth.json', '.config/gh/hosts.yml', '.cargo/credentials.toml', '.pgpass',
                 '.my.cnf', '.vault-token', 'service-account.json', 'client_secret.json',
                 'token.json', 'terminal_history', 'private.ppk', 'store.kdbx')
        for name in names:
            self.write(name, 'synthetic')
            with self.subTest(name=name), self.assertRaises(ValueError):
                self.workspace.read_file(name)
        self.write('ordinary.txt', 'ghp_' + 'A' * 32)
        with self.assertRaisesRegex(ValueError, 'resembles a credential'):
            self.workspace.read_file('ordinary.txt')

    @unittest.skipUnless(hasattr(os, 'link'), 'Hardlinks are unavailable.')
    def test_hardlinked_files_are_not_read_or_listed(self):
        outside = self.write('source.txt', 'outside')
        linked = self.root / 'linked.txt'
        os.link(outside, linked)
        with self.assertRaises(ValueError):
            self.workspace.read_file('linked.txt')
        self.assertNotIn('linked.txt', self.workspace.list_files()['files'])


class ReadAndSearchTests(ToolsTestCase):
    def test_line_range_returns_slice_with_whole_file_hash(self):
        content = ''.join(f'line {number}\n' for number in range(1, 6))
        self.write('a.txt', content)
        result = self.workspace.read_file('a.txt', start_line=2, end_line=3)
        self.assertEqual(result['content'], 'line 2\nline 3\n')
        self.assertEqual((result['start_line'], result['end_line'], result['total_lines']), (2, 3, 5))
        self.assertEqual(result['sha256'], sha(content.encode()))
        self.assertFalse(result['truncated'])
        self.assertEqual(self.workspace.read_file('a.txt', start_line=4)['content'], 'line 4\nline 5\n')

    def test_invalid_ranges_are_rejected(self):
        self.write('a.txt', 'one\ntwo\n')
        for kwargs in ({'start_line': 0}, {'start_line': 3, 'end_line': 2}, {'start_line': 9},
                       {'start_line': True}, {'end_line': 'x'}):
            with self.subTest(kwargs=kwargs), self.assertRaises(ValueError):
                self.workspace.read_file('a.txt', **kwargs)

    def test_empty_file_range_is_well_defined(self):
        self.write('empty.txt', b'')
        result = self.workspace.read_file('empty.txt', start_line=1)
        self.assertEqual((result['content'], result['start_line'], result['end_line'], result['total_lines']),
                         ('', 1, 0, 0))
        with self.assertRaisesRegex(ValueError, 'past the end'):
            self.workspace.read_file('empty.txt', start_line=2, end_line=2)

    def test_large_file_requires_a_range_and_is_cut_on_a_line_boundary(self):
        content = ''.join(f'{number:05d} ' + 'x' * 90 + '\n' for number in range(1, 1501))  # ~136 KB
        self.write('big.txt', content)
        with self.assertRaisesRegex(ValueError, 'start_line'):
            self.workspace.read_file('big.txt')
        result = self.workspace.read_file('big.txt', start_line=1)
        self.assertTrue(result['truncated'])
        self.assertTrue(result['content'].endswith('\n'))
        self.assertLessEqual(len(result['content'].encode()), 64_000)
        self.assertEqual(result['total_lines'], 1500)
        self.assertEqual(result['sha256'], sha(content.encode()))
        self.assertEqual(result['content'].count('\n'), result['end_line'])

    def test_list_files_pattern(self):
        for name in ('a.py', 'pkg/b.py', 'pkg/c.txt'):
            self.write(name, 'x')
        self.assertEqual(self.workspace.list_files('*.py')['files'], ['a.py', 'pkg/b.py'])
        self.assertEqual(self.workspace.list_files('pkg/*')['files'], ['pkg/b.py', 'pkg/c.txt'])

    def test_search_text(self):
        self.write('a.py', 'alpha\nBeta\r\ngamma beta\n')
        self.write('b.txt', 'beta again\n')
        self.write('.env', 'beta-secret\n')
        self.write('bin.dat', b'beta\x00\x01')
        result = self.workspace.search_text('beta')
        self.assertEqual([(m['path'], m['line']) for m in result['matches']],
                         [('a.py', 3), ('b.txt', 1)])
        insensitive = self.workspace.search_text('beta', ignore_case=True, pattern='*.py')
        self.assertEqual([(m['path'], m['line'], m['text']) for m in insensitive['matches']],
                         [('a.py', 2, 'Beta'), ('a.py', 3, 'gamma beta')])
        limited = self.workspace.search_text('beta', ignore_case=True, max_results=1)
        self.assertEqual(len(limited['matches']), 1)
        self.assertTrue(limited['truncated'])
        for bad in ('', None, 3):
            with self.assertRaises(ValueError):
                self.workspace.search_text(bad)

    @unittest.skipUnless(hasattr(os, 'mkfifo'), 'FIFO files are POSIX-specific.')
    def test_search_ignores_fifo_without_opening_it(self):
        os.mkfifo(self.root / 'pipe')
        self.write('regular.txt', 'needle')
        self.assertEqual(self.workspace.search_text('needle')['matches'][0]['path'], 'regular.txt')
        self.assertNotIn('pipe', self.workspace.list_files()['files'])

    def test_search_enforces_result_and_byte_budgets(self):
        for index in range(205):
            self.write(f'f{index:03}.txt', 'needle\n')
        result = self.workspace.search_text('needle', max_results=10_000)
        self.assertEqual(len(result['matches']), 200)
        self.assertTrue(result['truncated'])
        with patch('sse_agent.tools.MAX_SEARCH_BYTES', 1):
            self.assertTrue(self.workspace.search_text('needle')['truncated'])


class EditTests(ToolsTestCase):
    def test_expansion_is_rejected_before_large_allocation(self):
        target = self.write('a.txt', 'a' * 20_000)
        digest = self.workspace.read_file('a.txt')['sha256']
        tracemalloc.start()
        try:
            with self.assertRaisesRegex(ValueError, 'Result exceeds'):
                self.workspace.replace_in_file('a.txt', 'a', 'b' * 500, digest, replace_all=True)
            _, peak = tracemalloc.get_traced_memory()
        finally:
            tracemalloc.stop()
        # Reading uses a buffer of at most 2 MB. It must not allocate the 10 MB result
        # or its encoded copy, which previously added up to about 20 MB.
        self.assertLess(peak, 4_000_000)
        self.assertEqual(target.read_bytes(), b'a' * 20_000)

    def test_expansion_limit_counts_utf8_bytes_and_crlf(self):
        cases = [(b'x' * 1000, 'x', 'λ' * 1001),
                 (b'x\r\n' * 1000, 'x\n', 'λ' * 1000 + '\n')]
        for current, old, new in cases:
            target = self.write('a.txt', current)
            digest = sha(current)
            with self.subTest(old=old), self.assertRaisesRegex(ValueError, 'Result exceeds'):
                self.workspace.replace_in_file('a.txt', old, new, digest, replace_all=True)
            self.assertEqual(target.read_bytes(), current)

    def test_unique_replacement_accepts_unicode_result(self):
        self.write('a.txt', 'a' * 20_000)
        digest = self.workspace.read_file('a.txt')['sha256']
        result = self.workspace.replace_in_file('a.txt', 'a' * 20_000, 'λ' * 100, digest)
        self.assertEqual(result['sha256'], sha(('λ' * 100).encode()))

    def test_replace_in_file_unique_match(self):
        self.write('a.py', 'a = 1\nb = 2\n')
        original = self.workspace.read_file('a.py')
        result = self.workspace.replace_in_file('a.py', 'b = 2', 'b = 3', original['sha256'])
        self.assertEqual((self.root / 'a.py').read_text(), 'a = 1\nb = 3\n')
        self.assertEqual(result['sha256'], sha(b'a = 1\nb = 3\n'))
        self.assertEqual(self.workspace.read_file('a.py')['sha256'], result['sha256'])

    def test_replace_in_file_rejects_stale_missing_and_ambiguous(self):
        self.write('a.py', 'x\nx\n')
        digest = self.workspace.read_file('a.py')['sha256']
        with self.assertRaisesRegex(ValueError, '2 times'):
            self.workspace.replace_in_file('a.py', 'x', 'y', digest)
        with self.assertRaisesRegex(ValueError, 'not found'):
            self.workspace.replace_in_file('a.py', 'z', 'y', digest)
        with self.assertRaisesRegex(ValueError, 'changed'):
            self.workspace.replace_in_file('a.py', 'x', 'y', 'f' * 64)
        with self.assertRaises(ValueError):
            self.workspace.replace_in_file('a.py', '', 'y', digest)
        self.assertEqual((self.root / 'a.py').read_text(), 'x\nx\n')
        result = self.workspace.replace_in_file('a.py', 'x', 'y', digest, replace_all=True)
        self.assertEqual(result['replacements'], 2)
        self.assertEqual((self.root / 'a.py').read_text(), 'y\ny\n')

    def test_replace_rechecks_hash_immediately_before_atomic_write(self):
        target = self.write('race.txt', 'old')
        digest = self.workspace.read_file('race.txt')['sha256']
        original_load = self.workspace._load
        calls = 0

        def raced_load(path):
            nonlocal calls
            calls += 1
            if calls == 2:
                target.write_text('concurrent', encoding='utf-8')
            return original_load(path)

        with patch.object(self.workspace, '_load', side_effect=raced_load), \
                self.assertRaisesRegex(ValueError, 'during the write'):
            self.workspace.replace_in_file('race.txt', 'old', 'new', digest)
        self.assertEqual(target.read_text(encoding='utf-8'), 'concurrent')

    def test_replace_all_requires_a_boolean(self):
        self.write('a.py', 'x\n')
        digest = self.workspace.read_file('a.py')['sha256']
        for value in (1, 'true', None):
            with self.subTest(value=value), self.assertRaisesRegex(ValueError, 'boolean'):
                self.workspace.replace_in_file('a.py', 'x', 'y', digest, replace_all=value)

    def test_replace_in_file_preserves_crlf_and_mode(self):
        target = self.write('a.txt', b'one\r\ntwo\r\nthree\r\n')
        if os.name != 'nt':
            target.chmod(0o755)
        digest = self.workspace.read_file('a.txt')['sha256']
        self.workspace.replace_in_file('a.txt', 'two\nthree', 'TWO\nTHREE\nFOUR', digest)
        self.assertEqual(target.read_bytes(), b'one\r\nTWO\r\nTHREE\r\nFOUR\r\n')
        if os.name != 'nt':
            self.assertEqual(target.stat().st_mode & 0o777, 0o755)

    def test_replace_in_file_works_on_files_above_the_read_limit(self):
        content = ''.join(f'line {number}\n' for number in range(20_000))  # > 64 KB
        self.write('big.txt', content)
        digest = self.workspace.read_file('big.txt', start_line=1, end_line=1)['sha256']
        self.workspace.replace_in_file('big.txt', 'line 19999\n', 'last\n', digest)
        self.assertTrue((self.root / 'big.txt').read_text().endswith('last\n'))

    def test_write_file_preserves_existing_crlf(self):
        target = self.write('a.txt', b'one\r\ntwo\r\n')
        digest = self.workspace.read_file('a.txt')['sha256']
        self.workspace.write_file('a.txt', 'uno\ndos\n', digest)
        self.assertEqual(target.read_bytes(), b'uno\r\ndos\r\n')

    def test_write_file_preserves_utf8_bom(self):
        target = self.write('windows.ps1.txt', b'\xef\xbb\xbfWrite-Host "old"\r\n')
        digest = self.workspace.read_file('windows.ps1.txt')['sha256']
        self.workspace.write_file('windows.ps1.txt', 'Write-Host "new"\n', digest)
        self.assertEqual(target.read_bytes(), b'\xef\xbb\xbfWrite-Host "new"\r\n')

    def test_execution_surfaces_require_separate_authorization(self):
        for name in ('conftest.py', 'Makefile', '.github/workflows/ci.yml',
                     '.vscode/tasks.json', 'scripts/build.ps1'):
            target = self.root / name
            target.parent.mkdir(parents=True, exist_ok=True)
            result = self.workspace.execute('write_file', {'path': name, 'content': 'x',
                                                            'expected_sha256': None})
            self.assertIn('allow-executable-write', result['error'])
            self.assertFalse(target.exists())
        opted_in = Workspace(self.root, allow_write=True, allow_executable_write=True)
        self.assertTrue(opted_in.write_file('conftest.py', 'x', None)['written'])

    def test_write_file_rejects_content_that_exceeds_limit_after_crlf_conversion(self):
        target = self.write('a.txt', b'one\r\n')
        digest = self.workspace.read_file('a.txt')['sha256']
        content = 'x\n' * 32_000
        with self.assertRaisesRegex(ValueError, 'after CRLF conversion'):
            self.workspace.write_file('a.txt', content, digest)
        self.assertEqual(target.read_bytes(), b'one\r\n')

    def test_write_tools_are_absent_and_denied_in_read_only_mode(self):
        self.write('a.txt', 'x')
        read_only = Workspace(self.root)
        names = {item['function']['name'] for item in read_only.definitions()}
        self.assertEqual(names, {'list_files', 'search_text', 'read_file'})
        result = read_only.execute('replace_in_file', {'path': 'a.txt', 'old': 'x', 'new': 'y',
                                                       'expected_sha256': 'a' * 64})
        self.assertIn('error', result)
        self.assertEqual((self.root / 'a.txt').read_text(), 'x')

    def test_unexpected_tool_failure_becomes_an_error_result(self):
        with patch.object(Workspace, 'list_files', side_effect=RuntimeError('boom')):
            result = self.workspace.execute('list_files', {})
        self.assertIn('error', result)
        self.assertNotIn('boom', result['error'])
        self.assertIn('error', self.workspace.execute('read_file', {'unexpected': 1}))

    def test_os_errors_do_not_disclose_host_paths(self):
        with patch.object(Workspace, 'list_files', side_effect=OSError('/private/user/path')):
            result = self.workspace.execute('list_files', {})
        self.assertEqual(result, {'error': 'The file operation failed.'})


class CheckTests(ToolsTestCase):
    def test_checks_are_hidden_during_writes_without_separate_authorization(self):
        command = [sys.executable, '-c', 'print("ok")']
        blocked = Workspace(self.root, allow_write=True, checks={'tests': command})
        self.assertNotIn('run_check', {item['function']['name'] for item in blocked.definitions()})
        self.assertIn('error', blocked.execute('run_check', {'name': 'tests'}))
        allowed = Workspace(self.root, allow_write=True, checks={'tests': command},
                            allow_check_after_write=True)
        self.assertIn('run_check', {item['function']['name'] for item in allowed.definitions()})

    def test_output_keeps_the_tail_where_failures_usually_are(self):
        code = 'print("A" * 20000); print("FAIL: assertion at the end")'
        workspace = Workspace(self.root, checks={'noisy': [sys.executable, '-c', code]})
        result = workspace.run_check('noisy')
        self.assertTrue(result['truncated'])
        self.assertIn('FAIL: assertion at the end', result['output'])
        self.assertIn('omitted', result['output'])
        self.assertLess(len(result['output']), 16_200)

    def test_environment_is_an_allowlist(self):
        code = ('import os; print(",".join(sorted(k for k in os.environ if k in '
                '("GITHUB_TOKEN","AWS_SECRET_ACCESS_KEY","SSE_API_KEY","MY_FLAG","PATH"))))')
        variables = {'GITHUB_TOKEN': 't', 'AWS_SECRET_ACCESS_KEY': 's', 'SSE_API_KEY': 'k', 'MY_FLAG': '1'}
        with patch.dict(os.environ, variables):
            default = Workspace(self.root, checks={'env': [sys.executable, '-c', code]}).run_check('env')
            opted_in = Workspace(self.root, checks={'env': [sys.executable, '-c', code]},
                                 pass_env=['my_flag', 'SSE_API_KEY']).run_check('env')
        self.assertEqual(default['output'].strip(), 'PATH')
        self.assertEqual(opted_in['output'].strip(), 'MY_FLAG,PATH')


if __name__ == '__main__':
    unittest.main()
