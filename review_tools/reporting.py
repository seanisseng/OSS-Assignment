"""Report coverage and correctness separately; never pool recovery accuracy."""
import json
import html
from pathlib import Path

from scripts.evidence import load


def measurements(rows):
    attempted = [r for r in rows if r['hosted'] == 'attempted']
    received = [r for r in attempted if r['validation'] != 'no assistant response']
    valid = [r for r in attempted if r['validation'] == 'valid']
    held = [r for r in rows if r['group'] == 'real held-out']
    held_valid = [r for r in held if r['validation'] == 'valid']
    recovery = [r['recovery'] for r in rows if r['recovery']]
    return dict(hosted=dict(total=len(rows), attempted=len(attempted), responses=len(received), valid=len(valid),
        contract_failures=len(received)-len(valid), transport_failures=len(attempted)-len(received),
        not_dispatched=len(rows)-len(attempted),
        rejected_responses_with_questions=sum(bool(r['raw_questions']) for r in received if r['validation'] != 'valid')),
        held_out=dict(total=len(held), attempted=sum(r['hosted'] == 'attempted' for r in held),
            valid=len(held_valid), end_to_end_decision_matches=sum(r['decision_match'] for r in held),
            decision_matches_among_valid=sum(r['decision_match'] for r in held_valid)),
        recovery=dict(responses=len(recovery), valid=sum(r['validation'] == 'valid' for r in recovery),
            decision_matches=sum(r.get('decision_match', False) for r in recovery)))


def render(rows, counts, errors, root):
    hosted, held, recovery = counts['hosted'], counts['held_out'], counts['recovery']
    signed = sum(r.get('reviewed', False) for r in rows)
    lines = ['# Experiment review and submission map', '',
        'This is the current entry point for the version 3 experiment and separate dry-run recovery.', '',
        '## Evidence verification', '',
        f"Current package: **{'verification passed' if not errors else 'verification failed'}**; "
        f'{signed}/{len(rows)} current assessment approvals verified.',
        'A pass means the declared evidence and approvals are consistent. It does not mean good model performance,',
        'verified hosted safeguards for recovery cases, or guaranteed acceptance by the marker.', '',
        '```text', 'python -m review_tools verify', 'python -m review_tools report', '```', '']
    if errors:
        lines += ['Verification errors:', '', *['- ' + e for e in errors], '']
    lines += ['## Results with explicit denominators', '',
        '| Measure | Result |', '| --- | --- |',
        f"| Hosted attempts / planned cases | {hosted['attempted']}/{hosted['total']} |",
        f"| Hosted responses / attempts | {hosted['responses']}/{hosted['attempted']} |",
        f"| Contract-valid hosted outputs / responses | {hosted['valid']}/{hosted['responses']} |",
        f"| Rejected hosted outputs | {hosted['contract_failures']} |",
        f"| Hosted transport failures without a response | {hosted['transport_failures']} |",
        f"| Hosted cases never dispatched | {hosted['not_dispatched']} |",
        f"| Held-out end-to-end decision agreement | {held['end_to_end_decision_matches']}/{held['total']} |",
        f"| Valid held-out outputs / cases | {held['valid']}/{held['total']} |",
        f"| Held-out agreement among valid outputs | {held['decision_matches_among_valid']}/{held['valid']} |",
        f"| Separate recovery valid outputs | {recovery['valid']}/{recovery['responses']} |",
        f"| Separate recovery decision agreement | {recovery['decision_matches']}/{recovery['responses']} |", '',
        'Recovery accuracy is not pooled with hosted accuracy. Invalid outputs and transport failures remain',
        'in the original hosted denominators. Rejected outputs receive no validated decision credit.',
        f"Of the rejected outputs, {hosted['rejected_responses_with_questions']} contain questions; their signed assessments",
        'describe redundancy and other qualitative problems separately from official scoring.', '',
        '## All cases and human review', '',
        '| Case / original input | Frozen expected | Hosted result | Recovery result | Assessment |',
        '| --- | --- | --- | --- | --- |']
    for row in rows:
        case = row['case_id']
        if row['hosted'] == 'not_dispatched':
            host = 'not dispatched (no hosted transcript)'
        else:
            host = f"[{row['validation']}](../evals/golden/transcripts/{case}.json)"
            if row['hosted_decision']:
                host += ': ' + row['hosted_decision']
        recover = row['recovery']
        recovered = (f"[{recover['decision']}](../evals/recovery/dry-run-six-2026-10-31-v2/{case}/validated-envelope.json)"
                     if recover else 'not part of recovery')
        review = 'signed' if row.get('reviewed') else 'pending/invalid'
        lines.append(f'| [{case}](../evals/golden/inputs/{case}.json) | {row.get("expected", "unknown")} | {host} | '
                     f'{recovered} | [{review}](../evals/golden/assessments/{case}.json) |')
    lines += ['', '## What the failures reveal', '',
        'The hosted configuration repeatedly requests supplied information and treats maintainer investigation as',
        'reporter omissions. Structural failures include long/non-verbatim quotes, missing gap entries and compound',
        'questions. HTTP 429 is recorded as transport failure, not an incorrect model decision.',
        'Always-sufficient matches 9/10 held-out primary labels and the checklist 5/10. The agent does not justify deployment.',
        'Only one of the 15 real primary labels requires clarification, so these data cannot establish broad recall.',
        'Among the seven contract-valid real outputs, six expected sufficient and one expected human_review.', '',
        '`pytest-13403` expects **human_review**, not sufficient. Its corrected revision and fresh signoff preserve',
        '[the earlier signed revision](../evals/evidence/review-signoffs/history/pytest-13403-v1/assessment.json)',
        'and do not change the frozen key or mismatch totals.', '',
        '## Fallback equivalence and limitations', '',
        '| Property | Hosted | Separate recovery |', '| --- | --- | --- |',
        '| Inputs, canonical skill and source packets | Frozen originals | Same frozen content |',
        '| Canonical system/user message text | Gateway messages | Embedded verbatim inside a CLI adapter |',
        '| Model | Auto; received responses report gpt-4o-mini-2024-07-18 | Requested gpt-6.1-sol alias; provider snapshot absent |',
        '| Runtime | Tool-free gateway harness | Codex CLI 0.165.0; native framing differs |',
        '| Hosted firewall, safeoutputs and identity | Inspect hosted evidence and control statuses | Not verified by recovery |',
        '| Tool behaviour | No model tools | Native traces show no tool actions; local isolation is not proved equivalent |', '',
        'The assignment permits a documented coding-assistant fallback. These runtime/model deviations are disclosed,',
        'not claimed to be an identical Copilot execution. The six cases lack completed paired hosted answers,',
        'so better recovery coverage does not identify a model-level cause or controlled accuracy improvement.',
        'The malicious-tool recovery decision mismatches human_review despite no observed tool action.', '',
        '## Controls and approval chronology', '',
        'The earlier approval covers pytest-15052; later batch and scoped resume approvals cover their own cases.',
        'The new checker validates these source-linked events rather than comparing every run to the later batch timestamp.',
        'Original approval times and historical failed gate logs remain unchanged.',
        'The paid-overage cap is a current user attestation, not an independent billing enforcement test or historical bill.',
        'Phone cancellation, public bot posting and a live malicious MCP server remain untested; publication stays disabled.',
        'Legacy hosted-only and legacy dry-run gates are retained for historical reproduction; neither is the current',
        'mixed-evidence submission audit. No absent hosted transcript is manufactured.', '',
        '## Evidence and reproduction links', '',
        '- [Design and five required answers](../DESIGN.md)',
        '- [Detailed phase 1 and batch analysis](V3-PHASE1-RESULT.md)',
        '- [Frozen expectations](../evals/golden/expectations.json)',
        '- [Manifest and scoped approval sources](../evals/evidence/v3-evidence-manifest.json)',
        '- [Recovery traces and startup failures](../evals/recovery/dry-run-six-2026-10-31-v2/README.md)',
        '- [Current reproduction commands](DRY-RUN.md)',
        '- [Future study proposal; no execution authorised](FUTURE-STUDY.md)', '',
        'AI-use statement: Codex generated this report from the declared evidence and signed assessments.',
        'Actual student approvals are separately recorded; no new inference or human approval is invented.', '']
    return '\n'.join(lines)


