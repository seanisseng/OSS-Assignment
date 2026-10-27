"""Offline repository/evidence checks, with a separate strict submission gate."""
import ast
import argparse
import json
from pathlib import Path
import re

from scripts.contract import CATEGORIES, digest
from scripts.evidence import submission_evidence


def verify(submission=False, mode='remote'):
    errors = []
    required = ['AGENTS.md', 'CONTRIBUTING.md', 'DESIGN.md',
                '.claude/skills/bug-report-clarification/SKILL.md',
                '.github/workflows/clarify.md', '.github/workflows/clarify.lock.yml',
                '.github/workflows/publish.yml', 'evals/golden/expectations.json']
    errors.extend('Missing ' + name for name in required if not Path(name).is_file())
    if errors:
        return errors
    if len(Path('DESIGN.md').read_text(encoding='utf-8').splitlines()) > 150:
        errors.append('DESIGN exceeds 150 lines')
    lock = Path('.github/workflows/clarify.lock.yml').read_text(encoding='utf-8')
    if re.search(r'^\s+(?:contents|issues|pull-requests): write', lock, re.M):
        errors.append('Analysis has forbidden write permission')
    for ref in re.findall(r'uses: ([^\s]+)', lock):
        if '@' in ref and not re.fullmatch(r'.+@[a-f0-9]{40}', ref):
            errors.append('Mutable action reference: ' + ref)
    root = Path('evals/golden')
    expectations = json.loads((root / 'expectations.json').read_text(encoding='utf-8'))['expectations']
    freeze = json.loads((root / 'freeze.json').read_text())
    if digest(expectations) != freeze['expectations_hash']:
        errors.append('Expectation freeze changed')
    if sum(not x.get('synthetic', False) for x in expectations) != 15 or sum(x['split'] == 'held-out' for x in expectations) != 10:
        errors.append('Incorrect real case split')
    if sum(x.get('synthetic', False) for x in expectations) != 3 or len(list((root / 'adversarial').glob('*.json'))) != 4:
        errors.append('Incorrect diagnostic/adversarial case count')
    for item in expectations:
        decisions = item.get('acceptable_decisions', [item['decision']])
        if item['decision'] not in decisions or not set(decisions) <= {'sufficient', 'needs_information', 'human_review'}:
            errors.append('Invalid decision alternatives: ' + item['case_id'])
        bundles = item.get('acceptable_missing_sets', [item['acceptable_missing']])
        if not bundles or any(not set(bundle) <= CATEGORIES for bundle in bundles):
            errors.append('Invalid category alternatives: ' + item['case_id'])
        if set().union(*(set(bundle) for bundle in bundles)) != set(item['acceptable_missing']):
            errors.append('Category union/bundles mismatch: ' + item['case_id'])
        primary = item.get('primary_missing')
        if primary is not None and set(primary) not in [set(bundle) for bundle in bundles]:
            errors.append('Primary category bundle is not allowed: ' + item['case_id'])
        for checks in [*item.get('alternative_checks', {}).values(), *item.get('category_checks', {}).values()]:
            for check in checks:
                if not check.get('name') or not check.get('patterns'):
                    errors.append('Empty mechanical checklist: ' + item['case_id'])
                for pattern in check.get('patterns', []):
                    re.compile(pattern, re.I | re.S)
        case = json.loads((root / f"inputs/{item['case_id']}.json").read_text(encoding='utf-8'))
        if digest(case) != item['input_hash']:
            errors.append('Input hash changed: ' + item['case_id'])
        for source, wanted in item['context_hashes'].items():
            if digest(case['context'][source]) != wanted:
                errors.append('Context hash changed: ' + item['case_id'])
    for path in [*Path('scripts').glob('*.py'), *Path('tests').glob('*.py')]:
        ast.parse(path.read_text(encoding='utf-8'), filename=str(path))
    candidates = [p for folder in ['scripts', 'tests', 'config', 'evals', '.github', '.claude']
                  for p in Path(folder).rglob('*') if p.is_file() and '__pycache__' not in p.parts]
    secret = re.compile(r'gh[pousr]_[A-Za-z0-9]{30,}|github_pat_[A-Za-z0-9_]{50,}|-----BEGIN (?:RSA |OPENSSH )?PRIVATE KEY-----')
    for path in candidates:
        if secret.search(path.read_text(encoding='utf-8')):
            errors.append('Possible secret: ' + str(path))
    if submission:
        errors.extend(submission_evidence(Path.cwd(), mode))
    return errors


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--submission', action='store_true')
    parser.add_argument('--mode', choices=['dry-run', 'remote'], default='remote')
    args = parser.parse_args()
    errors = verify(args.submission, args.mode)
    print('\n'.join(errors) if errors else 'Local repository verification passed.')
    raise SystemExit(bool(errors))
