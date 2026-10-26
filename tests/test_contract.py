import copy
import unittest

from scripts.contract import digest, validate, authorize


class ContractTests(unittest.TestCase):
    def setUp(self):
        self.case = {'case_id': 'case-1', 'context': {'issue': 'A traceback'},
                     'title': 'crash', 'body': 'Steps'}
        self.result = dict(case_id='case-1', input_hash=digest(self.case),
                           decision='needs_information', missing=['reproducer'],
                           evidence=['issue'], reasoning='Cannot reproduce.',
                           questions=['Could you share a minimal reproducer?'],
                           comment='Could you share a minimal reproducer?')

    def test_valid(self):
        self.assertEqual(validate(self.case, self.result), self.result)

    def test_reject_mutations(self):
        changes = [dict(decision='close'), dict(repository='foreign/repo'),
                   dict(input_hash='stale'), dict(evidence=['unknown']),
                   dict(missing=['everything']), dict(comment='x' * 1201),
                   dict(questions=['a?', 'b?', 'c?', 'd?']), dict(decision='sufficient'),
                   dict(decision='human_review'), dict(comment='different'),
                   dict(questions=[]), dict(reasoning=''), dict(evidence=[])]
        for change in changes:
            with self.subTest(change=change), self.assertRaises(ValueError):
                validate(self.case, self.result | change)

    def test_no_action(self):
        for decision in ['sufficient', 'human_review']:
            validate(self.case, self.result | dict(decision=decision, missing=[],
                                                  questions=[], comment=''))

    def test_types(self):
        for key in self.result:
            bad = copy.deepcopy(self.result)
            bad[key] = None
            with self.subTest(key=key), self.assertRaises(ValueError):
                validate(self.case, bad)

    def test_publication_boundaries(self):
        args = dict(repository='seanisseng/OSS-Assignment', issue=1, allowed=[1],
                    enabled=True, approved_hash=digest(self.result), result=self.result,
                    existing=[], today_count=0, age_hours=1)
        self.assertTrue(authorize(**args))
        for change in [dict(repository='pytest-dev/pytest'), dict(issue=2),
                       dict(enabled=False), dict(approved_hash='other'),
                       dict(existing=[self.result['input_hash']]), dict(today_count=5),
                       dict(age_hours=25), dict(age_hours=-1)]:
            with self.subTest(change=change), self.assertRaises(ValueError):
                authorize(**(args | change))

    def test_burst(self):
        from scripts.contract import admit
        accepted = sum(admit(i, True) for i in range(300))
        self.assertEqual(accepted, 40)
        self.assertFalse(admit(0, False))


if __name__ == '__main__':
    unittest.main()