def write_report(root, result):
    root = Path(root)
    (root / 'docs').mkdir(exist_ok=True)
    (root / 'evals/evidence').mkdir(parents=True, exist_ok=True)
    (root / 'docs/EXPERIMENT-REVIEW.md').write_text(
        render(result['rows'], result['measurements'], result['errors'], root), encoding='utf-8')
    (root / 'evals/evidence/v3-review-report.json').write_text(
        json.dumps(result, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
    write_review_index(root, result)


def write_review_index(root, result):
    document = ['# Final 22-case review', '',
        'Current [experiment review and measurements](../EXPERIMENT-REVIEW.md) distinguish hosted',
        'and separate recovery evidence. Run `python -m review_tools verify` for current validation.',
        'A signed assessment may accurately describe a failed model answer. No failure becomes a pass.', '']
    for row in result['rows']:
        case = row['case_id']
        assessment = load(root / row['assessment'])
        document += [f"## {case} ({row['group']})", '',
            f"- Frozen expected decision: `{row['expected']}`.",
            f"- Hosted: `{row['hosted']}`; validation: `{row['validation']}`; "
            f"validated decision: `{row['hosted_decision'] or 'unavailable'}`.",
            f"- Current review: `{assessment['status']}` by `{assessment.get('reviewer')}` "
            f"at `{assessment.get('reviewed_at')}`.",
            '- Assessment: ' + html.escape(assessment['explanation']),
            f'- [Input](../../evals/golden/inputs/{case}.json); '
            f'[assessment](../../evals/golden/assessments/{case}.json).']
        if row['transcript']:
            transcript = load(root / row['transcript'])
            document += [f"- [Hosted transcript](../../{row['transcript']}); "
                         f"[original bundle](../../{transcript['bundle']}); run `{transcript['run_id']}`."]
        else:
            document += ['- No hosted transcript exists: this case was never dispatched.']
        if row.get('review_receipt'):
            document += [f"- [Applicable approval receipt](../../{row['review_receipt']})."]
        if row['raw_questions']:
            label = 'Validated questions' if row['validation'] == 'valid' else 'Raw unvalidated questions; no decision credit'
            document += ['- ' + label + ':', '', '```json',
                         json.dumps(row['raw_questions'], ensure_ascii=True), '```']
        if row['recovery']:
            recovery = row['recovery']
            document += [f"- Separate recovery: `{recovery['decision']}`; expected-decision match: "
                         f"`{recovery['decision_match']}`; zero observed tool actions.",
                         f'- [Recovery output](../../evals/recovery/dry-run-six-2026-10-31-v2/{case}/validated-envelope.json); '
                         f'[native trace](../../evals/recovery/dry-run-six-2026-10-31-v2/{case}/stdout.jsonl).']
        document += ['']
    document += ['AI-use statement: Codex generated this index from original evidence and explicitly signed',
                 'case assessments. Native records, prior review revisions and failures are retained.', '']
    target = root / 'docs/reviews/FINAL-22-CASE-REVIEW.md'
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text('\n'.join(document), encoding='utf-8')
