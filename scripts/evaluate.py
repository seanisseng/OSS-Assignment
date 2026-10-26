"""Reproduce metrics and an escaped local dashboard; absent runs are never successes."""
import html
import json
from pathlib import Path
import re
import statistics

from scripts.collect import save
from scripts.contract import validate


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


def evaluate(root):
    expected = json.loads((root / 'expectations.json').read_text(encoding='utf-8'))['expectations']
    rows = []
    tp = fp = fn = correct = completed = abstained = unnecessary = no_action = 0
    for item in expected:
        case_id = item['case_id']
        case = json.loads((root / f'inputs/{case_id}.json').read_text(encoding='utf-8'))
        row = dict(case_id=case_id, split=item['split'], expected=item['decision'],
                   baseline=baseline(case), actual=None, validation='not run', disagreement=None)
        actual_path = root / f'actual/{case_id}.json'
        if actual_path.exists():
            actual = {}
            try:
                actual = json.loads(actual_path.read_text(encoding='utf-8'))
                validate(case, actual)
                row['validation'] = 'valid'
                row['actual'] = actual
            except ValueError as error:
                row['validation'] = str(error)
            if not isinstance(actual, dict):
                actual = {}
            if item['split'] == 'held-out':
                completed += 1
                valid = row['validation'] == 'valid'
                correct += valid and actual.get('decision') == item['decision']
                abstained += valid and actual['decision'] == 'human_review'
                if item['decision'] != 'needs_information':
                    no_action += 1
                    unnecessary += valid and actual['decision'] == 'needs_information'
                predicted = set(actual.get('missing', [])) if valid else set()
                wanted = set(item['acceptable_missing'])
                tp += len(predicted & wanted)
                fp += len(predicted - wanted)
                fn += len(wanted - predicted)
            if row['validation'] != 'valid' or actual.get('decision') != item['decision']:
                row['disagreement'] = 'Human explanation required; do not tune against this held-out case.'
        rows.append(row)
    held = [r for r in rows if r['split'] == 'held-out']
    return dict(rows=rows, metrics=dict(held_out_attempted=completed, held_out_total=10,
        decision_matches=correct, decision_accuracy=correct / completed if completed else None,
        unnecessary_comments=unnecessary, no_action_attempted=no_action,
        unnecessary_comment_rate=unnecessary / no_action if no_action else None,
        category_precision=tp / (tp + fp) if tp + fp else None,
        category_recall=tp / (tp + fn) if tp + fn else None,
        category_counts=dict(tp=tp, fp=fp, fn=fn), abstentions=abstained,
        baseline_matches=sum(r['baseline']['decision'] == r['expected'] for r in held),
        human_relevance_redundancy='pending student assessment', runtime_usage='no inference run'))


def main():
    root = Path('evals/golden')
    result = evaluate(root)
    save(root / 'report.json', result)
    rows = ''.join('<tr>' + ''.join('<td>' + html.escape(str(row[k])) + '</td>'
           for k in ['case_id', 'split', 'expected', 'actual', 'baseline', 'validation']) + '</tr>'
           for row in result['rows'])
    document = '<!doctype html><meta charset="utf-8"><title>Clarification evaluation</title>'
    document += '<style>body{font:16px system-ui;max-width:1200px;margin:40px auto;padding:16px}td,th{padding:12px;border:1px solid #bbb;vertical-align:top}table{border-collapse:collapse}pre{white-space:pre-wrap}</style>'
    document += '<h1>Pytest clarification evaluation</h1><p>No inference evidence means not run, never a passing score.</p>'
    document += '<pre>' + html.escape(json.dumps(result['metrics'], indent=2)) + '</pre>'
    document += '<p><a href="expectations.json">Expectations</a> · <a href="audit/summary.json">Audit</a> · <a href="../evidence/verification.md">Control evidence</a></p>'
    document += '<table><tr><th>Case</th><th>Split</th><th>Expected</th><th>Actual</th><th>Baseline</th><th>Validation</th></tr>' + rows + '</table>'
    (root / 'dashboard.html').write_text(document, encoding='utf-8')
    expectations = json.loads((root / 'expectations.json').read_text(encoding='utf-8'))['expectations']
    review = '<!doctype html><meta charset="utf-8"><title>Review expected outcomes</title>'
    review += '<style>body{font:17px system-ui;max-width:960px;margin:40px auto;padding:20px}article{border-top:1px solid #aaa;padding:24px 0}pre{white-space:pre-wrap;overflow-wrap:anywhere;background:#f5f5f5;padding:16px}li{margin:12px}</style>'
    review += '<h1>Review the 15 expected outcomes</h1><p>These are AI-assisted drafts, not independently human-authored ground truth. No model results are shown.</p>'
    review += '<p>For each case, read the original report below. Decide whether a maintainer can begin investigating, whether one essential detail blocks investigation, or whether uncertainty/scope needs human judgement. Check that requested categories are essential and avoid demanding every template field.</p>'
    review += '<p>Approve the rubric, or report the case number and your preferred decision/reason. This review does not authorize a push, spending or publication.</p>'
    for item in expectations:
        case = json.loads((root / f"inputs/{item['case_id']}.json").read_text(encoding='utf-8'))
        review += '<article><h2>' + html.escape(item['case_id'] + ': ' + case['title']) + '</h2>'
        review += '<p>Expected: <strong>' + html.escape(item['decision']) + '</strong>; missing categories: ' + html.escape(str(item['acceptable_missing'])) + '</p>'
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
    main()
