"""Trusted explicitly authorized smoke attempt; never targets publication."""
import hashlib
import json
import os
from pathlib import Path

from scripts.contract import REPOSITORY, digest, require
from scripts.evidence import review_record
from scripts.runtime import api


def prepare():
    root = Path(os.environ.get('TRUSTED_ROOT', '.')).resolve()
    require(os.environ.get('GITHUB_REPOSITORY') == REPOSITORY, 'foreign repository')
    require(os.environ.get('GITHUB_REF') == 'refs/heads/main', 'main branch required')
    require(os.environ.get('GITHUB_RUN_ATTEMPT') == '1', 'retries forbidden')
    require(os.environ.get('SMOKE_ENABLED') == 'true', 'smoke test disabled')
    require(os.environ.get('CASE_ID') == 'pytest-15051', 'only development case 15051 allowed')
    review = review_record(root)
    case = json.loads((root / 'evals/golden/inputs/pytest-15051.json').read_text(encoding='utf-8'))
    expected = json.loads((root / 'evals/golden/expectations.json').read_text(encoding='utf-8'))
    entry = next(x for x in expected['expectations'] if x['case_id'] == 'pytest-15051')
    require(case['case_id'] == 'pytest-15051' and digest(case) == entry['input_hash'],
            'smoke input differs from reviewed snapshot')
    runs = api('actions/workflows/smoke.lock.yml/runs?per_page=1')
    count = runs['total_count']
    require(type(count) is int and count == 2, 'authorized replacement attempt exhausted or unknown')
    Path('input').mkdir(exist_ok=True)
    Path('output').mkdir(exist_ok=True)
    Path('input/case.json').write_text(json.dumps(case, ensure_ascii=False), encoding='utf-8')
    skill = (root / '.claude/skills/bug-report-clarification/SKILL.md').read_bytes()
    installed = Path('.github/skills/bug-report-clarification/SKILL.md')
    installed.parent.mkdir(parents=True, exist_ok=True)
    installed.write_bytes(skill)
    Path('AGENTS.md').write_bytes((root / 'AGENTS.md').read_bytes())
    manifest = dict(case_id=case['case_id'], input_hash=digest(case), sandbox_issue=None,
                    artifact_only=True, skill_sha256=hashlib.sha256(skill).hexdigest(),
                    configuration_hash=review['configuration_hash'])
    Path('input/manifest.json').write_text(json.dumps(manifest), encoding='utf-8')


if __name__ == '__main__':
    prepare()
