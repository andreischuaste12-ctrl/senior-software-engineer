import hashlib
import json
from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parent.parent


class DocumentationIntegrityTests(unittest.TestCase):
    def test_knowledge_edition_digest_matches_the_named_file(self):
        record = json.loads((ROOT / 'docs/verifications/knowledge-base-v2-2026-11-05.json').read_text())
        source = ROOT / record['english_edition_file']
        self.assertTrue(source.is_file())
        self.assertEqual(hashlib.sha256(source.read_bytes()).hexdigest(),
                         record['english_edition_sha256'])
        self.assertNotIn('original_file', record)
        self.assertIn('original_submitted_sha256', record)

    def test_evaluation_manifest_has_required_structural_fields(self):
        manifest = json.loads((ROOT / 'skills/senior-software-engineer/evals/evals.json').read_text())
        self.assertEqual(manifest['skill_name'], 'senior-software-engineer')
        self.assertTrue(manifest['evals'])
        required = {'id', 'category', 'type', 'objective', 'prompt', 'expected_output',
                    'severity_if_failed', 'files', 'expectations', 'forbidden', 'allowed_changes'}
        for evaluation in manifest['evals']:
            self.assertFalse(required - evaluation.keys(), evaluation['id'])
        self.assertEqual({item['id'] for item in manifest['evals']},
                         set(manifest['automated_scenarios']))
        self.assertEqual({item['category'] for item in manifest['evals']},
                         {'happy-path', 'edge-case', 'negative-trigger', 'security-abuse',
                          'regression-guard'})

    def test_version_is_consistent_across_code_changelog_and_guide(self):
        from sse_agent import __version__
        changelog = (ROOT / 'CHANGELOG.md').read_text(encoding='utf-8')
        newest = re.search(r'^## (\S+) - ', changelog, re.MULTILINE)
        self.assertIsNotNone(newest)
        self.assertEqual(newest.group(1), __version__)
        guide = (ROOT / 'docs/cli-agent.md').read_text(encoding='utf-8')
        self.assertIn(f'# Terminal AI agent — {__version__}', guide)

    def test_relative_markdown_links_resolve(self):
        broken = []
        for document in ROOT.rglob('*.md'):
            if any(part.startswith('.') for part in document.relative_to(ROOT).parts):
                continue
            text = document.read_text(encoding='utf-8')
            for target in re.findall(r'\]\(([^)]+)\)', text):
                path = target.split('#', 1)[0]
                if not path or path.startswith(('http://', 'https://', 'mailto:')):
                    continue
                if not (document.parent / path).resolve().exists():
                    broken.append(f'{document.relative_to(ROOT)} -> {target}')
        self.assertEqual(broken, [])


if __name__ == '__main__':
    unittest.main()
