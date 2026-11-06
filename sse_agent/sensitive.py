"""Credential-like content detection and redaction.

This is defense in depth, not complete secret detection: signatures cover recognizable
private keys and provider token formats, and ignore obvious documentation placeholders.
"""

from collections.abc import Callable
import re

# Cheap pre-filter so ordinary files avoid running every signature.
HINT = re.compile(
    rb'BEGIN|AKIA|ASIA|aws|AWS|github_pat_|gh[pousr]_|xox[baprs]-|hooks\.slack\.com|sk-|sk_live_|rk_live_|'
    rb'whsec_|AIza|ya29\.|eyJ|npm_|glpat-|SG\.|AccountKey|://|ck_|cs_|shp(?:at|ss|ca|pa)_|APP_USR-|key-')
PRIVATE_KEY = re.compile(rb'-----BEGIN (?:[A-Z0-9]+ )*PRIVATE KEY(?: BLOCK)?-----')
BASE64_RUN = re.compile(rb'[A-Za-z0-9+/]{40,}={0,2}')
PLACEHOLDER_WORDS = (b'example', b'your', b'xxxx', b'placeholder', b'changeme', b'dummy', b'sample',
                     b'redacted', b'fake')
WEAK_PASSWORDS = {b'password', b'passwd', b'secret', b'postgres', b'mysql', b'admin', b'root',
                  b'redis', b'test', b'testing', b'changeme', b'example'}


def looks_real(token: bytes) -> bool:
    """Reject documentation placeholders such as AKIA...EXAMPLE or ghp_aaaa..."""
    lowered = token.lower()
    if any(word in lowered for word in PLACEHOLDER_WORDS):
        return False
    # Judge the body, not the provider prefix: ghp_aaaa... is a placeholder.
    body = lowered[8:] if len(lowered) > 16 else lowered
    return len(set(body)) > 3


def real_password(token: bytes) -> bool:
    lowered = token.lower()
    if lowered in WEAK_PASSWORDS or lowered[:1] in {b'$', b'{', b'<', b'%', b'*'}:
        return False
    return looks_real(token)


def boundary(body: bytes) -> bytes:
    return rb'(?<![A-Za-z0-9_])' + body + rb'(?![A-Za-z0-9_])'


# (name, regex, capture group holding the secret, validator)
SIGNATURES: tuple[tuple[str, re.Pattern[bytes], int, Callable[[bytes], bool]], ...] = (
    ('aws-access-key', re.compile(boundary(rb'(?:AKIA|ASIA)[A-Z0-9]{16}')), 0, looks_real),
    ('aws-secret-key', re.compile(
        rb'(?i)aws_?secret_?access_?key["\']?\s*[:=]\s*["\']?([A-Za-z0-9/+=]{40})'), 1, looks_real),
    ('github-token', re.compile(boundary(rb'github_pat_[A-Za-z0-9_]{20,}')), 0, looks_real),
    ('github-token', re.compile(boundary(rb'gh[pousr]_[A-Za-z0-9]{20,}')), 0, looks_real),
    ('slack-token', re.compile(boundary(rb'xox[baprs]-[A-Za-z0-9-]{20,}')), 0, looks_real),
    ('slack-webhook', re.compile(
        rb'hooks\.slack\.com/services/T[A-Z0-9]{6,}/B[A-Z0-9]{6,}/[A-Za-z0-9]{16,}'), 0, looks_real),
    ('anthropic-key', re.compile(rb'sk-ant-[A-Za-z0-9_-]{20,}'), 0, looks_real),
    ('openai-key', re.compile(rb'sk-(?:proj|svcacct|admin)-[A-Za-z0-9_-]{20,}'), 0, looks_real),
    ('openai-key', re.compile(rb'(?<![A-Za-z0-9_-])sk-[A-Za-z0-9]{32,}(?![A-Za-z0-9_-])'), 0, looks_real),
    ('stripe-key', re.compile(boundary(rb'(?:sk|rk)_live_[A-Za-z0-9]{16,}')), 0, looks_real),
    ('stripe-webhook', re.compile(boundary(rb'whsec_[A-Za-z0-9]{24,}')), 0, looks_real),
    ('google-api-key', re.compile(rb'AIza[0-9A-Za-z_-]{35}'), 0, looks_real),
    ('google-oauth-token', re.compile(rb'ya29\.[0-9A-Za-z_-]{20,}'), 0, looks_real),
    ('jwt', re.compile(rb'eyJ[A-Za-z0-9_-]{10,}\.eyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}'), 0, looks_real),
    ('npm-token', re.compile(boundary(rb'npm_[A-Za-z0-9]{36}')), 0, looks_real),
    ('gitlab-token', re.compile(rb'glpat-[A-Za-z0-9_-]{20,}'), 0, looks_real),
    ('sendgrid-key', re.compile(rb'SG\.[A-Za-z0-9_-]{16,}\.[A-Za-z0-9_-]{16,}'), 0, looks_real),
    ('azure-storage-key', re.compile(rb'AccountKey=([A-Za-z0-9+/]{40,}={0,2})'), 1, looks_real),
    ('database-url', re.compile(
        rb'(?:postgres(?:ql)?|mysql|mariadb|mongodb(?:\+srv)?|redis|rediss|amqps?|mssql)://'
        rb'[^\s:/@\'"]+:([^\s@/\'"]{8,})@'), 1, real_password),
    ('woocommerce-key', re.compile(boundary(rb'c[ks]_[a-f0-9]{40}')), 0, looks_real),
    ('shopify-token', re.compile(boundary(rb'shp(?:at|ss|ca|pa)_[a-f0-9]{32}')), 0, looks_real),
    ('mercadopago-token', re.compile(rb'APP_USR-[0-9]{10,}-[0-9]{6}-[a-f0-9]{32}-[0-9]{6,}'), 0, looks_real),
    ('mailgun-key', re.compile(boundary(rb'key-[0-9a-f]{32}')), 0, looks_real),
)


def find_sensitive(data: bytes) -> list[tuple[int, int, str]]:
    """Return (start, end, kind) spans of credential-like content."""
    if not HINT.search(data):
        return []
    spans: list[tuple[int, int, str]] = []
    for header in PRIVATE_KEY.finditer(data):
        following = data[header.end():header.end() + 600]
        body = BASE64_RUN.search(following)
        if body:
            end = header.end() + body.end()
            while end < len(data) and data[end:end + 1] in b'ABCDEFGHIJKLMNOPQRSTUVWXYZ' \
                    b'abcdefghijklmnopqrstuvwxyz0123456789+/=\r\n ':
                end += 1
            spans.append((header.start(), end, 'private-key'))
    for kind, pattern, group, valid in SIGNATURES:
        for match in pattern.finditer(data):
            if valid(match.group(group)):
                spans.append((match.start(group), match.end(group), kind))
    return sorted(spans)


def contains_sensitive_content(data: bytes) -> bool:
    return bool(find_sensitive(data))


def redact_sensitive_text(text: str) -> tuple[str, bool]:
    """Replace credential-like spans in text and report whether anything was redacted."""
    data = text.encode('utf-8')
    spans = find_sensitive(data)
    if not spans:
        return text, False
    output = bytearray()
    cursor = 0
    for start, end, kind in spans:
        if start < cursor:
            continue
        output += data[cursor:start] + f'[REDACTED:{kind}]'.encode()
        cursor = end
    output += data[cursor:]
    return output.decode('utf-8', errors='replace'), True
