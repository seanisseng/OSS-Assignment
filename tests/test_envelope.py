"""Grounding checks are structural, never a judgement of blocker necessity."""
import copy
import json
from pathlib import Path
import unittest

from scripts.contract import digest
from scripts.single_response import build_packet, validate_response


class EnvelopeTests(unittest.TestCase):
    def setUp(self):
        self.case = dict(case_id='example', title='Crash', body='pytest crashes.',
                         context={'issue': 'pytest crashes.'})
        self.packet = build_packet(self.case, 'Canonical skill')
        self.value = dict(version=2, assessment=dict(
            supplied_facts=[dict(source='issue', quote='pytest crashes.')], gaps=[]),
            recommendation=dict(case_id='example', input_hash=digest(self.case),
                decision='sufficient', missing=[], evidence=['issue'], reasoning='Investigable.',
                questions=[], comment=''))

    def test_grounded_no_action(self):
        self.assertEqual(validate_response(self.case, self.packet, json.dumps(self.value)), self.value)

    def test_missing_gap_unknown_source_and_invented_quotes_fail(self):
        mutations = [lambda x: x.update(version=True),
            lambda x: x.update(extra=1),
            lambda x: x['assessment']['supplied_facts'][0].update(source='not-delivered'),
            lambda x: x['assessment']['supplied_facts'][0].update(quote='made up'),
            lambda x: x['assessment'].update(supplied_facts=[]),
            lambda x: x['assessment'].update(gaps=[self.gap()])]
        for mutation in mutations:
            value = copy.deepcopy(self.value)
            mutation(value)
            with self.subTest(value=value), self.assertRaises(ValueError):
                validate_response(self.case, self.packet, json.dumps(value))

    def gap(self):
        return dict(question_index=0, category='traceback', missing_fact='Failure diagnostic',
                    investigation_blocker='Cannot identify failing operation', related_fact_indexes=[0])

    def test_each_question_has_one_gap_and_valid_fact_references(self):
        self.value['recommendation'].update(decision='needs_information', missing=['traceback'],
                                           questions=['What traceback appears?'], comment='What traceback appears?')
        self.value['assessment']['gaps'] = [self.gap()]
        validate_response(self.case, self.packet, json.dumps(self.value))
        for change in [dict(question_index=True), dict(question_index=1),
                       dict(category='versions'), dict(related_fact_indexes=[1]),
                       dict(related_fact_indexes=[True]), dict(missing_fact='')]:
            value = copy.deepcopy(self.value)
            value['assessment']['gaps'][0].update(change)
            with self.subTest(change=change), self.assertRaises(ValueError):
                validate_response(self.case, self.packet, json.dumps(value))
        self.value['assessment']['gaps'] *= 2
        with self.assertRaises(ValueError):
            validate_response(self.case, self.packet, json.dumps(self.value))

    def test_duplicate_json_keys_are_not_silently_repaired(self):
        raw = json.dumps(self.value).replace('"version": 2', '"version": 1, "version": 2')
        with self.assertRaises(ValueError):
            validate_response(self.case, self.packet, raw)


if __name__ == '__main__':
    unittest.main()
