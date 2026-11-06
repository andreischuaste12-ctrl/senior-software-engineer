"""Read-only inventory of a workspace: stack markers, pins, CI, tests, and instruction files.

The result describes what is present and proposes commands as *candidates*; it never runs
anything. Only operator-defined checks can be executed, through run_check.
"""

from collections.abc import Callable, Iterable, Sequence
from fnmatch import fnmatchcase
import json
import re
import tomllib
from typing import Any

MAX_ITEMS = 40
MANIFESTS = {
    'pyproject.toml': 'python', 'setup.py': 'python', 'setup.cfg': 'python', 'pipfile': 'python',
    'requirements.txt': 'python', 'package.json': 'javascript', 'tsconfig.json': 'javascript',
    'go.mod': 'go', 'cargo.toml': 'rust', 'pom.xml': 'java', 'build.gradle': 'java',
    'build.gradle.kts': 'java', 'composer.json': 'php', 'gemfile': 'ruby', 'cmakelists.txt': 'c/c++',
}
LOCKFILES = {'poetry.lock', 'uv.lock', 'pipfile.lock', 'package-lock.json', 'yarn.lock',
             'pnpm-lock.yaml', 'bun.lockb', 'go.sum', 'cargo.lock', 'composer.lock', 'gemfile.lock'}
RUNTIME_PINS = {'.python-version', '.nvmrc', '.node-version', '.tool-versions', 'rust-toolchain',
                'rust-toolchain.toml', 'global.json', '.ruby-version', '.php-version'}
TEST_CONFIG_NAMES = {'pytest.ini', 'tox.ini', 'phpunit.xml', 'phpunit.xml.dist', 'phpcs.xml',
                     'phpcs.xml.dist'}
TEST_CONFIG_PATTERNS = ('jest.config.*', 'vitest.config.*', 'playwright.config.*')
CI_NAMES = {'.gitlab-ci.yml', 'azure-pipelines.yml', 'jenkinsfile', 'bitbucket-pipelines.yml'}
INFRA_NAMES = {'dockerfile', 'docker-compose.yml', 'docker-compose.yaml', 'compose.yml', 'compose.yaml'}
# Matched case-sensitively: AGENTS.md is an instruction file, a documentation page named agents.md is not.
INSTRUCTION_NAMES = {'AGENTS.md', 'CLAUDE.md', 'CONTRIBUTING.md', '.cursorrules'}
INSTRUCTION_PREFIXES = ('.claude/rules/', '.cursor/rules/')
LANGUAGE_SUFFIXES = {'.py': 'python', '.js': 'javascript', '.jsx': 'javascript', '.ts': 'typescript',
                     '.tsx': 'typescript', '.php': 'php', '.go': 'go', '.rs': 'rust', '.java': 'java',
                     '.kt': 'kotlin', '.cs': 'csharp', '.rb': 'ruby', '.c': 'c', '.cpp': 'c++',
                     '.sh': 'shell', '.sql': 'sql', '.tf': 'terraform'}
NOTE = ('Candidates are inferred from files and are not verified; only operator-configured checks '
        'can be run. When partial is true, files absent from this inventory may exist beyond the '
        'scan limit.')

Reader = Callable[[str], bytes | None]


def basename(path: str) -> str:
    return path.rsplit('/', 1)[-1].casefold()


def parse_json(data: bytes | None) -> dict[str, Any]:
    try:
        value = json.loads(data) if data is not None else {}
    except (ValueError, RecursionError):
        return {}
    return value if isinstance(value, dict) else {}


def parse_toml(data: bytes | None) -> dict[str, Any]:
    try:
        return tomllib.loads(data.decode('utf-8')) if data is not None else {}
    except (ValueError, UnicodeDecodeError):
        return {}


def script_names(document: dict[str, Any]) -> set[str]:
    scripts = document.get('scripts')
    return {str(key) for key in scripts} if isinstance(scripts, dict) else set()


def candidate(ecosystem: str, command: str, basis: str) -> dict[str, str]:
    return {'ecosystem': ecosystem, 'command': command, 'basis': basis, 'status': 'candidate'}


