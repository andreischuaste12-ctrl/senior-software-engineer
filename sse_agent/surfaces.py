"""Paths and content that can run code later, so writes to them need an explicit opt-in."""

from fnmatch import fnmatchcase
import posixpath

EXECUTION_FILENAMES = {
    'conftest.py', 'setup.py', 'sitecustomize.py', 'usercustomize.py', 'noxfile.py', 'tox.ini',
    'setup.cfg', 'pytest.ini', '.coveragerc', 'makefile', 'gnumakefile', 'justfile', 'rakefile',
    'gemfile', 'procfile', 'vagrantfile', 'jenkinsfile', 'dockerfile', 'docker-compose.yml',
    'docker-compose.yaml', 'compose.yml', 'compose.yaml', 'taskfile.yml', 'taskfile.yaml',
    'package.json', 'composer.json', 'pyproject.toml', 'cargo.toml', 'build.rs', 'build.gradle',
    'build.gradle.kts', 'settings.gradle', 'settings.gradle.kts', 'pom.xml', 'cmakelists.txt',
    '.pre-commit-config.yaml', '.gitmodules', '.gitlab-ci.yml', '.travis.yml', 'appveyor.yml',
    'azure-pipelines.yml', 'bitbucket-pipelines.yml', 'phpunit.xml', 'phpunit.xml.dist',
    '.bashrc', '.bash_profile', '.zshrc', '.profile', '.babelrc', '.babelrc.js',
}
EXECUTION_PATTERNS = ('*.config.js', '*.config.cjs', '*.config.mjs', '*.config.ts', '*.config.mts',
                      '*.config.cts', 'gulpfile.*', 'gruntfile.*', '.eslintrc.js', '.eslintrc.cjs',
                      '.mocharc.js', '.mocharc.cjs', '.prettierrc.js')
EXECUTION_SUFFIXES = ('.sh', '.bash', '.zsh', '.fish', '.ps1', '.psm1', '.bat', '.cmd', '.vbs',
                      '.mk', '.make', '.cmake', '.pth')
EXECUTION_DIRECTORIES = {'.github', '.circleci', '.gitlab', '.githooks', '.husky', '.vscode',
                         '.idea', '.devcontainer', 'scripts', 'bin', 'hack'}


def normalize_relative(relative: str) -> str:
    """Normalize separators, dot segments, repeated slashes, and case."""
    text = relative.replace('\\', '/').casefold()
    normalized = posixpath.normpath(text) if text.strip('/') else ''
    return normalized.removeprefix('./').strip('/')


def execution_surface(relative: str) -> bool:
    """Return whether writing this path can trigger common automation."""
    normalized = normalize_relative(relative)
    if not normalized or normalized == '.':
        return False
    parts = normalized.split('/')
    name = parts[-1]
    return (name in EXECUTION_FILENAMES or
            any(fnmatchcase(name, pattern) for pattern in EXECUTION_PATTERNS) or
            name.endswith(EXECUTION_SUFFIXES) or
            any(part in EXECUTION_DIRECTORIES for part in parts[:-1]))


def executable_content(data: bytes) -> bool:
    """Return whether bytes start like a script with an interpreter line."""
    return data.startswith(b'#!')
