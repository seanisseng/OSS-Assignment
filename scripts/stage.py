"""Validate raw model data in a clean job, before it is eligible for review."""
import json
from pathlib import Path
import re

from scripts.contract import digest, require, validate


def main():
    manifest = json.loads(Path('trusted-input/manifest.json').read_text(encoding='utf-8'))
    case_id = manifest['case_id']
    require(isinstance(case_id, str) and re.fullmatch(r'[a-z0-9-]{1,64}', case_id), 'invalid case ID')
    case = json.loads(Path(f'evals/golden/inputs/{case_id}.json').read_text(encoding='utf-8'))
    require(digest(case) == manifest['input_hash'], 'trusted input mismatch')
    path = Path('staged/recommendation.json')
    require(not path.is_symlink() and path.stat().st_size <= 32768, 'oversized/symlink output')
    result = json.loads(path.read_text(encoding='utf-8'))
    validate(case, result)
    print(json.dumps(result, ensure_ascii=True, indent=2))
    print('Exact approval hash:', digest(result))


if __name__ == '__main__':
    main()
