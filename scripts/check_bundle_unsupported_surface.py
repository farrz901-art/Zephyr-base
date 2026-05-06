from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path


def _read_text(path: Path) -> str:
    raw = path.read_bytes()
    if raw.startswith(b'\xff\xfe') or raw.startswith(b'\xfe\xff'):
        return raw.decode('utf-16')
    if raw.startswith(b'\xef\xbb\xbf'):
        return raw.decode('utf-8-sig')
    return raw.decode('utf-8')


def _read_json(path: Path) -> dict[str, object]:
    loaded: object = json.loads(_read_text(path))
    if not isinstance(loaded, dict):
        raise ValueError(f'Expected JSON object at {path}')
    return loaded


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description='Check bundled adapter unsupported surface behavior.')
    parser.add_argument('--bundle-root', type=Path, default=Path('runtime/public-core-bundle'))
    parser.add_argument('--json', action='store_true')
    args = parser.parse_args(argv)

    root = Path(__file__).resolve().parents[1]
    bundle_root = args.bundle_root if args.bundle_root.is_absolute() else (root / args.bundle_root).resolve()
    runner = root / 'public-core-bridge' / 'run_public_core_adapter.py'
    request = root / 'tests/fixtures/unsupported_pdf_request.json'
    out_dir = root / '.tmp' / 'bundled_adapter_unsupported_pdf'
    completed = subprocess.run(
        [
            sys.executable,
            str(runner),
            '--request',
            str(request),
            '--out-dir',
            str(out_dir),
            '--bundle-root',
            str(bundle_root),
            '--json',
        ],
        cwd=root,
        check=False,
        capture_output=True,
        text=True,
    )
    if completed.stdout:
        print(completed.stdout)
    if completed.stderr:
        print(completed.stderr, file=sys.stderr)

    run_result_path = out_dir / 'run_result.json'
    if not run_result_path.exists():
        report = {
            'schema_version': 1,
            'report_id': 'zephyr.base.bundle_unsupported_surface_check.v1',
            'summary': {
                'pass': False,
                'unsupported_pdf_rejected': False,
                'hidden_pdf_route_available': False,
                'secret_safe_error': False,
            },
            'result': {
                'returncode': completed.returncode,
                'status': 'missing_run_result',
                'error_code': None,
                'category': None,
                'secret_safe': None,
                'normalized_text_non_empty': False,
            },
        }
        out_path = root / '.tmp' / 'bundle_unsupported_surface_check.json'
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
        if args.json:
            print(json.dumps(report, ensure_ascii=False, indent=2))
        return 1

    run_result = _read_json(run_result_path)
    error_obj = run_result.get('error')
    if not isinstance(error_obj, dict):
        raise ValueError('Expected base_error_v1 payload in run_result.error')
    normalized_text = _read_text(out_dir / 'normalized_text.txt')
    category = error_obj.get('category')
    hidden_pdf_route_available = bool(normalized_text.strip()) or run_result.get('status') == 'success'
    unsupported_pdf_rejected = completed.returncode != 0 and run_result.get('status') == 'failed'
    secret_safe_error = error_obj.get('secret_safe') is True
    report = {
        'schema_version': 1,
        'report_id': 'zephyr.base.bundle_unsupported_surface_check.v1',
        'summary': {
            'pass': bool(
                unsupported_pdf_rejected
                and category in {'input', 'processing'}
                and secret_safe_error
                and not hidden_pdf_route_available
            ),
            'unsupported_pdf_rejected': unsupported_pdf_rejected,
            'hidden_pdf_route_available': hidden_pdf_route_available,
            'secret_safe_error': secret_safe_error,
        },
        'result': {
            'returncode': completed.returncode,
            'status': run_result.get('status'),
            'error_code': error_obj.get('error_code'),
            'category': category,
            'secret_safe': error_obj.get('secret_safe'),
            'normalized_text_non_empty': bool(normalized_text.strip()),
        },
    }
    out_path = root / '.tmp' / 'bundle_unsupported_surface_check.json'
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report['summary']['pass'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
