"""Reproduce metrics and an escaped local dashboard; absent runs are never successes."""
import html
import argparse
import json
from pathlib import Path
import re
import statistics

from scripts.collect import save
from scripts.contract import validate
from scripts.scoring import accepted_decisions, category_reference, category_scores, class_results, decision_match


def baseline(case):
    body = case['body'].lower()
    missing = []
    if '```' not in body:
        missing.append('reproducer')
    if not re.search(r'pytest[\s=v-]*\d|commit|current main', body):
        missing.append('versions')
    if not re.search(r'expect|should|instead|error|crash|fails', body):
        missing.append('expected_actual')
    return dict(decision='needs_information' if missing else 'sufficient', missing=missing)


def attempt(root, case_id, case, mode=None):
    """A transcript without output still records a failed/interrupted attempt."""
    path = root / f'actual/{case_id}.json'
    transcript = root / f'transcripts/{case_id}.json'
    if mode == 'single-response' and transcript.exists():
        from scripts.hosted_evidence import inspect_attempt
        checked = inspect_attempt(root.parent.parent, case_id)
        # Human review is reported separately; native evidence failures prevent credit.
        provenance_errors = [x for x in checked['errors'] if not x.startswith('Case review:')]
        if provenance_errors:
            return {}, '; '.join(provenance_errors)
        if checked['validation'] != 'valid':
            return {}, checked['validation']
    if not path.exists():
        if transcript.exists():
            try:
                status = json.loads(transcript.read_text(encoding='utf-8')).get('status', 'unknown')
            except (ValueError, AttributeError):
                status = 'invalid transcript'
            return {}, status + ': no output'
        return {}, 'not run'
    try:
        actual = json.loads(path.read_text(encoding='utf-8'))
        validate(case, actual)
        if transcript.exists():
            record = json.loads(transcript.read_text(encoding='utf-8'))
            if record.get('status') != 'completed':
                return actual, str(record.get('status', 'unknown')) + ': output retained'
        return actual, 'valid'
    except (ValueError, KeyError, TypeError) as error:
        return {}, str(error)


def adversarial_results(root, mode=None):
    rows = []
    for path in sorted((root / 'adversarial').glob('*.json')):
        expected = json.loads(path.read_text(encoding='utf-8'))
        case_id = expected['case_id']
        case = json.loads((root / f'inputs/{case_id}.json').read_text(encoding='utf-8'))
        actual, validation = attempt(root, case_id, case, mode)
        rows.append(dict(case_id=case_id, expected=expected['expected_decision'], actual=actual or None,
                         validation=validation, decision_match=validation == 'valid' and
                         actual.get('decision') == expected['expected_decision'],
                         safety='Human tool-trace assessment required; decision match alone is not resistance.',
                         executor='Separate deterministic/mocked tests; no remote publication claim.'))
    return rows


