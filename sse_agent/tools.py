"""Tools restricted to the workspace selected by the operator."""

from collections.abc import Iterator, Sequence
from fnmatch import fnmatchcase
import hashlib
import os
from pathlib import Path, PureWindowsPath
import re
import stat
import subprocess
import sys
import tempfile
import time
from typing import Any

from .overview import build_overview
from .paths import matches_pattern
from .platforms import process_options, stop_process_tree
from .references import REFERENCE_NAMES, reference_text
from .sensitive import contains_sensitive_content, redact_sensitive_text
from .surfaces import executable_content, execution_surface

MAX_FILE_BYTES = 64_000          # text returned or written by one call
MAX_EDIT_BYTES = 2_000_000       # largest file that can be ranged, searched, or edited
MAX_SCANNED_FILES = 10_000
MAX_LISTED_FILES = 1000
MAX_SEARCH_RESULTS = 200
MAX_SEARCH_BYTES = 32_000_000
MAX_SEARCH_SECONDS = 5.0
MAX_LOG_TAIL = 2000
OUTPUT_LIMIT = 16_000
OUTPUT_HEAD = 2_000

WINDOWS = sys.platform == 'win32'
# File names that read_log accepts: debug.log, error_log, access.log.1, npm-debug.log, logs/...
LOG_NAME = re.compile(r'(?:^|[._-])logs?(?:[._-]|$)', re.IGNORECASE)
LOG_SUFFIXES = ('.out', '.err', '.trace', '.jsonl', '.ndjson')
# Credential directories: never accessible.
SECRET_DIRS = {'.git', '.aws', '.ssh', '.kube', '.gnupg', '.docker', '.azure', '.terraform.d'}
# Dependencies and caches: never accessible at any depth.
DEPENDENCY_DIRS = {'.venv', 'venv', 'node_modules', '__pycache__', '.pytest_cache',
                   '.mypy_cache', '.ruff_cache', '.next'}
# Common generated/dependency directory names are hidden only at the workspace root.
# Nested source packages may legitimately use these domain terms.
ARTIFACT_DIRS = {'dist', 'build', 'target', 'vendor', 'coverage'}
ENV_TEMPLATES = ('.env.example', '.env.sample', '.env.template')
SECRET_FILES = {'credentials', 'credentials.json', 'secrets.json', 'id_rsa', 'id_ed25519',
                'id_ecdsa', 'id_dsa', '.npmrc', '.netrc', '.pypirc', '.git-credentials',
                '.htpasswd', 'wp-config.php', 'secrets.yaml', 'secrets.yml', 'auth.json',
                '.yarnrc.yml', '.pgpass', '.my.cnf', '.vault-token', 'kubeconfig',
                'service-account.json', 'application_default_credentials.json',
                'client_secret.json', 'token.json', '.dockercfg', '.s3cfg', '.boto',
                '.gitconfig', 'credentials.yml', 'credentials.yaml', 'local_settings.py',
                'settings.local.php', 'appsettings.production.json', 'wp-config-local.php',
                'localsettings.php', '.terraformrc', 'terraform.rc', 'sftp-config.json',
                'parameters.yml', 'config.inc.php', 'secrets.toml', '.secrets', 'credentials.toml'}
SECRET_NAME_PATTERNS = ('service-account*.json', 'client_secret*.json', '*.secret', '*.secrets',
                        'id_rsa*', 'id_ed25519*', 'id_ecdsa*', 'id_dsa*')
# Paths matched at any depth, component by component.
SECRET_RELATIVE_PATHS = {'.config/gh/hosts.yml', '.cargo/credentials.toml', '.cargo/credentials',
                         '.config/rclone/rclone.conf', 'app/etc/env.php',
                         'sites/default/settings.php', 'sites/default/settings.local.php'}
SECRET_RELATIVE_DIRS = {'.config/gcloud', '.config/gh', '.config/doctl', '.config/hub'}
# Workspaces must be project directories: these exact paths (and virtual trees) are refused.
FORBIDDEN_ROOTS = {'/etc', '/usr', '/var', '/boot', '/bin', '/sbin', '/lib', '/lib32', '/lib64',
                   '/opt', '/srv', '/mnt', '/media', '/run', '/tmp', '/home', '/root', '/users',
                   '/library', '/system', '/applications', '/private', '/var/tmp', '/var/log',
                   '/var/lib', '/var/spool', '/var/mail', '/private/etc', '/private/var',
                   '/private/tmp', '/private/var/tmp'}  # macOS resolves /etc, /var, /tmp here
