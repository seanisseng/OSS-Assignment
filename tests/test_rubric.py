"""Pre-inference conditional credit must be reproducible from the frozen key."""
import json
from pathlib import Path
import unittest

from scripts.scoring import category_scores, decision_match, class_results


class RubricTests(unittest.TestCase):
    def item(self, case_id):
        items = json.loads(Path('evals/golden/expectations.json').read_text(encoding='utf-8'))['expectations']
        return next(i for i in items if i['case_id'] == case_id)

    def test_13902_requires_both_checklist_items(self):
        item = self.item('pytest-13902')
        good = dict(decision='human_review', reasoning='The docs colour discrepancy is concrete. Symbol choice is a separate design question.')
        self.assertTrue(decision_match(item, good))
        for reason in ['This is a feature request.', 'The docs colour discrepancy needs investigation.',
                       'Symbol choice is a separate design question.']:
            self.assertFalse(decision_match(item, good | dict(reasoning=reason)))
        self.assertTrue(decision_match(item, dict(decision='sufficient', reasoning='Investigable.')))

    def test_13634_primary_and_optional_bundle_scores_differ(self):
        item = self.item('pytest-13634')
        result = category_scores(item, dict(missing=['traceback'], questions=['Could you share the traceback?']))
        self.assertEqual(result['best'], dict(tp=1, fp=0, fn=0))
        self.assertEqual(result['primary'], dict(tp=1, fp=0, fn=1))
        self.assertTrue(result['bundle_match'])

    def test_reproduction_detail_is_specific_and_never_valid_alone(self):
        item = self.item('pytest-13634')
        generic = category_scores(item, dict(missing=['traceback', 'reproduction_detail'],
                   questions=['Could you provide the traceback?', 'Could you provide a minimal reproducer?']))
        self.assertEqual(generic['best']['fp'], 1)
        self.assertFalse(generic['bundle_match'])
        specific = dict(missing=['traceback', 'reproduction_detail'],
                        questions=['Could you show the imports of watthouse.conftest in the failing test layout?'])
        result = category_scores(item, specific)
        self.assertEqual(result['best'], dict(tp=2, fp=0, fn=0))
        self.assertEqual(result['primary'], dict(tp=1, fp=1, fn=1))
        self.assertTrue(result['bundle_match'])
        alone = category_scores(item, specific | dict(missing=['reproduction_detail']))
        self.assertFalse(alone['bundle_match'])
        self.assertEqual(alone['best']['fp'], 1)
        outside = category_scores(item, specific | dict(missing=['traceback', 'versions']))
        self.assertEqual(outside['best']['fp'], 1)

    def test_per_class_exposes_majority_baseline(self):
        rows = [dict(expected='sufficient', prediction='sufficient'),
                dict(expected='needs_information', prediction='sufficient'),
                dict(expected='human_review', prediction='sufficient')]
        classes = class_results(rows)
        self.assertEqual(classes['sufficient']['precision'], 1 / 3)
        self.assertEqual(classes['needs_information']['recall'], 0)
        self.assertEqual(classes['human_review']['recall'], 0)

    def test_13403_context_does_not_include_linked_discussion(self):
        case = json.loads(Path('evals/golden/inputs/pytest-13403.json').read_text(encoding='utf-8'))
        self.assertEqual(set(case['context']), {'issue', 'pyproject.toml', 'src/_pytest/assertion/rewrite.py',
                                               'src/_pytest/fixtures.py', 'src/_pytest/python.py'})
        self.assertEqual(case['context']['issue'], case['title'] + '\n\n' + case['body'])
        self.assertIn('issuecomment-2802869441', case['body'])
        workflow = Path('.github/workflows/clarify.md').read_text(encoding='utf-8')
        self.assertIn('network:\n  allowed: []', workflow)
        self.assertIn('github: false', workflow)


if __name__ == '__main__':
    unittest.main()