def evaluate(root, mode=None):
    expected = json.loads((root / 'expectations.json').read_text(encoding='utf-8'))['expectations']
    rows = []
    tp = fp = fn = correct = primary_correct = completed = abstained = unnecessary = no_action = 0
    primary_categories = dict(tp=0, fp=0, fn=0)
    for item in expected:
        case_id = item['case_id']
        case = json.loads((root / f'inputs/{case_id}.json').read_text(encoding='utf-8'))
        row = dict(case_id=case_id, split=item['split'], expected=item['decision'],
                   synthetic=item.get('synthetic', False),
                   acceptable_decisions=accepted_decisions(item),
                   baseline=baseline(case), actual=None, validation='not run', disagreement=None)
        actual, row['validation'] = attempt(root, case_id, case, mode)
        if row['validation'] != 'not run':
            row['actual'] = actual or None
            row['decision_match'] = row['validation'] == 'valid' and decision_match(item, actual)
            row['primary_decision_match'] = row['validation'] == 'valid' and actual.get('decision') == item['decision']
            row['alternative_credit'] = row['decision_match'] and not row['primary_decision_match']
            if item['split'] == 'held-out':
                completed += 1
                valid = row['validation'] == 'valid'
                primary_correct += valid and actual.get('decision') == item['decision']
                correct += row['decision_match']
                abstained += valid and actual['decision'] == 'human_review'
                if 'needs_information' not in accepted_decisions(item):
                    no_action += 1
                    unnecessary += valid and actual['decision'] == 'needs_information'
                scores = category_scores(item, actual if valid else {})
                row['category_reference'] = scores['reference']
                row['category_scores'] = scores
                tp += scores['best']['tp']
                fp += scores['best']['fp']
                fn += scores['best']['fn']
                for key in primary_categories:
                    primary_categories[key] += scores['primary'][key]
            if not row['decision_match']:
                row['disagreement'] = 'Human explanation required; do not tune against this held-out case.'
        rows.append(row)
    held = [r for r in rows if r['split'] == 'held-out']
    synthetic_diagnostics = [r for r in rows if r['synthetic']]
    attacks = adversarial_results(root, mode)
    assessed = sum((root / f"assessments/{r['case_id']}.json").exists() for r in rows + attacks)
    real = [r for r in rows if not r['synthetic']]
    attempted_real = [r for r in real if r['validation'] != 'not run']
    def class_rows(values, predictor):
        return [dict(expected=r['expected'], prediction=predictor(r)) for r in values]
    prediction = lambda r: r['actual']['decision'] if r['validation'] == 'valid' else 'invalid_or_missing'
    baselines = {}
    for name, values in [('all_real', real), ('held_out', held)]:
        baselines[name] = dict(total=len(values),
            always_sufficient_primary_matches=sum(r['expected'] == 'sufficient' for r in values),
            always_sufficient_per_class=class_results(class_rows(values, lambda r: 'sufficient')),
            checklist_primary_matches=sum(r['baseline']['decision'] == r['expected'] for r in values),
            checklist_per_class=class_results(class_rows(values, lambda r: r['baseline']['decision'])))
    groups = {}
    for name, values in [('real_all', real), ('real_development', [r for r in real if r['split']=='development']),
                         ('real_held_out', held), ('diagnostics', synthetic_diagnostics)]:
        counts = dict(tp=0, fp=0, fn=0)
        for row in values:
            if row['validation'] == 'not run':
                continue
            item = next(x for x in expected if x['case_id'] == row['case_id'])
            scores = category_scores(item, row['actual'] if row['validation']=='valid' else {})['primary']
            for key in counts:
                counts[key] += scores[key]
        no_action_rows = [r for r in values if 'needs_information' not in r['acceptable_decisions']]
        groups[name] = dict(total=len(values), attempted=sum(r['validation']!='not run' for r in values),
            valid=sum(r['validation']=='valid' for r in values),
            decision_matches=sum(r.get('decision_match',False) for r in values),
            primary_matches=sum(r.get('primary_decision_match',False) for r in values),
            abstentions=sum(prediction(r)=='human_review' for r in values),
            unnecessary_clarification=sum(prediction(r)=='needs_information' for r in no_action_rows),
            no_action_total=len(no_action_rows), category_counts=counts,
            category_precision=counts['tp']/(counts['tp']+counts['fp']) if counts['tp']+counts['fp'] else None,
            category_recall=counts['tp']/(counts['tp']+counts['fn']) if counts['tp']+counts['fn'] else None)
    return dict(rows=rows, adversarial=attacks, baselines=baselines, groups=groups,
        evidence_mode=mode or 'legacy', metrics=dict(held_out_attempted=completed, held_out_total=len(held),
        primary_decision_matches=primary_correct,
        decision_matches=correct,
        per_class=class_results(class_rows(attempted_real, prediction)),
        held_out_per_class=class_results(class_rows([r for r in held if r['validation'] != 'not run'], prediction)),
        real_not_run=len(real) - len(attempted_real),
        unnecessary_comments=unnecessary, no_action_attempted=no_action,
        unnecessary_comment_rate=unnecessary / no_action if no_action else None,
        category_precision=tp / (tp + fp) if tp + fp else None,
        category_recall=tp / (tp + fn) if tp + fn else None,
        category_counts=dict(tp=tp, fp=fp, fn=fn), abstentions=abstained,
        primary_category_counts=primary_categories,
        primary_category_precision=primary_categories['tp'] / (primary_categories['tp'] + primary_categories['fp']) if primary_categories['tp'] + primary_categories['fp'] else None,
        primary_category_recall=primary_categories['tp'] / (primary_categories['tp'] + primary_categories['fn']) if primary_categories['tp'] + primary_categories['fn'] else None,
        baseline_primary_matches=sum(r['baseline']['decision'] == r['expected'] for r in held),
        baseline_matches=sum(r['baseline']['decision'] in r['acceptable_decisions'] for r in held),
        synthetic_diagnostic_total=len(synthetic_diagnostics),
        synthetic_diagnostic_attempted=sum(r['validation'] != 'not run' for r in synthetic_diagnostics),
        synthetic_diagnostic_matches=sum(r.get('decision_match', False) for r in synthetic_diagnostics),
        adversarial_total=len(attacks),
        adversarial_attempted=sum(r['validation'] != 'not run' for r in attacks),
        adversarial_matches=sum(r['decision_match'] for r in attacks),
        assessment_files_present=assessed,
        human_relevance_redundancy='See assessments; content checked by submission gate, not file count.',
        runtime_usage='see per-case transcripts; usage not parsed' if any(r['validation'] != 'not run' for r in rows + attacks) else 'no inference run'))


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--mode', choices=['legacy', 'single-response'], default='legacy')
    args = parser.parse_args([] if argv is None else argv)
    root = Path('evals/golden')
    result = evaluate(root, None if args.mode == 'legacy' else args.mode)
    save(root / 'report.json', result)
    rows = ''.join('<tr>' + ''.join('<td>' + html.escape(str(row[k])) + '</td>'
        for k in ['case_id', 'split', 'expected', 'acceptable_decisions', 'actual', 'baseline', 'validation']) + '</tr>'
           for row in result['rows'])
    document = '<!doctype html><meta charset="utf-8"><title>Clarification evaluation</title>'
    document += '<style>body{font:16px system-ui;max-width:1200px;margin:40px auto;padding:16px}td,th{padding:12px;border:1px solid #bbb;vertical-align:top}table{border-collapse:collapse}pre{white-space:pre-wrap}</style>'
    document += '<h1>Pytest clarification evaluation</h1><p>No inference evidence means not run, never a passing score.</p>'
    document += '<pre>' + html.escape(json.dumps(result['metrics'], indent=2)) + '</pre>'
    document += '<h2>Baselines and per-class results</h2><pre>' + html.escape(json.dumps(result['baselines'], indent=2)) + '</pre>'
    document += '<p><a href="expectations.json">Expectations</a> · <a href="audit/summary.json">Audit</a> · <a href="../evidence/verification.md">Control evidence</a></p>'
    document += '<table><tr><th>Case</th><th>Split</th><th>Primary</th><th>Accepted</th><th>Actual</th><th>Baseline</th><th>Validation</th></tr>' + rows + '</table>'
    document += '<h2>Adversarial decisions (separate from historical accuracy)</h2>'
    document += '<p>Decision matches do not prove resistance. Inspect tool traces and human safety assessments.</p>'
    document += '<pre>' + html.escape(json.dumps(result['adversarial'], indent=2)) + '</pre>'
    (root / 'dashboard.html').write_text(document, encoding='utf-8')
    expectations = json.loads((root / 'expectations.json').read_text(encoding='utf-8'))['expectations']
    review = '<!doctype html><meta charset="utf-8"><title>Review expected outcomes</title>'
    review += '<style>body{font:17px system-ui;max-width:960px;margin:40px auto;padding:20px}article{border-top:1px solid #aaa;padding:24px 0}pre{white-space:pre-wrap;overflow-wrap:anywhere;background:#f5f5f5;padding:16px}li{margin:12px}</style>'
    review += '<h1>Review 15 real cases and 3 synthetic diagnostics</h1><p>The rubric was revised after user-supplied AI critique; it is not independent human ground truth. No model results are shown. Rule A: a clearly specified change or docs bug can be sufficient, regardless of whether maintainers accept it.</p>'
    review += '<p>For each case, read the original report below. Decide whether a maintainer can begin investigating, whether one essential detail blocks investigation, or whether uncertainty/scope needs human judgement. Check that requested categories are essential and avoid demanding every template field.</p>'
    review += '<p>Approve the rubric, or report the case number and your preferred decision/reason. This review does not authorize a push, spending or publication.</p>'
    for item in expectations:
        case = json.loads((root / f"inputs/{item['case_id']}.json").read_text(encoding='utf-8'))
        review += '<article><h2>' + html.escape(item['case_id'] + ': ' + case['title']) + '</h2>'
        review += '<p>Expected: <strong>' + html.escape(item['decision']) + '</strong>; missing categories: ' + html.escape(str(item['acceptable_missing'])) + '</p>'
        review += '<p>Accepted decisions: ' + html.escape(str(accepted_decisions(item))) + '; synthetic: ' + str(item.get('synthetic', False)) + '; split: ' + html.escape(item['split']) + '</p>'
        review += '<p>Valid category bundles: ' + html.escape(str(item.get('acceptable_missing_sets', [item['acceptable_missing']]))) + '</p>'
        review += '<p>Primary category bundle: ' + html.escape(str(item.get('primary_missing', item['acceptable_missing']))) + '</p>'
        if item.get('alternative_checks') or item.get('category_checks'):
            review += '<pre>' + html.escape(json.dumps(dict(alternative_checks=item.get('alternative_checks', {}),
                category_checks=item.get('category_checks', {})), indent=2)) + '</pre>'
        escaped_body = html.escape(case['body']).replace('\r', '&#13;').replace('\n', '&#10;')
        review += '<p>Reason: ' + html.escape(item['rationale']) + '</p><details><summary>Read original report body</summary><pre>' + escaped_body + '</pre></details></article>'
    (root / 'review.html').write_text(review, encoding='utf-8')
    observations = json.loads((root / 'audit/observations.json').read_text())
    times = [x['first_response_hours'] for x in observations if x['first_response_hours'] is not None]
    save(root / 'audit/summary.json', dict(denominator=len(observations), responded=len(times),
         unresolved=len(observations) - len(times), median_responded_hours=statistics.median(times),
         created_from=min(x['created_at'] for x in observations),
         created_to=max(x['created_at'] for x in observations),
         clarification_coding='AI-assisted draft; student review pending',
         clarification_issue_numbers=[13634, 13835, 13885], clarification_count=3))
    print(json.dumps(result['metrics'], indent=2))


if __name__ == '__main__':
    import sys
    main(sys.argv[1:])
