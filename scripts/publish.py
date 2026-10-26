"""Trusted executor: one hardcoded comment endpoint; no model code execution."""
import datetime as dt
import json
import os
from pathlib import Path
import re
import urllib.request

from scripts.contract import REPOSITORY, authorize, digest, require, validate
from scripts.runtime import api


def pages(path):
    values = []
    for page in range(1, 101):
        batch = api(path + ('&' if '?' in path else '?') + f'per_page=100&page={page}')
        values.extend(batch)
        if len(batch) < 100:
            return values
    raise ValueError('pagination safety ceiling; refuse incomplete duplicate/count scan')


def main():
    require(os.environ['GITHUB_REPOSITORY'] == REPOSITORY, 'foreign repository')
    require(os.environ['GITHUB_REF'] == 'refs/heads/main', 'main required')
    require(os.environ.get('GITHUB_RUN_ATTEMPT') == '1', 'publisher retries forbidden')
    policy = json.loads(Path('config/policy.json').read_text())
    run_id = os.environ['ANALYSIS_RUN']
    require(re.fullmatch(r'[0-9]+', run_id) is not None, 'invalid run ID')
    permission = api('collaborators/' + os.environ['GITHUB_ACTOR'] + '/permission')
    require(permission['permission'] in {'admin', 'maintain'}, 'maintainer approval required')
    run = api('actions/runs/' + run_id)
    require(run['event'] == 'workflow_dispatch' and run['conclusion'] == 'success'
            and run['path'] == '.github/workflows/clarify.lock.yml'
            and run['head_branch'] == 'main'
            and run['head_sha'] == os.environ['GITHUB_SHA']
            and run['run_attempt'] == 1, 'untrusted, failed, retried or stale analysis')
    files = list(Path('staged').rglob('*'))
    require(len(files) == 1 and files[0].name == 'recommendation.json'
            and not files[0].is_symlink() and files[0].stat().st_size <= 32768,
            'unexpected artifact files')
    result = json.loads(files[0].read_text(encoding='utf-8'))
    manifest = json.loads(Path('trusted-input/manifest.json').read_text(encoding='utf-8'))
    case_id = result.get('case_id', '')
    require(isinstance(case_id, str) and re.fullmatch(r'[a-z0-9-]{1,64}', case_id), 'invalid case ID')
    case = json.loads(Path('evals/golden/inputs', case_id + '.json').read_text(encoding='utf-8'))
    validate(case, result)
    require(manifest['case_id'] == case_id and manifest['input_hash'] == digest(case), 'analysis input mismatch')
    issue = policy['case_targets'].get(case_id)
    require(type(issue) is int and manifest['sandbox_issue'] == issue, 'trusted target mismatch')
    trusted_issue = api(f'issues/{issue}')
    require('pull_request' not in trusted_issue and trusted_issue['state'] == 'open', 'not an open issue')
    require('clarification-sandbox' in {x['name'] for x in trusted_issue['labels']}, 'sandbox label required')
    marker = '<!-- clarification:' + result['input_hash'] + ' -->'
    comments = pages(f'issues/{issue}/comments')
    existing = [result['input_hash']] if any(marker in c['body'] for c in comments) else []
    today = dt.datetime.now(dt.timezone.utc).date().isoformat()
    all_comments = pages('issues/comments?since=' + today + 'T00:00:00Z')
    count = sum(c['user']['login'] == 'github-actions[bot]' and '<!-- clarification:' in c['body']
                and c['created_at'].startswith(today) for c in all_comments)
    age = (dt.datetime.now(dt.timezone.utc) - dt.datetime.fromisoformat(run['created_at'].replace('Z', '+00:00'))).total_seconds() / 3600
    # Read live repository variable immediately before the final write. Missing => deny.
    enabled = api('actions/variables/CLARIFICATION_ENABLED')['value'] == 'true'
    authorize(repository=REPOSITORY, issue=issue, allowed=policy['allowed_issues'],
              enabled=enabled and policy['enabled'] and os.environ.get('ENABLED') == 'true',
              approved_hash=os.environ['APPROVED_HASH'], result=result, existing=existing,
              today_count=count, age_hours=age)
    # Escape HTML, links, mentions and Markdown so recommendation remains plain text.
    import html
    text = html.escape(result['comment']).replace('@', '@\u200b')
    text = re.sub(r'([\\`*_[\]#])', r'\\\1', text)
    body = text + '\n\nAI-assisted clarification; reviewed by @' + os.environ['GITHUB_ACTOR']
    body += f'. Analysis: https://github.com/{REPOSITORY}/actions/runs/{run_id}\n' + marker
    require(len(body) <= 1200, 'rendered comment including disclosure exceeds 1200 characters')
    request = urllib.request.Request(f'https://api.github.com/repos/{REPOSITORY}/issues/{issue}/comments',
        data=json.dumps({'body': body}).encode(), method='POST',
        headers={'Authorization': 'Bearer ' + os.environ['GH_TOKEN'],
                 'Content-Type': 'application/json', 'Accept': 'application/vnd.github+json'})
    # No retry: an uncertain response must be reconciled by scanning comments.
    with urllib.request.urlopen(request, timeout=30) as response:
        posted = json.load(response)
    require(posted['user']['login'] == 'github-actions[bot]', 'unexpected publication identity')
    print(json.dumps(dict(comment_url=posted['html_url'], recommendation_hash=digest(result),
                          analysis_run=run_id, actor=os.environ['GITHUB_ACTOR'])))


if __name__ == '__main__':
    main()
