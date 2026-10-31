"""Read-only audit by default; explicit report and prepare-only operations."""
import argparse
import json
from pathlib import Path

from review_tools.checks import verify
from review_tools.reporting import write_report
from review_tools.replay import prepare


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=Path.cwd())
    sub = parser.add_subparsers(dest='command', required=True)
    sub.add_parser('verify')
    sub.add_parser('report')
    replay = sub.add_parser('replay')
    replay.add_argument('--case', required=True)
    replay.add_argument('--workspace', required=True, type=Path)
    replay.add_argument('--prepare-only', action='store_true', required=True)
    args = parser.parse_args(argv)
    if args.command == 'replay':
        try:
            print(json.dumps(prepare(args.root, args.case, args.workspace), indent=2))
            return 0
        except (OSError, ValueError, KeyError, TypeError) as error:
            parser.exit(1, str(error) + '\n')
    result = verify(args.root)
    if args.command == 'report':
        write_report(args.root, result)
    print(json.dumps({k: v for k, v in result.items() if k != 'rows'}, indent=2))
    return int(bool(result['errors']))


if __name__ == '__main__':
    raise SystemExit(main())
