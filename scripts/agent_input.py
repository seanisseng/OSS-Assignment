"""Export a report-first view and lossless, bounded context files; no inference."""
import json
from pathlib import Path

from scripts.contract import require


CHUNK_BYTES = 8192


def export_case(case, workspace):
    context = case['context']
    require(isinstance(context, dict) and all(
        isinstance(key, str) and isinstance(value, str) for key, value in context.items()),
        'context must map evidence keys to text')
    workspace = Path(workspace)
    folder = workspace / 'input/context'
    folder.mkdir(parents=True, exist_ok=True)
    index = {}
    for number, (key, value) in enumerate(context.items()):
        remaining = value.encode('utf-8')
        parts = []
        while remaining or not parts:
            text = remaining[:CHUNK_BYTES].decode('utf-8', errors='ignore')
            data = text.encode('utf-8')
            relative = f'input/context/{number:03d}-{len(parts):03d}.txt'
            (workspace / relative).write_bytes(data)
            parts.append(relative)
            remaining = remaining[len(data):]
        index[key] = dict(bytes=len(value.encode('utf-8')), parts=parts)
    report = case | {'context': index}
    (workspace / 'input/case.json').write_bytes(
        (json.dumps(report, indent=2, ensure_ascii=False) + '\n').encode('utf-8'))
