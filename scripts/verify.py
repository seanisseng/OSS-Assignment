"""Offline repository/evidence checks, with a separate strict submission gate."""
import ast
import json
from pathlib import Path
import re
import sys

from scripts.contract import digest, validate


def verify(submission=False):
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
    if len(expectations) != 15 or sum(x['split'] == 'held-out' for x in expectations) != 10:
        errors.append('Incorrect real case split')
    for item in expectations:
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
        if not freeze['review_approved']:
            errors.append('Student expectation review not recorded')
        case_ids = [x['case_id'] for x in expectations] + [p.stem for p in (root / 'adversarial').glob('*.json')]
        for case_id in case_ids:
            actual = root / f'actual/{case_id}.json'
            transcript = root / f'transcripts/{case_id}.json'
            if not actual.exists() or not transcript.exists():
                errors.append('Missing actual output/transcript: ' + case_id)
                continue
            case = json.loads((root / f'inputs/{case_id}.json').read_text(encoding='utf-8'))
            try:
                validate(case, json.loads(actual.read_text(encoding='utf-8')))
            except ValueError:
                errors.append('Invalid actual result: ' + case_id)
        for name in ['remote-smoke.json', 'skill-loading.json', 'publication.json', 'phone-stop.json']:
            if not Path('evals/evidence', name).exists():
                errors.append('Required remote evidence absent: ' + name)
    return errors


if __name__ == '__main__':
    errors = verify('--submission' in sys.argv)
    print('\n'.join(errors) if errors else 'Local repository verification passed.')
    raise SystemExit(bool(errors))