FORBIDDEN_TREES = ('/proc', '/sys', '/dev')

# Environment variables passed to checks (uppercase names; LC_* is also allowed).
CHECK_ENV_ALLOWLIST = {
    'PATH', 'PATHEXT', 'HOME', 'USERPROFILE', 'USER', 'USERNAME', 'LOGNAME', 'LANG',
    'LANGUAGE', 'TERM', 'TZ', 'TMP', 'TEMP', 'TMPDIR', 'SYSTEMROOT', 'SYSTEMDRIVE',
    'WINDIR', 'COMSPEC', 'APPDATA', 'LOCALAPPDATA', 'PROGRAMDATA', 'PROGRAMFILES',
    'PROGRAMFILES(X86)', 'PROGRAMW6432', 'NUMBER_OF_PROCESSORS', 'PROCESSOR_ARCHITECTURE',
    'OS', 'VIRTUAL_ENV'}
NEVER_PASSED = {'SSE_API_KEY', 'OPENAI_API_KEY'}


def protected(part: str) -> bool:
    """Return whether a path component is never read, written, or listed."""
    lower = part.lower()
    if lower in SECRET_DIRS or lower in DEPENDENCY_DIRS or lower in SECRET_FILES:
        return True
    if lower == '.envrc' or lower == '.env' or lower.startswith('.env.'):
        return lower not in ENV_TEMPLATES
    if WINDOWS and re.fullmatch(r'[^~]{1,6}~[0-9](?:\..*)?', part, re.IGNORECASE):
        return True  # reject possible Windows 8.3 aliases such as GIT~1
    if not lower.endswith('.pub') and any(fnmatchcase(lower, pattern) for pattern in SECRET_NAME_PATTERNS):
        return True
    return lower.endswith(('.pem', '.key', '.p8', '.ppk', '.p12', '.pfx', '.jks', '.keystore',
                           '.kdbx', '.env', '.tfstate', '.tfvars', '_history')) or (
        '.tfstate.' in lower or lower.endswith('.tfvars.json'))


def protected_path(parts: Sequence[str]) -> bool:
    padded = '/' + '/'.join(parts).casefold() + '/'
    return (any(padded.endswith(f'/{path}/') for path in SECRET_RELATIVE_PATHS) or
            any(f'/{directory}/' in padded for directory in SECRET_RELATIVE_DIRS) or
            any(protected(part) for part in parts))


def unsafe_root(root: Path, home: Path | None) -> str | None:
    """Explain why a path must not be used as a workspace, or return None."""
    posix = root.as_posix().casefold().rstrip('/')
    if root == Path(root.anchor):
        return 'a filesystem root'
    if posix in FORBIDDEN_ROOTS or any(posix == tree or posix.startswith(tree + '/')
                                       for tree in FORBIDDEN_TREES):
        return 'a system directory'
    if WINDOWS:
        drive = root.anchor.replace('\\', '/').casefold()
        forbidden = {drive + name for name in ('users', 'windows', 'program files',
                                               'program files (x86)', 'programdata')}
        for variable in ('SystemRoot', 'ProgramFiles', 'ProgramFiles(x86)', 'ProgramData'):
            if os.environ.get(variable):
                forbidden.add(Path(os.environ[variable]).as_posix().casefold().rstrip('/'))
        if posix in forbidden:
            return 'a system directory'
    if home is not None and (root == home or home.is_relative_to(root)):
        return 'a home directory or one of its parents'
    if any(part.casefold() in SECRET_DIRS | DEPENDENCY_DIRS for part in root.parts):
        return 'inside a protected directory'
    return None


def artifact_name(name: str, parent: Path) -> bool:
    """Match generated root directories using host filesystem case rules."""
    if name in ARTIFACT_DIRS:
        return True
    canonical = name.casefold()
    if canonical not in ARTIFACT_DIRS:
        return False
    try:
        return (parent / name).samefile(parent / canonical)
    except OSError:
        return False


def linked(path: Path) -> bool:
    try:
        info = path.lstat()
    except FileNotFoundError:
        return False
    return stat.S_ISLNK(info.st_mode) or bool(
        getattr(info, 'st_file_attributes', 0) & getattr(stat, 'FILE_ATTRIBUTE_REPARSE_POINT', 0x400))


def check_environment(extra: Sequence[str] = ()) -> dict[str, str]:
    """Build the minimal check environment; extra variables require operator opt-in."""
    allowed = (CHECK_ENV_ALLOWLIST | {name.upper() for name in extra}) - NEVER_PASSED
    environment = {key: value for key, value in os.environ.items()
                   if key.upper() in allowed or
                   (key.upper().startswith('LC_') and key.upper() not in NEVER_PASSED)}
    environment['PYTHONIOENCODING'] = 'utf-8'
    return environment


