"""Component-aware glob matching where ** represents zero or more directories."""

from fnmatch import fnmatchcase
from functools import cache


def matches_pattern(relative: str, pattern: str | None) -> bool:
    if not pattern:
        return True
    parts = relative.replace('\\', '/').split('/')
    pattern = pattern.replace('\\', '/')
    if pattern.startswith('./'):
        pattern = pattern[2:]
    tokens = pattern.split('/')
    if len(tokens) == 1:
        return fnmatchcase(parts[-1], tokens[0])

    @cache
    def match(i: int, j: int) -> bool:
        if j == len(tokens):
            return i == len(parts)
        if tokens[j] == '**':
            return match(i, j + 1) or (i < len(parts) and match(i + 1, j))
        return i < len(parts) and fnmatchcase(parts[i], tokens[j]) and match(i + 1, j + 1)

    return match(0, 0)
