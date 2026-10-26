"""Closed output contract. No model-controlled targets or commands."""
import hashlib
import json

CATEGORIES = {'reproducer', 'expected_actual', 'versions', 'traceback', 'configuration'}
FIELDS = {'case_id', 'input_hash', 'decision', 'missing', 'evidence', 'reasoning',
          'questions', 'comment'}
REPOSITORY = 'seanisseng/OSS-Assignment'


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False,
                                    separators=(',', ':')).encode()).hexdigest()


def require(condition, message):
    if not condition:
        raise ValueError(message)


def validate(case, result):
    require(isinstance(result, dict) and set(result) == FIELDS, 'unknown/missing fields')
    for key in ['case_id', 'input_hash', 'decision', 'reasoning', 'comment']:
        require(isinstance(result[key], str), 'invalid string: ' + key)
    for key in ['missing', 'evidence', 'questions']:
        value = result[key]
        require(isinstance(value, list) and all(isinstance(x, str) and x for x in value),
                'invalid list: ' + key)
        require(len(value) == len(set(value)), 'duplicate values')
    require(result['case_id'] == case['case_id'], 'case mismatch')
    require(result['input_hash'] == digest(case), 'input mismatch')
    require(result['decision'] in {'sufficient', 'needs_information', 'human_review'},
            'unknown decision')
    require(set(result['missing']) <= CATEGORIES, 'unknown category')
    require(bool(result['evidence']) and set(result['evidence']) <= set(case['context']),
            'unresolved evidence')
    require(0 < len(result['reasoning'].strip()) <= 2000, 'invalid reasoning')
    require(len(result['comment']) <= 1200, 'comment too long')
    if result['decision'] == 'needs_information':
        require(bool(result['missing']), 'missing categories required')
        require(1 <= len(result['questions']) <= 3, 'one to three questions required')
        require(all(q.endswith('?') and q.count('?') == 1 for q in result['questions']),
                'each question must be a single question')
        require(result['comment'] == '\n'.join(result['questions']), 'comment mismatch')
    else:
        require(not result['comment'] and not result['questions'] and not result['missing'],
                'no-action decisions cannot request information')
    return result


def authorize(*, repository, issue, allowed, enabled, approved_hash, result,
              existing, today_count, age_hours):
    require(repository == REPOSITORY, 'foreign repository')
    require(type(issue) is int and issue in allowed, 'issue not allowlisted')
    require(enabled is True, 'operation disabled')
    require(approved_hash == digest(result), 'exact recommendation not approved')
    require(result['decision'] == 'needs_information', 'nothing to publish')
    require(result['input_hash'] not in existing, 'duplicate input revision')
    require(0 <= today_count < 5, 'daily publication cap')
    require(0 <= age_hours <= 24, 'stale artifact')
    return True


def admit(attempts, enabled):
    return enabled is True and type(attempts) is int and 0 <= attempts < 40