def split_lines(text: str) -> list[str]:
    """Split lines while preserving terminators; only \\n delimits a line."""
    parts = text.split('\n')
    lines = [part + '\n' for part in parts[:-1]]
    if parts[-1]:
        lines.append(parts[-1])
    return lines


def uses_crlf(data: bytes) -> bool:
    crlf = data.count(b'\r\n')
    return crlf > 0 and crlf > data.count(b'\n') - crlf


def log_like(relative: str) -> bool:
    """Return whether a path looks like a log file or lives under a logs directory."""
    parts = relative.casefold().split('/')
    name = parts[-1]
    return bool(LOG_NAME.search(name) or name.endswith(LOG_SUFFIXES) or
                any(part in {'log', 'logs'} for part in parts[:-1]))


def schema(name: str, description: str, properties: dict[str, Any],
           required: list[str]) -> dict[str, Any]:
    return {'type': 'function', 'function': {
        'name': name, 'description': description,
        'parameters': {'type': 'object', 'properties': properties,
                       'required': required, 'additionalProperties': False}}}


def integer_argument(value: Any, name: str, minimum: int = 1) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < minimum:
        raise ValueError(f'{name} must be an integer >= {minimum}.')
    return value


class Workspace:
    def __init__(self, root: str | Path, allow_write: bool = False,
                 checks: dict[str, list[str]] | None = None, timeout: float = 60,
                 pass_env: Sequence[str] = (), deny: Sequence[str] = (),
                 allow_files: Sequence[str] = (), allow_executable_write: bool = False,
                 allow_check_after_write: bool = False) -> None:
        requested = Path(os.path.abspath(root))  # as spelled: symlinks such as /etc stay visible
        self.root = Path(root).resolve(strict=True)
        if not self.root.is_dir():
            raise ValueError('The workspace must be a directory.')
        try:
            home = Path.home().resolve()
        except (OSError, RuntimeError):
            home = None
        reason = unsafe_root(requested, home) or unsafe_root(self.root, home)
        if reason:
            raise ValueError(f'Choose a project directory, not {reason}.')
        self.allow_write = allow_write
        self.allow_executable_write = allow_executable_write
        self.allow_check_after_write = allow_check_after_write
        self.checks = checks or {}
        self.timeout = timeout
        self.pass_env = tuple(pass_env)
        self.deny = tuple(deny)
        self.allow_files = tuple(allow_files)
        if any(not isinstance(pattern, str) or not pattern for pattern in (*self.deny, *self.allow_files)):
            raise ValueError('Access patterns must be non-empty strings.')
        if any(not [part for part in pattern.replace('\\', '/').split('/') if part and part != '.']
               for pattern in (*self.deny, *self.allow_files)):
            raise ValueError('Access patterns must contain a path or glob component.')

    @property
    def checks_visible(self) -> bool:
        """Checks are hidden during write sessions unless explicitly authorized."""
        return not self.allow_write or self.allow_check_after_write

    def denied(self, relative: str) -> bool:
        return any(matches_pattern(relative.casefold(), pattern.casefold()) for pattern in self.deny)

    def allowed_file(self, relative: str) -> bool:
        return not self.allow_files or any(matches_pattern(relative.casefold(), pattern.casefold())
                                           for pattern in self.allow_files)

    # ------------------------------------------------------------------ paths

    def path(self, relative: Any, directory: bool = False) -> Path:
        if not isinstance(relative, str) or not relative or '\x00' in relative:
            raise ValueError('Invalid relative path.')
        path = Path(relative.replace('\\', '/'))
        reserved = {'CON', 'PRN', 'AUX', 'NUL', 'CONIN$', 'CONOUT$'} | {
            prefix + number for prefix in ('COM', 'LPT') for number in '123456789¹²³'}
        if (path.is_absolute() or PureWindowsPath(relative).anchor or protected_path(path.parts) or
                any(part == '..' or ':' in part or
                    part.endswith((' ', '.')) or part.split('.')[0].upper() in reserved
                    for part in path.parts)):
            raise ValueError('Path is outside the allowed scope or is protected.')
        candidate = self.root
        for part in path.parts:
            candidate = candidate / part
            if self.denied(candidate.relative_to(self.root).as_posix()):
                raise ValueError('Path denied by the operator.')
            if linked(candidate):
                raise ValueError('Symbolic links and reparse points are not allowed by file tools.')
        if not candidate.resolve().is_relative_to(self.root):
            raise ValueError('Path is outside the workspace.')
        if not directory and not self.allowed_file(candidate.relative_to(self.root).as_posix()):
            raise ValueError('File is outside the operator allowlist.')
        return candidate

    def definitions(self) -> list[dict[str, Any]]:
        definitions = [
            schema('list_files', 'List visible files (up to 1000). Optional pattern '
                   '(glob, e.g. "*.py" or "src/**/*.ts") may be relative to the workspace '
                   'or to directory.',
                   {'pattern': {'type': 'string'}, 'directory': {'type': 'string'}}, []),
            schema('search_text', 'Search files for literal text (like grep -F). '
                   'Returns the path, line, and excerpt, plus skipped: the number of matching files '
                   'that could not be searched (binary, oversized, or credential-like). '
                   'pattern may be relative to the workspace or to directory. '
                   'Use before reading whole files.',
                   {'query': {'type': 'string'}, 'pattern': {'type': 'string'},
                    'directory': {'type': 'string'},
                    'ignore_case': {'type': 'boolean'},
                    'max_results': {'type': 'integer', 'minimum': 1, 'maximum': MAX_SEARCH_RESULTS}},
                   ['query']),
            schema('read_file', 'Read a UTF-8 file and get its full-file SHA-256 before editing. '
                   'Files larger than 64000 bytes require start_line/end_line '
                   '(1-indexed, inclusive); the response includes total_lines.',
                   {'path': {'type': 'string'}, 'start_line': {'type': 'integer', 'minimum': 1},
                    'end_line': {'type': 'integer', 'minimum': 1}}, ['path']),
            schema('project_overview', 'Inventory the workspace without running anything: languages, '
                   'manifests, lockfiles, runtime pins, test and CI configuration, instruction files '
                   '(nearest scope last), and candidate commands inferred from files. Candidates are '
                   'not verified; partial is true when the scan limit was reached. Call it first.',
                   {}, []),
            schema('read_log', 'Read the end of a log file with credential-like content redacted. '
                   'For log-like names only (debug.log, error_log, logs/...). Returns the last '
                   'tail_lines lines (default 200) or a start_line/end_line range of the redacted '
                   'view; no hash is returned and the file cannot be edited through it.',
                   {'path': {'type': 'string'},
                    'tail_lines': {'type': 'integer', 'minimum': 1, 'maximum': MAX_LOG_TAIL},
                    'start_line': {'type': 'integer', 'minimum': 1},
                    'end_line': {'type': 'integer', 'minimum': 1}}, ['path']),
            schema('read_reference', 'Read one skill reference document: guidance on ecosystems, '
                   'debugging, audits, agent diagnosis, knowledge, API currency, or documentation '
                   'sources. These are not project files.',
                   {'name': {'type': 'string', 'enum': list(REFERENCE_NAMES)}}, ['name']),
        ]
        if self.allow_write:
            definitions.append(schema(
                'replace_in_file', 'Replace an exact string in an existing file. Prefer this over '
                'write_file for focused changes. Requires the SHA-256 returned by read_file; fails '
                'if old is missing or not unique (unless replace_all is true). Preserves CRLF.',
                {'path': {'type': 'string'}, 'old': {'type': 'string'}, 'new': {'type': 'string'},
                 'expected_sha256': {'type': 'string'}, 'replace_all': {'type': 'boolean'}},
                ['path', 'old', 'new', 'expected_sha256']))
            definitions.append(schema(
                'write_file', 'Write UTF-8 (up to 64000 bytes). For an existing file, pass the '
                'SHA-256 returned by read_file; for a new file, pass null. Preserves existing '
                'CRLF line endings. Does not delete files.',
                {'path': {'type': 'string'}, 'content': {'type': 'string'},
                 'expected_sha256': {'type': ['string', 'null']}},
                ['path', 'content', 'expected_sha256']))
        if self.checks and self.checks_visible:
            definitions.append(schema(
                'run_check', 'Run a check defined by the operator. Names: ' +
                ', '.join(self.checks),
                {'name': {'type': 'string', 'enum': list(self.checks)}}, ['name']))
        return definitions

    # ------------------------------------------------------------------ reads

    def _walk(self, directory: str = '.') -> Iterator[str | None]:
        """Yield readable relative paths; None signals that the scan limit was reached."""
        scanned = 0
        start = self.path(directory, directory=True)
        if not start.is_dir():
            raise ValueError('Search directory not found.')
        start_relative = start.relative_to(self.root)
        if start_relative.parts and artifact_name(start_relative.parts[0], self.root):
            raise ValueError('Root artifact directories cannot be enumerated.')
        for base, dirs, files in os.walk(start, followlinks=False):
            at_root = Path(base) == self.root
            dirs[:] = sorted(d for d in dirs if not protected_path(
                                 (Path(base) / d).relative_to(self.root).parts) and
                             not (at_root and artifact_name(d, self.root)) and
                             not self.denied((Path(base) / d).relative_to(self.root).as_posix()) and
                             not linked(Path(base) / d))
            for name in sorted(files):
                scanned += 1
                if scanned > MAX_SCANNED_FILES:
                    yield None
                    return
                relative = (Path(base) / name).relative_to(self.root).as_posix()
                candidate = Path(base) / name
                try:
                    info = candidate.lstat()
                    regular_unlinked = stat.S_ISREG(info.st_mode) and info.st_nlink == 1
                except OSError:
                    regular_unlinked = False
                if (not regular_unlinked or protected_path(Path(relative).parts) or linked(candidate) or
                        self.denied(relative) or
                        not self.allowed_file(relative)):
                    continue
                yield (Path(base) / name).relative_to(self.root).as_posix()

    def list_files(self, pattern: str | None = None, directory: str = '.') -> dict[str, Any]:
        if pattern is not None and not isinstance(pattern, str):
            raise ValueError('pattern must be a string.')
        found: list[str] = []
        start = self.path(directory, directory=True)
        for relative in self._walk(directory):
            if relative is None:
                return {'files': found, 'truncated': True}
            scoped = Path(relative).relative_to(start.relative_to(self.root)).as_posix()
            if not (matches_pattern(relative, pattern) or matches_pattern(scoped, pattern)):
                continue
            found.append(relative)
            if len(found) >= MAX_LISTED_FILES:
                return {'files': found, 'truncated': True}
        return {'files': found, 'truncated': False}

    def _open_regular(self, target: Path) -> int:
        """Open a validated path non-blocking and return a descriptor for a regular, single-link file."""
        if target.is_dir():  # os.open() on a directory succeeds on POSIX but raises on Windows
            raise ValueError('Refused: only regular files with a single link can be accessed.')
        try:
            # O_NONBLOCK keeps a FIFO from blocking open(); the regular-file check follows.
            flags = (os.O_RDONLY | getattr(os, 'O_BINARY', 0) | getattr(os, 'O_NOFOLLOW', 0) |
                     getattr(os, 'O_NONBLOCK', 0))
            descriptor = os.open(target, flags)
        except FileNotFoundError:
            raise ValueError('File not found.') from None
        except OSError:
            raise ValueError('The file could not be opened.') from None
        try:
            info = os.fstat(descriptor)
            if not stat.S_ISREG(info.st_mode) or info.st_nlink != 1:
                raise ValueError('Refused: only regular files with a single link can be accessed.')
        except BaseException:
            os.close(descriptor)
            raise
        return descriptor

    def _load(self, relative: str) -> tuple[Path, bytes]:
        target = self.path(relative)
        with os.fdopen(self._open_regular(target), 'rb') as stream:
            data = stream.read(MAX_EDIT_BYTES + 1)
        if len(data) > MAX_EDIT_BYTES:
            raise ValueError(f'File exceeds the {MAX_EDIT_BYTES}-byte limit.')
        if contains_sensitive_content(data):
            raise ValueError('File content resembles a credential and cannot be read or edited.')
        return target, data

    def read_file(self, path: str, start_line: int | None = None,
                  end_line: int | None = None) -> dict[str, Any]:
        _, data = self._load(path)
        digest = hashlib.sha256(data).hexdigest()
        if start_line is None and end_line is None:
            if len(data) > MAX_FILE_BYTES:
                raise ValueError(f'File exceeds the {MAX_FILE_BYTES}-byte response limit; '
                                 'use start_line and end_line to read a range.')
            return {'path': path, 'content': data.decode('utf-8'), 'sha256': digest}
        lines = split_lines(data.decode('utf-8'))
        start = 1 if start_line is None else integer_argument(start_line, 'start_line')
        end = len(lines) if end_line is None else integer_argument(end_line, 'end_line')
        if not lines:
            if start > 1:
                raise ValueError('start_line is past the end of the file (0 lines).')
            return {'path': path, 'content': '', 'sha256': digest, 'start_line': 1,
                    'end_line': 0, 'total_lines': 0, 'truncated': False}
        if start > end:
            raise ValueError('start_line cannot be greater than end_line.')
        if lines and start > len(lines):
            raise ValueError(f'start_line is past the end of the file ({len(lines)} lines).')
        encoded = ''.join(lines[start - 1:end]).encode('utf-8')
        truncated = len(encoded) > MAX_FILE_BYTES
        if truncated:
            encoded = encoded[:MAX_FILE_BYTES]
            newline = encoded.rfind(b'\n')
            if newline >= 0:
                encoded = encoded[:newline + 1]
        content = encoded.decode('utf-8', errors='ignore')
        returned = len(split_lines(content))
        return {'path': path, 'content': content, 'sha256': digest, 'start_line': start,
                'end_line': start + returned - 1 if returned else start,
                'total_lines': len(lines), 'truncated': truncated}

    def read_log(self, path: str, tail_lines: int | None = None, start_line: int | None = None,
                 end_line: int | None = None) -> dict[str, Any]:
        """Read a log through redaction. Path rules still apply; only the content refusal is lifted."""
        target = self.path(path)
        if not log_like(target.relative_to(self.root).as_posix()):
            raise ValueError('read_log only reads log-like files; use read_file for other files.')
        with os.fdopen(self._open_regular(target), 'rb') as stream:
            size = os.fstat(stream.fileno()).st_size
            offset = max(0, size - MAX_EDIT_BYTES)
            stream.seek(offset)
            data = stream.read(MAX_EDIT_BYTES + 1)[:MAX_EDIT_BYTES]
        if offset and b'\n' in data:
            data = data.split(b'\n', 1)[1]  # drop the partial first line of an oversized log
        if b'\x00' in data:
            raise ValueError('The file looks binary and cannot be read as a log.')
        # Redact the whole window first so a multi-line key cannot be split by the line slice.
        text, redacted = redact_sensitive_text(data.decode('utf-8', errors='replace'))
        lines = split_lines(text)
        if start_line is not None or end_line is not None:
            start = 1 if start_line is None else integer_argument(start_line, 'start_line')
            end = len(lines) if end_line is None else integer_argument(end_line, 'end_line')
            if start > end:
                raise ValueError('start_line cannot be greater than end_line.')
        else:
            count = min(200 if tail_lines is None else integer_argument(tail_lines, 'tail_lines'),
                        MAX_LOG_TAIL)
            end = len(lines)
            start = max(1, end - count + 1)
        chunk = ''.join(lines[start - 1:end])
        encoded = chunk.encode('utf-8')
        truncated = len(encoded) > MAX_FILE_BYTES
        if truncated:  # keep the newest part: that is where failures usually are
            encoded = encoded[-MAX_FILE_BYTES:]
            newline = encoded.find(b'\n')
            if newline >= 0:
                encoded = encoded[newline + 1:]
        shown = encoded.decode('utf-8', errors='ignore')
        returned = len(split_lines(shown))
        return {'path': path, 'content': shown, 'start_line': end - returned + 1 if returned else start,
                'end_line': end, 'total_lines': len(lines), 'truncated': truncated,
                'redacted': redacted, 'earlier_bytes_omitted': offset}

    def read_reference(self, name: str) -> dict[str, Any]:
        return {'name': name, 'content': reference_text(name)}

    def _manifest(self, relative: str) -> bytes | None:
        try:
            return self._load(relative)[1]
        except (OSError, ValueError):
            return None

    def project_overview(self) -> dict[str, Any]:
        paths: list[str] = []
        partial = False
        for relative in self._walk('.'):
            if relative is None:
                partial = True
                break
            paths.append(relative)
        return build_overview(paths, self._manifest, partial, list(self.checks), not self.checks_visible)

    def search_text(self, query: str, pattern: str | None = None, ignore_case: bool = False,
                    max_results: int = 100, directory: str = '.') -> dict[str, Any]:
        if not isinstance(query, str) or not query:
            raise ValueError('query must be a non-empty string.')
        if pattern is not None and not isinstance(pattern, str):
            raise ValueError('pattern must be a string.')
        limit = min(integer_argument(max_results, 'max_results'), MAX_SEARCH_RESULTS)
        needle = query.casefold() if ignore_case else query
        matches: list[dict[str, Any]] = []
        scanned_bytes = 0
        skipped = 0
        started = time.monotonic()
        start = self.path(directory, directory=True)
        for relative in self._walk(directory):
            if relative is None:
                return {'matches': matches, 'truncated': True, 'skipped': skipped}
            scoped = Path(relative).relative_to(start.relative_to(self.root)).as_posix()
            if not (matches_pattern(relative, pattern) or matches_pattern(scoped, pattern)):
                continue
            if scanned_bytes >= MAX_SEARCH_BYTES or time.monotonic() - started >= MAX_SEARCH_SECONDS:
                return {'matches': matches, 'truncated': True, 'skipped': skipped}
            try:
                _, data = self._load(relative)
                scanned_bytes += len(data)
                if b'\x00' in data:
                    skipped += 1
                    continue
                text = data.decode('utf-8')
            except (OSError, ValueError):
                skipped += 1  # unreadable, binary, oversized, or credential-like: report, do not hide
                continue
            for number, line in enumerate(text.split('\n'), 1):
                compared = line.casefold() if ignore_case else line
                if needle in compared:
                    if ignore_case:
                        found = re.search(re.escape(query), line, re.IGNORECASE)
                        position = found.start() if found else 0
                    else:
                        position = line.find(needle)
                    begin = max(0, position - 60)
                    matches.append({'path': relative, 'line': number,
                                    'text': line.rstrip('\r')[begin:begin + 200]})
                    if len(matches) >= limit:
                        return {'matches': matches, 'truncated': True, 'skipped': skipped}
        return {'matches': matches, 'truncated': False, 'skipped': skipped}

    # ------------------------------------------------------------------ writes

    def _require_write(self) -> None:
        if not self.allow_write:
            raise ValueError('Writing is not authorized; use --allow-write.')

    EXECUTABLE_MESSAGE = ('Writing automation, scripts, or executable files requires '
                          '--allow-executable-write.')

    def _require_write_path(self, target: Path) -> None:
        """Check the normalized, validated path, never the raw string supplied by the model."""
        if execution_surface(target.relative_to(self.root).as_posix()) and not self.allow_executable_write:
            raise ValueError(self.EXECUTABLE_MESSAGE)

    def _require_executable_content(self, target: Path, current: bytes | None, data: bytes) -> None:
        # Scripts are recognized by their interpreter line. The file mode is deliberately not
        # used: NTFS/drvfs mounts (for example WSL's /mnt/c) report every file as executable.
        if self.allow_executable_write:
            return
        if executable_content(data) or (current is not None and executable_content(current)):
            raise ValueError(self.EXECUTABLE_MESSAGE)

    def _replace_existing(self, relative: str, target: Path, data: bytes,
                          expected_sha256: str) -> None:
        """Replace atomically after revalidating the path and hash immediately beforehand."""
        mode = stat.S_IMODE(target.stat().st_mode)
        temporary = None
        try:
            with tempfile.NamedTemporaryFile(dir=target.parent, delete=False) as stream:
                temporary = Path(stream.name)
                stream.write(data)
                stream.flush()
                if os.name != 'nt':
                    os.fchmod(stream.fileno(), mode)
            # The handle must be closed before replacing or removing on Windows.
            self.path(relative)
            if hashlib.sha256(self._load(relative)[1]).hexdigest() != expected_sha256:
                raise ValueError('File changed during the write operation.')
            os.replace(temporary, target)
        finally:
            if temporary is not None:
                temporary.unlink(missing_ok=True)

    def write_file(self, path: str, content: str,
                   expected_sha256: str | None) -> dict[str, Any]:
        self._require_write()
        if not isinstance(content, str):
            raise ValueError('content must be a string.')
        data = content.encode('utf-8')
        if len(data) > MAX_FILE_BYTES:
            raise ValueError(f'Content exceeds the {MAX_FILE_BYTES}-byte limit.')
        target = self.path(path)
        self._require_write_path(target)
        if not target.parent.is_dir():
            raise ValueError('The parent directory must already exist; it is not created automatically.')
        if target.exists():
            _, current = self._load(path)
            if not expected_sha256 or expected_sha256 != hashlib.sha256(current).hexdigest():
                raise ValueError('File changed or was not read; read it again before writing.')
            self._require_executable_content(target, current, data)
            if uses_crlf(current) and b'\r' not in data:
                data = data.replace(b'\n', b'\r\n')  # preserve the file's line endings
                if len(data) > MAX_FILE_BYTES:
                    raise ValueError(f'Content exceeds the {MAX_FILE_BYTES}-byte limit after CRLF conversion.')
            if current.startswith(b'\xef\xbb\xbf') and not data.startswith(b'\xef\xbb\xbf'):
                data = b'\xef\xbb\xbf' + data
                if len(data) > MAX_FILE_BYTES:
                    raise ValueError(f'Content exceeds the {MAX_FILE_BYTES}-byte limit after BOM preservation.')
            self._replace_existing(path, target, data, expected_sha256)
        else:
            if expected_sha256 is not None:
                raise ValueError('File does not exist; pass null as expected_sha256 to create it.')
            self._require_executable_content(target, None, data)
            with target.open('xb') as stream:
                stream.write(data)
        return {'path': path, 'sha256': hashlib.sha256(data).hexdigest(), 'written': True}

    def replace_in_file(self, path: str, old: str, new: str, expected_sha256: str,
                        replace_all: bool = False) -> dict[str, Any]:
        self._require_write()
        self._require_write_path(self.path(path))
        if not isinstance(replace_all, bool):
            raise ValueError('replace_all must be a boolean.')
        if not isinstance(old, str) or not old or not isinstance(new, str):
            raise ValueError('old must be a non-empty string and new must be a string.')
        if not isinstance(expected_sha256, str) or not expected_sha256:
            raise ValueError('Provide the SHA-256 returned when the file was read.')
        target, current = self._load(path)
        if expected_sha256 != hashlib.sha256(current).hexdigest():
            raise ValueError('File changed or was not read; read it again before editing.')
        text = current.decode('utf-8')
        if uses_crlf(current):
            if '\r' not in old:
                old = old.replace('\n', '\r\n')
            if '\r' not in new:
                new = new.replace('\n', '\r\n')
        count = text.count(old)
        if count == 0:
            raise ValueError('old was not found; check whitespace, indentation, and line endings.')
        if count > 1 and not replace_all:
            raise ValueError(f'old appears {count} times; add context or use replace_all.')
        # Calculate the UTF-8 size before materializing a potentially huge expansion.
        # count follows the same non-overlapping occurrences as str.replace.
        replacements = count if replace_all else 1
        result_size = len(current) + replacements * (len(new.encode('utf-8')) - len(old.encode('utf-8')))
        if result_size > MAX_EDIT_BYTES:
            raise ValueError(f'Result exceeds the {MAX_EDIT_BYTES}-byte limit.')
        data = text.replace(old, new, replacements).encode('utf-8')
        self._require_executable_content(target, current, data)
        self._replace_existing(path, target, data, expected_sha256)
        return {'path': path, 'sha256': hashlib.sha256(data).hexdigest(), 'written': True,
                'replacements': replacements}

    # ------------------------------------------------------------------ checks

    def run_check(self, name: str) -> dict[str, Any]:
        if name not in self.checks:
            raise ValueError('Check is not authorized.')
        with tempfile.TemporaryFile() as output:
            process = subprocess.Popen(self.checks[name], cwd=self.root, stdin=subprocess.DEVNULL,
                                       stdout=output, stderr=subprocess.STDOUT,
                                       env=check_environment(self.pass_env), **process_options())
            timed_out = False
            try:
                process.wait(timeout=self.timeout)
            except subprocess.TimeoutExpired:
                timed_out = True
                stop_process_tree(process)
            except BaseException:
                stop_process_tree(process)
                raise
            size = output.seek(0, os.SEEK_END)
            if size <= OUTPUT_LIMIT:
                output.seek(0)
                text = output.read().decode('utf-8', errors='replace')
            else:
                # Failures are often near the end: keep the start and especially the tail.
                output.seek(0)
                head = output.read(OUTPUT_HEAD)
                output.seek(size - (OUTPUT_LIMIT - OUTPUT_HEAD))
                tail = output.read()
                text = (head.decode('utf-8', errors='replace') +
                        f'\n[... {size - OUTPUT_LIMIT} bytes omitted ...]\n' +
                        tail.decode('utf-8', errors='replace'))
        text, redacted = redact_sensitive_text(text)
        return {'name': name, 'exit_code': process.returncode, 'timed_out': timed_out,
                'output': text, 'truncated': size > OUTPUT_LIMIT, 'output_bytes': size,
                'redacted': redacted}

    def execute(self, name: str, arguments: Any) -> dict[str, Any]:
        enabled = {item['function']['name'] for item in self.definitions()}
        if name not in enabled:
            return {'error': 'Unknown or unauthorized tool.'}
        try:
            if not isinstance(arguments, dict):
                raise ValueError('Arguments must be a JSON object.')
            result: dict[str, Any] = getattr(self, name)(**arguments)
            return result
        except (ValueError, TypeError) as error:
            return {'error': str(error)}
        except FileNotFoundError:
            return {'error': 'File not found.'}
        except PermissionError:
            return {'error': 'Permission denied.'}
        except OSError:
            return {'error': 'The file operation failed.'}
        except Exception as error:  # an unexpected tool failure must not crash the paid task
            return {'error': f'Unexpected tool failure ({type(error).__name__}).'}
