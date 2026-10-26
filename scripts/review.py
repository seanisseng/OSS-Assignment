"""Local review helper; validates and prints exact recommendation hash."""
import json
from pathlib import Path
import re
import sys

from scripts.contract import digest, require, validate


def main():
    require(len(sys.argv) == 3, 'usage: python -m scripts.review CASE_ID result.json')
    case_id, filename = sys.argv[1:]
    require(re.fullmatch(r'[a-z0-9-]{1,64}', case_id), 'invalid ID')
    case = json.loads(Path(f'evals/golden/inputs/{case_id}.json').read_text(encoding='utf-8'))
    result = json.loads(Path(filename).read_text(encoding='utf-8'))
    validate(case, result)
    print(json.dumps(result, ensure_ascii=True, indent=2))
    print('Recommendation hash:', digest(result))


if __name__ == '__main__':
    main()
