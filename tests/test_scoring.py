"""Regression checks for frozen alternatives, not post-hoc leniency."""
import unittest

from scripts.evaluate import accepted_decisions, category_reference


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


if __name__ == '__main__':
    unittest.main()
