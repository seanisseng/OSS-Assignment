"""Rebuild the per-case review index from preserved evidence; never approves drafts."""
import json
from pathlib import Path

from scripts.collect import save
from scripts.evidence import load
from scripts.evaluate import evaluate
from scripts.single_response import CASE_ORDER, DEVELOPMENT_CASES


def build(repo):
    root = repo / 'evals/golden'
    report = evaluate(root, 'single-response')
    save(root / 'report.json', report)
    rows = {x['case_id']:x for x in report['rows'] + report['adversarial']}
    freeze_path = root / 'final-configuration.json'
    freeze = load(freeze_path) if freeze_path.exists() else {}
    status = ('Final configuration awaits approval.' if not freeze.get('approved') else
              'Configuration approved; execution and review completion are counted below.')
    document = ['# Final 22-case review', '',
        'Status: ' + status + ' Entries below are evidence-driven.', '',
        'Previous configuration: seven successful executions; real development decision agreement',
        '1/5 and diagnostic agreement 2/2. Preserve that batch separately; it is not a final-study result.', '',
        'Native skill delivery is distinct from observed procedural compliance. Structural grounding',
        'does not establish that an investigation blocker is reasonable. Drafts require case review.', '',
        '## Group measurements', '', '```json', json.dumps(report['groups'],indent=2), '```', '',
        '## Baselines', '', '```json', json.dumps(report['baselines'],indent=2), '```', '',
        '## Every case', '']
    reliability = dict(planned=22, archived=0, workflow_success=0, requests_sent=0,
                       native_evidence_complete=0, reviewed=0, adversarial_decision_matches=0)
    for case_id in CASE_ORDER:
        row = rows[case_id]
        transcript = root / f'transcripts/{case_id}.json'
        record = load(transcript) if transcript.exists() else {}
        assessment_path = root / f'assessments/{case_id}.json'
        assessment = load(assessment_path) if assessment_path.exists() else {}
        actual = row['actual']
        expected = row['expected']
        group = ('real development' if case_id in DEVELOPMENT_CASES else 'real held-out')
        if case_id.startswith('diagnostic-'): group = 'synthetic diagnostic'
        if case_id in {'fake-approval','impersonation','malicious-tool','secret-exfiltration'}:
            group = 'adversarial'
            reliability['adversarial_decision_matches'] += bool(row.get('decision_match'))
        reliability['archived'] += bool(record)
        reliability['workflow_success'] += record.get('workflow_status') == 'success'
        reliability['requests_sent'] += record.get('requests_sent',0)
        reliability['reviewed'] += assessment.get('status') == 'reviewed'
        if record:
            from scripts.hosted_evidence import inspect_attempt
            checked = inspect_attempt(repo,case_id)
            reliability['native_evidence_complete'] += checked['evidence_complete']
        questions = actual.get('questions',[]) if actual else []
        explanation = assessment.get('explanation','Not run; no mismatch assessment exists.')
        document += [f'### {case_id} ({group})', '',
            f'- Expected: `{expected}`; actual: `{actual.get("decision") if actual else "unavailable"}`.',
            f'- Workflow: `{record.get("workflow_status","not run")}`; validation: `{row["validation"]}`.',
            f'- Decision agreement: `{row.get("decision_match","not measured")}`.',
            f'- Questions: {json.dumps(questions,ensure_ascii=False)}',
            f'- Review: `{assessment.get("status","pending")}`; {explanation}',
            f'- [Input](../../evals/golden/inputs/{case_id}.json); '
            f'[transcript](../../evals/golden/transcripts/{case_id}.json); '
            f'[assessment](../../evals/golden/assessments/{case_id}.json).']
        if record:
            document.append(f'- [Original hosted bundle](../../{record["bundle"]}); run ID `{record["run_id"]}`.')
        document.append('')
    document += ['## Execution reliability', '', '```json', json.dumps(reliability,indent=2), '```', '',
        'Workflow success, complete native evidence, valid response structure, agreement and review',
        'are separate counts. Missing output is a failed/absent result, never a sufficient decision.', '',
        '## Interpretation limits', '',
        'Fifteen real reports are a small, imbalanced sample with only one clarification primary.',
        'Development and held-out findings are separate. Three diagnostics and four attacks do not',
        'increase the historical denominator. Expectations were AI-assisted and accepted before inference.',
        'Only limited traceback-linked source excerpts are delivered. Auto is an unpinned selection;',
        'reported model identity and token usage do not guarantee reproducibility or account billing.',
        'Lexical conditional scoring can miss paraphrases or reward shallow matches; inspect semantics.',
        'The malicious-tool case supplies simulated evidence; no live malicious MCP server was exercised.',
        'No improvement claim is justified before comparing the final measurements. Publication is',
        'unnecessary for artifact-only submission; phone cancellation remains untested unless evidenced.', '',
        'AI may draft assessments; reviewer identities and timestamps must describe actual review.',
        'No student signoff is inferred from AI-authored text or the model audit.']
    path = repo / 'docs/reviews/FINAL-22-CASE-REVIEW.md'
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text('\n'.join(document)+'\n',encoding='utf-8')
    save(root / 'execution-summary.json',reliability)


if __name__ == '__main__':
    build(Path.cwd())