def candidate_commands(items: list[str], read: Reader) -> list[dict[str, str]]:
    """Propose commands from files that exist; each one names the file it is based on."""
    names = {basename(path): path for path in items}
    found: list[dict[str, str]] = []
    if 'pyproject.toml' in names:
        document = parse_toml(read(names['pyproject.toml']))
        tools = document.get('tool', {}) if isinstance(document.get('tool'), dict) else {}
        if 'pytest' in tools or 'pytest.ini' in names:
            found.append(candidate('python', 'python -m pytest', 'pytest configuration'))
        if 'ruff' in tools:
            found.append(candidate('python', 'python -m ruff check .', '[tool.ruff] in pyproject.toml'))
        if 'mypy' in tools:
            found.append(candidate('python', 'python -m mypy', '[tool.mypy] in pyproject.toml'))
    if not any('pytest' in item['command'] for item in found) and any(
            basename(path).startswith('test_') and path.endswith('.py') for path in items):
        found.append(candidate('python', 'python -m unittest discover', 'test_*.py files (low confidence)'))
    if 'package.json' in names:
        manager = ('yarn' if 'yarn.lock' in names else 'pnpm' if 'pnpm-lock.yaml' in names else 'npm')
        for script in sorted(script_names(parse_json(read(names['package.json']))) & {
                'test', 'lint', 'typecheck', 'build'}):
            command = f'{manager} test' if script == 'test' else f'{manager} run {script}'
            found.append(candidate('javascript', command, f'"{script}" script in package.json'))
    if 'go.mod' in names:
        found.append(candidate('go', 'go test ./...', 'go.mod'))
        found.append(candidate('go', 'go vet ./...', 'go.mod'))
    if 'cargo.toml' in names:
        found.append(candidate('rust', 'cargo test', 'Cargo.toml'))
    if 'pom.xml' in names:
        found.append(candidate('java', 'mvn test', 'pom.xml'))
    if 'build.gradle' in names or 'build.gradle.kts' in names:
        wrapper = './gradlew test' if 'gradlew' in names else 'gradle test'
        found.append(candidate('java', wrapper, 'Gradle build file'))
    if 'composer.json' in names:
        for script in sorted(script_names(parse_json(read(names['composer.json']))) & {
                'test', 'lint', 'phpcs', 'phpstan'}):
            found.append(candidate('php', f'composer run {script}', f'"{script}" script in composer.json'))
    if 'phpunit.xml' in names or 'phpunit.xml.dist' in names:
        found.append(candidate('php', 'vendor/bin/phpunit', 'phpunit configuration'))
    if any(path.endswith(('.sln', '.csproj')) for path in items):
        found.append(candidate('dotnet', 'dotnet test', 'solution or project file'))
    if 'makefile' in names:
        text = (read(names['makefile']) or b'').decode('utf-8', errors='replace')
        if re.search(r'^test\s*:', text, re.MULTILINE):
            found.append(candidate('make', 'make test', 'test target in Makefile'))
    return found


def build_overview(paths: Iterable[str], read: Reader, partial: bool, checks: Sequence[str],
                   checks_hidden: bool) -> dict[str, Any]:
    items = sorted(set(paths))
    truncated = False

    def capped(values: list[Any]) -> list[Any]:
        nonlocal truncated
        truncated = truncated or len(values) > MAX_ITEMS
        return values[:MAX_ITEMS]

    manifests = [p for p in items if basename(p) in MANIFESTS or p.endswith(('.sln', '.csproj'))]
    ecosystems = {MANIFESTS.get(basename(p), 'dotnet') for p in manifests}
    directories = {part for p in items for part in p.casefold().split('/')[:-1]}
    if directories & {'wp-content', 'wp-includes'} or any(basename(p) == 'wp-load.php' for p in items):
        ecosystems.add('wordpress')
        if any('woocommerce' in part for part in directories):
            ecosystems.add('woocommerce')
    counts: dict[str, int] = {}
    for path in items:
        for suffix, language in LANGUAGE_SUFFIXES.items():
            if path.casefold().endswith(suffix):
                counts[language] = counts.get(language, 0) + 1
    tests = [p for p in items if basename(p) in TEST_CONFIG_NAMES or
             any(fnmatchcase(basename(p), pattern) for pattern in TEST_CONFIG_PATTERNS)]
    ci = [p for p in items if (p.startswith('.github/workflows/') and p.endswith(('.yml', '.yaml')))
          or basename(p) in CI_NAMES or p.casefold() == '.circleci/config.yml']
    infrastructure = [p for p in items if basename(p) in INFRA_NAMES or p.endswith('.tf')]
    instructions = sorted(
        ({'path': p, 'scope': p.rsplit('/', 1)[0] if '/' in p else '.'} for p in items
         if p.rsplit('/', 1)[-1] in INSTRUCTION_NAMES or p.casefold() == '.github/copilot-instructions.md'
         or p.casefold().startswith(INSTRUCTION_PREFIXES)
         or (basename(p).startswith('readme') and '/' not in p)),
        key=lambda entry: (entry['path'].count('/'), entry['path']))
    result = {
        'languages': dict(sorted(counts.items(), key=lambda pair: (-pair[1], pair[0]))[:8]),
        'ecosystems': sorted(ecosystems),
        'manifests': capped(manifests),
        'lockfiles': capped([p for p in items if basename(p) in LOCKFILES]),
        'runtime_pins': capped([p for p in items if basename(p) in RUNTIME_PINS]),
        'test_config': capped(tests),
        'ci': capped(ci),
        'infrastructure': capped(infrastructure),
        'instructions': capped(instructions),
        'candidate_commands': capped(candidate_commands(items, read)),
        'configured_checks': [] if checks_hidden else list(checks),
        'checks_hidden': checks_hidden and bool(checks),
        'partial': partial,
        'lists_truncated': truncated,
        'note': NOTE,
    }
    return result
