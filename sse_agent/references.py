"""Read-only access to the skill package's reference documents.

The references live in the installed skill package, not in the user's workspace, so the
file tools cannot reach them. Access is limited to a fixed list of names: no path is ever
built from model input.
"""

from importlib.resources import files
from importlib.resources.abc import Traversable
from pathlib import Path

REFERENCE_NAMES = ('ecosystems', 'debugging', 'audit', 'agents', 'knowledge', 'api-currency',
                   'url-matrix')
MAX_REFERENCE_BYTES = 64_000


def skill_package() -> Traversable:
    """Return the skill directory from a checkout, or the installed sse_skill package."""
    checkout = Path(__file__).resolve().parent.parent / 'skills' / 'senior-software-engineer'
    if (checkout / 'SKILL.md').is_file():
        return checkout
    return files('sse_skill')


def reference_text(name: object) -> str:
    """Return one reference document by exact allowlisted name."""
    if not isinstance(name, str) or name not in REFERENCE_NAMES:
        raise ValueError('Unknown reference; choose one of: ' + ', '.join(REFERENCE_NAMES) + '.')
    try:
        text = (skill_package() / 'references' / f'{name}.md').read_text(encoding='utf-8')
    except OSError:
        raise ValueError('The reference is unavailable; reinstall the package.') from None
    if len(text.encode('utf-8')) > MAX_REFERENCE_BYTES:
        raise ValueError('The reference exceeds the response limit.')
    return text
