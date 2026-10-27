"""Regression checks for frozen alternatives, not post-hoc leniency."""
import unittest
import contextlib
import io
import json
from pathlib import Path
import tempfile

from scripts.evaluate import accepted_decisions, category_reference, evaluate, main
from scripts.contract import digest


class ScoringTests(unittest.TestCase):
    def test_primary_is_default(self):
        self.assertEqual(accepted_decisions({'decision': 'sufficient'}), ['sufficient'])

    def test_explicit_alternative(self):
        item = {'decision': 'sufficient', 'acceptable_decisions': ['sufficient', 'human_review']}
        self.assertIn('human_review', accepted_decisions(item))
        self.assertNotIn('needs_information', accepted_decisions(item))

    def test_optional_gaps_are_not_all_required(self):
        item = {'acceptable_missing': ['traceback', 'configuration', 'reproducer'],
                'acceptable_missing_sets': [['traceback'], ['configuration'],
                                            ['traceback', 'configuration']]}
        self.assertEqual(category_reference(item, {'configuration'}), {'configuration'})
        self.assertEqual(category_reference(item, {'traceback', 'configuration'}),
                         {'traceback', 'configuration'})

    def test_irrelevant_category_still_penalized(self):
        item = {'acceptable_missing': ['traceback'], 'acceptable_missing_sets': [['traceback']]}
        reference = category_reference(item, {'traceback', 'versions'})
        self.assertEqual({'traceback', 'versions'} - reference, {'versions'})
        self.assertEqual(reference - set(), {'traceback'})

    def test_legacy_single_reference(self):
        self.assertEqual(category_reference({'acceptable_missing': []}, set()), set())

    def fixture(self, root):
        def write(path, value):
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(json.dumps(value), encoding='utf-8')
        cases = [dict(case_id='gap', title='Crash', body='It crashes', context={'issue': 'crash'}),
                 dict(case_id='borderline', title='Docs', body='```example``` pytest 8 expected error', context={'issue': 'docs'})]
        items = [dict(case_id='gap', split='held-out', decision='needs_information', rationale='missing diagnostic', acceptable_missing=['traceback', 'configuration'], acceptable_missing_sets=[['traceback'], ['configuration']]),
                 dict(case_id='borderline', split='held-out', decision='human_review', rationale='borderline', acceptable_decisions=['sufficient', 'human_review'], acceptable_missing=[])]
        write(root / 'expectations.json', {'expectations': items})
        for case in cases:
            write(root / 'inputs' / (case['case_id'] + '.json'), case)
        write(root / 'audit/observations.json', [dict(first_response_hours=2, created_at='2024-01-01'), dict(first_response_hours=None, created_at='2024-01-02')])
        return cases, write

    def result(self, case, decision):
        needs = decision == 'needs_information'
        return dict(case_id=case['case_id'], input_hash=digest(case), decision=decision,
                    missing=['traceback'] if needs else [], evidence=['issue'], reasoning='Investigable gap.',
                    questions=['Could you share the traceback?'] if needs else [],
                    comment='Could you share the traceback?' if needs else '')

    def test_full_metrics_count_alternatives_and_optional_categories(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            cases, write = self.fixture(root)
            for case, decision in zip(cases, ['needs_information', 'sufficient']):
                write(root / 'actual' / (case['case_id'] + '.json'), self.result(case, decision))
            metrics = evaluate(root)['metrics']
            self.assertEqual(metrics['decision_matches'], 2)
            self.assertEqual(metrics['primary_decision_matches'], 1)
            self.assertEqual(metrics['category_recall'], 1)
            self.assertEqual(metrics['category_precision'], 1)
            self.assertEqual(metrics['unnecessary_comment_rate'], 0)
            write(root / 'actual/borderline.json', self.result(cases[1], 'needs_information'))
            self.assertEqual(evaluate(root)['metrics']['unnecessary_comment_rate'], 1)
            (root / 'actual/borderline.json').write_text('not json')
            invalid = evaluate(root)
            self.assertEqual(invalid['metrics']['held_out_attempted'], 2)
            self.assertEqual(invalid['metrics']['decision_matches'], 1)
            self.assertIsNotNone(invalid['rows'][1]['disagreement'])

    def test_reports_keep_absence_and_escape_untrusted_body(self):
        with tempfile.TemporaryDirectory() as temp, contextlib.chdir(temp):
            root = Path('evals/golden')
            cases, write = self.fixture(root)
            cases[0]['body'] = '<script>alert(1)</script>'
            write(root / 'inputs/gap.json', cases[0])
            with contextlib.redirect_stdout(io.StringIO()):
                main()
            report = json.loads((root / 'report.json').read_text())
            self.assertEqual(report['metrics']['real_not_run'], 2)
            self.assertIsNone(report['metrics']['per_class']['needs_information']['recall'])
            review = (root / 'review.html').read_text(encoding='utf-8')
            self.assertIn('&lt;script&gt;', review)
            self.assertNotIn('<script>', review)
            self.assertTrue((root / 'dashboard.html').exists())


if __name__ == '__main__':
    unittest.main()
