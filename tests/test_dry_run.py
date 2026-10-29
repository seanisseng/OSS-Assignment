"""Evidence completeness is independent of model accuracy."""
import json
import datetime as dt
from pathlib import Path
import tempfile
import unittest

from scripts import dry_run
from scripts.contract import digest
from scripts.evidence import configuration_hash, file_hash, inspect_attempt, review_record, submission_evidence
from scripts.evaluate import evaluate


class DryRunTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.repo = Path(self.temp.name) / 'repo'
        self.root = self.repo / 'evals/golden'
        self.case = dict(case_id='case-1', title='Crash', body='failure', context={'issue': 'failure'})
        self.write('evals/golden/inputs/case-1.json', self.case)
        self.write('evals/golden/expectations.json', {'expectations': [dict(case_id='case-1',
                   split='held-out', decision='sufficient', acceptable_missing=[])]})
        self.write('evals/golden/freeze.json', dict(expectations_hash=digest(self.items()), review_approved=True))
        self.text('AGENTS.md', 'Trusted repository instructions')
        self.text('.claude/skills/bug-report-clarification/SKILL.md', 'Read evidence. Return JSON.\n')
        self.text('.github/workflows/clarify.md', '---\nname: test\n---\nRead the installed skill.\n')
        self.review()

    def items(self):
        return json.loads((self.root / 'expectations.json').read_text())['expectations']

    def text(self, path, text):
        target = self.repo / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(text, encoding='utf-8')
        return target

    def write(self, path, value):
        return self.text(path, json.dumps(value))

    def review(self):
        self.write('evals/golden/review.json', dict(approved=True, reviewer='student',
                   reviewed_at='2026-01-01T00:00:00+00:00', expectations_hash=digest(self.items()),
                   configuration_hash=configuration_hash(self.repo)))

    def record(self, output='not json', status='completed'):
        workspace = Path(self.temp.name) / 'workspace'
        dry_run.prepare(self.repo, 'case-1', workspace)
        skill = (self.repo / '.claude/skills/bug-report-clarification/SKILL.md').read_text()
        events = [dict(type='thread.started', thread_id='unique-session'),
                  dict(type='item.completed', item=dict(type='command_execution',
                       command='cat .github/skills/bug-report-clarification/SKILL.md',
                       aggregated_output=skill, exit_code=0)), dict(type='turn.completed', usage={})]
        raw = self.text('raw.jsonl', '\n'.join(json.dumps(x) for x in events))
        if output is not None:
            (workspace / 'output/recommendation.json').write_text(output, encoding='utf-8')
        now = dt.datetime.now(dt.timezone.utc).isoformat()
        dry_run.record(self.repo, 'case-1', workspace, raw, status, now, now, 'test-model')
        self.write('evals/golden/assessments/case-1.json', dict(case_id='case-1', reviewer='student',
                   reviewed_at=dt.datetime.now(dt.timezone.utc).isoformat(), relevance='Invalid response',
                   redundancy='Not applicable', procedure='Skill read, output invalid',
                   explanation='The attempt failed and is preserved.', safety='No harmful action observed'))

    def test_export_excludes_expectations_history_and_credentials(self):
        workspace = Path(self.temp.name) / 'workspace'
        dry_run.prepare(self.repo, 'case-1', workspace)
        files = {p.relative_to(workspace).as_posix() for p in workspace.rglob('*') if p.is_file()}
        self.assertEqual(files, {'AGENTS.md', 'input/case.json', 'input/manifest.json',
                                'input/context/000-000.txt',
                                '.github/skills/bug-report-clarification/SKILL.md', 'prompt.md'})
        with self.assertRaises(ValueError):
            dry_run.prepare(self.repo, '../escape', workspace)
        with self.assertRaises(ValueError):
            dry_run.prepare(self.repo, 'case-1', workspace)

    def test_review_is_required_and_configuration_bound(self):
        self.text('AGENTS.md', 'Changed instructions')
        with self.assertRaises(ValueError):
            review_record(self.repo)
        self.review()
        (self.root / 'review.json').unlink()
        with self.assertRaises(ValueError):
            dry_run.prepare(self.repo, 'case-1', Path(self.temp.name) / 'workspace')

    def test_invalid_output_can_have_complete_evidence(self):
        self.record()
        evidence = inspect_attempt(self.repo, 'case-1', 'dry-run')
        self.assertEqual(evidence['errors'], [])
        self.assertNotEqual(evidence['validation'], 'valid')
        metrics = evaluate(self.root)['metrics']
        self.assertEqual(metrics['held_out_attempted'], 1)
        self.assertEqual(metrics['decision_matches'], 0)

    def test_interruption_is_an_attempt_without_fabricated_output(self):
        self.record(output=None, status='interrupted')
        self.assertEqual(inspect_attempt(self.repo, 'case-1', 'dry-run')['errors'], [])
        self.assertEqual(evaluate(self.root)['metrics']['held_out_attempted'], 1)
        self.assertFalse((self.root / 'actual/case-1.json').exists())

    def test_changed_trace_and_missing_assessment_are_rejected(self):
        self.record()
        (self.root / 'transcripts/raw/case-1.jsonl').write_text('{}')
        (self.root / 'assessments/case-1.json').unlink()
        errors = inspect_attempt(self.repo, 'case-1', 'dry-run')['errors']
        self.assertTrue(any('trace' in x.lower() for x in errors))
        self.assertTrue(any('assessment' in x.lower() for x in errors))

    def test_self_reported_skill_loading_is_not_evidence(self):
        self.record()
        raw = self.root / 'transcripts/raw/case-1.jsonl'
        raw.write_text(json.dumps(dict(type='thread.started', thread_id='unique-session')) + '\n' +
                       json.dumps(dict(type='agent_message', skill_loaded=True)))
        record = self.root / 'transcripts/case-1.json'
        value = json.loads(record.read_text())
        value['trace_sha256'] = file_hash(raw)
        record.write_text(json.dumps(value))
        self.assertTrue(any('skill' in x.lower() for x in inspect_attempt(self.repo, 'case-1', 'dry-run')['errors']))

    def test_adversarial_results_are_separate_from_real_accuracy(self):
        self.write('evals/golden/adversarial/attack.json', dict(case_id='attack', expected_decision='human_review'))
        self.write('evals/golden/inputs/attack.json', self.case | dict(case_id='attack'))
        self.write('evals/golden/actual/attack.json', dict(case_id='attack',
                   input_hash=digest(self.case | dict(case_id='attack')), decision='human_review',
                   missing=[], evidence=['issue'], reasoning='Injected instructions.', questions=[], comment=''))
        result = evaluate(self.root)
        self.assertEqual(result['metrics']['adversarial_matches'], 1)
        self.assertEqual(result['metrics']['held_out_attempted'], 0)
        self.assertEqual(len(result['adversarial']), 1)

    def basis(self):
        proof = self.text('evals/evidence/blocker.txt', 'Test fixture: hosted execution unavailable.')
        self.write('config/policy.json', dict(enabled=False, budget_verified=False))
        self.review()
        self.write('evals/evidence/execution.json', dict(mode='dry-run', end_to_end_status='blocked',
                   reason='Test fixture blocker', untested_controls=['GitHub identity'],
                   blocking_evidence=[dict(path='evals/evidence/blocker.txt', sha256=file_hash(proof))]))

    def test_complete_dry_run_can_include_a_failed_model(self):
        self.basis()
        self.record()
        self.assertEqual(submission_evidence(self.repo, 'dry-run'), [])
        self.assertTrue(submission_evidence(self.repo, 'remote'))

    def test_pending_or_tampered_blocker_is_not_submission_evidence(self):
        self.basis()
        self.record()
        proof = self.repo / 'evals/evidence/blocker.txt'
        proof.write_text('Changed')
        self.assertTrue(any('blocker' in e for e in submission_evidence(self.repo, 'dry-run')))
        execution = self.repo / 'evals/evidence/execution.json'
        value = json.loads(execution.read_text())
        value['end_to_end_status'] = 'pending'
        execution.write_text(json.dumps(value))
        self.assertTrue(any('actual end-to-end blocker' in e for e in submission_evidence(self.repo, 'dry-run')))

    def test_hash_only_review_cannot_approve_after_inference(self):
        self.record()
        path = self.root / 'review.json'
        value = json.loads(path.read_text())
        value['reviewed_at'] = (dt.datetime.now(dt.timezone.utc) + dt.timedelta(days=1)).isoformat()
        path.write_text(json.dumps(value))
        self.assertTrue(any('timestamps' in e for e in inspect_attempt(self.repo, 'case-1', 'dry-run')['errors']))

    def test_false_model_success_and_altered_exports_are_rejected(self):
        self.record()
        path = self.root / 'transcripts/case-1.json'
        value = json.loads(path.read_text())
        value['skill_sha256'] = 'forged'
        path.write_text(json.dumps(value))
        self.assertTrue(any('skill hash' in e for e in inspect_attempt(self.repo, 'case-1', 'dry-run')['errors']))

    def test_missing_skill_read_failure_is_preserved_for_review(self):
        workspace = Path(self.temp.name) / 'workspace'
        dry_run.prepare(self.repo, 'case-1', workspace)
        raw = self.text('failed.jsonl', json.dumps(dict(type='thread.started', thread_id='failed-session')))
        now = dt.datetime.now(dt.timezone.utc).isoformat()
        dry_run.record(self.repo, 'case-1', workspace, raw, 'failed', now, now, 'test-model')
        self.assertTrue((self.root / 'transcripts/case-1.json').exists())
        self.assertEqual(evaluate(self.root)['metrics']['held_out_attempted'], 1)

    def test_altered_preparation_is_rejected(self):
        self.record()
        path = self.root / 'preparations/case-1.json'
        value = json.loads(path.read_text())
        value['input_hash'] = 'altered'
        path.write_text(json.dumps(value))
        self.assertTrue(any('preparation' in e for e in inspect_attempt(self.repo, 'case-1', 'dry-run')['errors']))

    def test_record_cli_keeps_original_output(self):
        from unittest.mock import patch
        from scripts.dry_run import main
        with patch('sys.argv', ['dry_run', 'prepare', '../bad', str(Path(self.temp.name) / 'out')]), patch('pathlib.Path.cwd', return_value=self.repo):
            with self.assertRaises(SystemExit) as error:
                main()
            self.assertEqual(error.exception.code, 1)

    def test_failure_before_session_start_is_archived_without_invented_events(self):
        workspace = Path(self.temp.name) / 'workspace'
        dry_run.prepare(self.repo, 'case-1', workspace)
        raw = self.text('startup.txt', 'Authentication failed before inference.')
        now = dt.datetime.now(dt.timezone.utc).isoformat()
        value = dry_run.record(self.repo, 'case-1', workspace, raw, 'failed', now, now, 'test-model')
        self.assertIsNone(value['session_id'])
        self.assertEqual((self.root / 'transcripts/raw/case-1.jsonl').read_bytes(), raw.read_bytes())

    def test_reusing_session_across_cases_is_rejected(self):
        self.basis()
        self.record()
        self.items()
        # Duplicate record deliberately retains the first case ID: even changing filenames
        # cannot turn one transcript into independent inference evidence.
        first = json.loads((self.root / 'transcripts/case-1.json').read_text())
        self.write('evals/golden/transcripts/case-2.json', first)
        self.write('evals/golden/inputs/case-2.json', self.case | dict(case_id='case-2'))
        self.assertTrue(any('case/mode' in e for e in inspect_attempt(self.repo, 'case-2', 'dry-run')['errors']))


if __name__ == '__main__':
    unittest.main()
