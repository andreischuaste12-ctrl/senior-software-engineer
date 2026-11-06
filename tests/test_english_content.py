"""Prevent Portuguese prose from returning to maintained project content."""

from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parent.parent
TEXT_SUFFIXES = {'.md', '.py', '.toml', '.yml', '.yaml', '.json', '.txt'}
IGNORED_PARTS = {'.git', '.mypy_cache', '.ruff_cache', '__pycache__', 'build', 'dist'}
# Hex keeps the prohibited-language samples out of the maintained source itself.
ACCENTED = bytes.fromhex('c3a3c3b5c3a1c3a0c3a2c3a9c3aac3adc3b3c3b4c3bac3a7').decode()
WORD_HEX = (
    '6ec3a36f', '6172717569766f', '6172717569766f73', '6176616c6961c3a7c3a36f',
    '63c3b36469676f', '636f6e7465c3ba646f', '636f727265c3a7c3a36f',
    '6469726574c3b372696f', '696e73747275c3a7c3b56573', '6c6963656ec3a761',
    '70726f6a65746f', '7265666572c3aa6e636961', '7265766973c3a36f',
    '7365677572616ec3a761', '757375c3a172696f', '76616c696461c3a7c3a36f',
)
PORTUGUESE_WORDS = [bytes.fromhex(value).decode() for value in WORD_HEX]
PORTUGUESE_MARKERS = re.compile(
    f'[{re.escape(ACCENTED + ACCENTED.upper())}]|\\b(?:{"|".join(PORTUGUESE_WORDS)})\\b',
    re.IGNORECASE,
)


class EnglishContentTests(unittest.TestCase):
    def test_maintained_text_is_english(self):
        findings = []
        for path in sorted(ROOT.rglob('*')):
            if (not path.is_file() or path.suffix not in TEXT_SUFFIXES or
                    any(part in IGNORED_PARTS or part.endswith('.egg-info') for part in path.parts)):
                continue
            for number, line in enumerate(path.read_text(encoding='utf-8').splitlines(), 1):
                if PORTUGUESE_MARKERS.search(line):
                    findings.append(f'{path.relative_to(ROOT)}:{number}: {line.strip()}')
        self.assertEqual(findings, [], '\n'.join(findings))


if __name__ == '__main__':
    unittest.main()
