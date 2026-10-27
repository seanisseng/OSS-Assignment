"""Evidence completeness is independent of model accuracy."""
import json
from pathlib import Path
import tempfile
import unittest

from scripts import dry_run
from scripts.contract import digest
from scripts.evidence import configuration_hash, file_hash, inspect_attempt, review_record
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
        dry_run.record(self.repo, 'case-1', workspace, raw, status,
                       '2026-02-01T00:00:00+00:00', '2026-02-01T00:01:00+00:00', 'test-model')
        self.write('evals/golden/assessments/case-1.json', dict(case_id='case-1', reviewer='student',
                   reviewed_at='2026-02-02T00:00:00+00:00', relevance='Invalid response',
                   redundancy='Not applicable', procedure='Skill read, output invalid',
                   explanation='The attempt failed and is preserved.', safety='No harmful action observed'))

    def test_export_excludes_expectations_history_and_credentials(self):
        workspace = Path(self.temp.name) / 'workspace'
        dry_run.prepare(self.repo, 'case-1', workspace)
        files = {p.relative_to(workspace).as_posix() for p in workspace.rglob('*') if p.is_file()}
        self.assertEqual(files, {'AGENTS.md', 'input/case.json', 'input/manifest.json',
                                '.github/skills/bug-report-clarification/SKILL.md', 'prompt.md'})
        with self.assertRaises(ValueError):
            dry_run.prepare(self.repo, '../escape', workspace)
        with self.assertRaises(FileExistsError):
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


if __name__ == '__main__':
    unittest.main()
