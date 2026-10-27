"""Mechanical scoring against predeclared alternatives and text checklists."""
import re


def accepted_decisions(item):
    return item.get('acceptable_decisions', [item['decision']])


def checks_pass(checks, text):
    return all(all(re.search(pattern, text, re.I | re.S) is not None
                   for pattern in check['patterns']) for check in checks)


def decision_match(item, actual):
    decision = actual.get('decision')
    if decision not in accepted_decisions(item):
        return False
    checks = item.get('alternative_checks', {}).get(decision, [])
    return checks_pass(checks, actual.get('reasoning', ''))


def category_reference(item, predicted):
    options = item.get('acceptable_missing_sets', [item['acceptable_missing']])
    def key(values):
        reference = set(values)
        denominator = len(predicted) + len(reference)
        f1 = 2 * len(predicted & reference) / denominator if denominator else 1
        return (-f1, len(reference), tuple(sorted(reference)))
    return set(min(options, key=key))


def category_scores(item, actual):
    predicted = set(actual.get('missing', []))
    questions = '\n'.join(actual.get('questions', []))
    invalid = {name for name in predicted if not checks_pass(item.get('category_checks', {}).get(name, []), questions)}
    invalid.update(name for name in predicted if name in item.get('category_requires_any', {})
                   and not predicted.intersection(item['category_requires_any'][name]))
    eligible = predicted - invalid
    best = category_reference(item, eligible)
    primary = set(item.get('primary_missing', item['acceptable_missing']))
    def counts(reference):
        return dict(tp=len(eligible & reference), fp=len((predicted - reference) | invalid),
                    fn=len(reference - eligible))
    bundles = item.get('acceptable_missing_sets', [item['acceptable_missing']])
    return dict(best=counts(best), primary=counts(primary), reference=sorted(best),
                invalid_categories=sorted(invalid), bundle_match=not invalid and any(predicted == set(x) for x in bundles))


def class_results(rows):
    result = {}
    for name in ['sufficient', 'needs_information', 'human_review']:
        tp = sum(r['expected'] == name and r['prediction'] == name for r in rows)
        fp = sum(r['expected'] != name and r['prediction'] == name for r in rows)
        fn = sum(r['expected'] == name and r['prediction'] != name for r in rows)
        result[name] = dict(tp=tp, fp=fp, fn=fn, support=tp + fn,
                            precision=tp / (tp + fp) if tp + fp else None,
                            recall=tp / (tp + fn) if tp + fn else None)
    return result


def apply_review_conditions(item):
    """Serialize the user-requested checks into the key before any inference."""
    if item['case_id'] == 'pytest-13902':
        item['alternative_checks'] = {'human_review': [
            dict(name='Names the documentation colour discrepancy', patterns=[
                r'\bdoc(?:s|umentation)?\b', r'\bcolou?rs?\b',
                r'\b(?:discrepanc\w*|mismatch\w*|incorrect|different|green|mixed)\b']),
            dict(name='Separates symbol choice as a design question', patterns=[
                r'\b(?:symbols?|glyphs?)\b',
                r'\bseparate\b[^.!?\n]*\bdesign\b|\bdesign\b[^.!?\n]*\bseparate\b'])]}
        item['alternative_rationale'] = ('human_review earns alternative credit only if both frozen '
            'reasoning checks pass. Primary remains sufficient. Regex checks are lexical proxies, '
            'not proof of semantic correctness; report human assessment separately.')
    if item['case_id'] == 'pytest-13634':
        item['acceptable_missing'] = ['traceback', 'configuration', 'reproduction_detail']
        item['primary_missing'] = ['traceback', 'configuration']
        item['category_requires_any'] = {'reproduction_detail': ['traceback', 'configuration']}
        item['acceptable_missing_sets'] = [['traceback'], ['configuration'], ['traceback', 'configuration'],
            ['traceback', 'reproduction_detail'], ['configuration', 'reproduction_detail'],
            ['traceback', 'configuration', 'reproduction_detail']]
        item['category_checks'] = {'reproduction_detail': [dict(
            name='Question names a specific missing import, fixture, layout or invocation detail',
            patterns=[r'\b(?:imports?|importing|fixtures?|directory|layout|invocation|command|rootdir|conftest(?:\.py)?|watthouse(?:\.conftest)?|pythonpath|sys\.path)\b'])]}
        item['redundancy_check'] = ('reproduction_detail alone is not a valid bundle. A generic minimal '
            'reproducer request without a named specific detail fails the frozen question-text check. '
            'Unknown/irrelevant categories and failed detail checks count as false positives.')
    return item
