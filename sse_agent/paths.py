"""Component-aware glob matching where ** represents zero or more directories."""

from fnmatch import fnmatchcase
from functools import cache


def matches_pattern(relative: str, pattern: str | None) -> bool:
    if not pattern:
        return True
    parts = relative.replace('\\', '/').split('/')
    normalized = pattern.replace('\\', '/')
    anchored = normalized.startswith(('./', '/'))
    directory_pattern = normalized.endswith('/')
    tokens = [token for token in normalized.split('/') if token and token != '.']
    if not tokens:
        return False
    if directory_pattern:
        tokens.append('**')
        # A trailing slash follows gitignore-style directory semantics unless
        # the operator explicitly anchors it with ./ or /.  Therefore dir/
        # protects both dir/... and nested/dir/....
        if not anchored:
            tokens.insert(0, '**')
    if len(tokens) == 1 and not anchored and '/' not in normalized.rstrip('/'):
        return fnmatchcase(parts[-1], tokens[0])

    @cache
    def match(i: int, j: int) -> bool:
        if j == len(tokens):
            return i == len(parts)
        if tokens[j] == '**':
            return match(i, j + 1) or (i < len(parts) and match(i + 1, j))
        return i < len(parts) and fnmatchcase(parts[i], tokens[j]) and match(i + 1, j + 1)

    return match(0, 0)
