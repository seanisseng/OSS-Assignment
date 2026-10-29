"""The one-case hosted smoke test cannot enable publication."""
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from scripts import smoke
from scripts.contract import digest


class SmokeTests(unittest.TestCase):
    def setUp(self):
        self.previous = Path.cwd()
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()
        os.chdir(self.root)
        self.addCleanup(os.chdir, self.previous)
        self.case = dict(case_id='pytest-15051', context={'issue': 'Historical report'})
        for name, value in {
            'evals/golden/inputs/pytest-15051.json': self.case,
            'evals/golden/expectations.json': {'expectations': [
                {'case_id': 'pytest-15051', 'input_hash': digest(self.case)}]},
            'config/policy.json': {'enabled': False, 'budget_verified': False},
        }.items():
            p = self.root / name
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(json.dumps(value), encoding='utf-8')
        skill = self.root / '.claude/skills/bug-report-clarification/SKILL.md'
        skill.parent.mkdir(parents=True)
        skill.write_text('Canonical procedure', encoding='utf-8')
        (self.root / 'AGENTS.md').write_text('Trusted instructions', encoding='utf-8')
        self.environment = patch.dict(os.environ, {
            'TRUSTED_ROOT': str(self.root), 'GITHUB_REPOSITORY': 'seanisseng/OSS-Assignment',
            'GITHUB_REF': 'refs/heads/main', 'GITHUB_RUN_ATTEMPT': '1',
            'CASE_ID': 'pytest-15051', 'SMOKE_ENABLED': 'true'}, clear=True)
        self.environment.start()
        self.addCleanup(self.environment.stop)
        self.review = patch.object(smoke, 'review_record', return_value={
            'configuration_hash': 'reviewed-configuration'})
        self.review_check = self.review.start()
        self.addCleanup(self.review.stop)
        self.api_patch = patch.object(smoke, 'api', return_value={'total_count': 1})
        self.api = self.api_patch.start()
        self.addCleanup(self.api_patch.stop)

    def test_exports_only_case_instructions_and_manifest_with_publication_disabled(self):
        smoke.prepare()
        manifest = json.loads(Path('input/manifest.json').read_text())
        self.assertIsNone(manifest['sandbox_issue'])
        self.assertTrue(manifest['artifact_only'])
        self.assertEqual(manifest['input_hash'], digest(self.case))
        self.assertEqual(manifest['configuration_hash'], 'reviewed-configuration')
        self.assertEqual(Path('.github/skills/bug-report-clarification/SKILL.md').read_text(),
                         'Canonical procedure')
        self.assertEqual(len(list(Path('input').iterdir())), 2)
        self.review_check.assert_called_once_with(self.root)
        self.api.assert_called_once_with('actions/workflows/smoke.lock.yml/runs?per_page=1')
        self.assertFalse(json.loads(Path('config/policy.json').read_text())['enabled'])

    def test_denies_disabled_wrong_case_branch_repository_and_retries(self):
        for key, value in [('SMOKE_ENABLED', 'false'), ('CASE_ID', 'pytest-14775'),
                           ('GITHUB_REF', 'refs/heads/other'),
                           ('GITHUB_REPOSITORY', 'pytest-dev/pytest'),
                           ('GITHUB_RUN_ATTEMPT', '2')]:
            with self.subTest(key=key), patch.dict(os.environ, {key: value}):
                with self.assertRaises(ValueError):
                    smoke.prepare()
        self.api.assert_not_called()

    def test_denies_second_dispatch_and_invalid_count(self):
        for count in [2, 0, True, '1']:
            with self.subTest(count=count):
                self.api.return_value = {'total_count': count}
                with self.assertRaises(ValueError):
                    smoke.prepare()

    def test_denies_stale_review_and_changed_input(self):
        self.review_check.side_effect = ValueError('review configuration changed')
        with self.assertRaisesRegex(ValueError, 'review configuration changed'):
            smoke.prepare()
        self.review_check.side_effect = None
        Path('evals/golden/inputs/pytest-15051.json').write_text(
            json.dumps(self.case | {'body': 'changed'}))
        with self.assertRaisesRegex(ValueError, 'input differs'):
            smoke.prepare()


if __name__ == '__main__':
    unittest.main()
