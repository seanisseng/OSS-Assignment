"""Trusted pre-agent checks; never import code from agent artifacts."""
import json
import os
from pathlib import Path
import re
import sys
import urllib.request

from scripts.contract import REPOSITORY, admit, digest, require


def api(path):
    request = urllib.request.Request('https://api.github.com/repos/' + REPOSITORY + '/' + path,
        headers={'Authorization': 'Bearer ' + os.environ['GH_TOKEN'],
                 'Accept': 'application/vnd.github+json'})
    with urllib.request.urlopen(request, timeout=30) as response:
        return json.load(response)


def prepare():
    root = Path(os.environ.get('TRUSTED_ROOT', '.'))
    policy = json.loads((root / 'config/policy.json').read_text())
    require(os.environ['GITHUB_REPOSITORY'] == REPOSITORY, 'foreign repository')
    require(os.environ['GITHUB_REF'] == 'refs/heads/main', 'main branch required')
    require(policy['enabled'] and policy['budget_verified'] and
            os.environ.get('ENABLED') == 'true', 'disabled or unverified allowance')
    review = json.loads((root / 'evals/golden/freeze.json').read_text())
    require(review['review_approved'] is True, 'student expectation review pending')
    require(os.environ.get('GITHUB_RUN_ATTEMPT') == '1', 'automatic/manual retries forbidden')
    runs = api('actions/workflows/clarify.lock.yml/runs?per_page=1')
    require(admit(runs['total_count'] - 1, True), '40 attempts exhausted')
    case_id = os.environ['CASE_ID']
    require(re.fullmatch(r'[a-z0-9-]{1,64}', case_id) is not None, 'invalid case id')
    case = json.loads((root / 'evals/golden/inputs' / (case_id + '.json')).read_text(encoding='utf-8'))
    require(case['case_id'] == case_id, 'case mismatch')
    issue = policy['case_targets'].get(case_id)
    require(type(issue) is int and issue in policy['allowed_issues'], 'not allowlisted')
    Path('input').mkdir(exist_ok=True)
    Path('output').mkdir(exist_ok=True)
    Path('input/case.json').write_text(json.dumps(case, ensure_ascii=False), encoding='utf-8')
    skill = (root / '.claude/skills/bug-report-clarification/SKILL.md').read_bytes()
    installed = Path('.github/skills/bug-report-clarification/SKILL.md')
    installed.parent.mkdir(parents=True, exist_ok=True)
    installed.write_bytes(skill)
    Path('AGENTS.md').write_bytes((root / 'AGENTS.md').read_bytes())
    Path('input/manifest.json').write_text(json.dumps(dict(case_id=case_id, input_hash=digest(case),
        sandbox_issue=issue, skill_sha256=__import__('hashlib').sha256(skill).hexdigest())), encoding='utf-8')


if __name__ == '__main__':
    require(sys.argv[1:] == ['prepare'], 'unsupported command')
    prepare()
