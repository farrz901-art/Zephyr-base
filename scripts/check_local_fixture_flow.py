from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path


def _read_text(path: Path) -> str:
    raw = path.read_bytes()
    if raw.startswith(b"\xff\xfe") or raw.startswith(b"\xfe\xff"):
        return raw.decode('utf-16')
    if raw.startswith(b"\xef\xbb\xbf"):
        return raw.decode('utf-8-sig')
    return raw.decode('utf-8')


def _read_json(path: Path) -> dict[str, object]:
    return json.loads(_read_text(path))


def _run(root: Path, request: str, out_dir: str) -> int:
    runner = root / 'public-core-bridge' / 'run_public_core_fixture.py'
    cmd = [sys.executable, str(runner), '--request', request, '--out-dir', out_dir, '--json']
    completed = subprocess.run(cmd, cwd=root, check=False, capture_output=True, text=True)
    if completed.stdout:
        print(completed.stdout)
    if completed.stderr:
        print(completed.stderr, file=sys.stderr)
    return completed.returncode


def _verify(root: Path, rel_out_dir: str, expected_marker: str) -> dict[str, object]:
    out_dir = root / rel_out_dir
    run_result = _read_json(out_dir / 'run_result.json')
    content = _read_json(out_dir / 'content_evidence.json')
    receipt = _read_json(out_dir / 'receipt.json')
    usage = _read_json(out_dir / 'usage_fact.json')
    normalized = _read_text(out_dir / 'normalized_text.txt')
    preview = str(run_result['normalized_text_preview'])
    marker_found = expected_marker in normalized or expected_marker in preview or expected_marker in json.dumps(content)
    return {
        'run_result_exists': (out_dir / 'run_result.json').exists(),
        'normalized_text_exists': (out_dir / 'normalized_text.txt').exists(),
        'content_evidence_exists': (out_dir / 'content_evidence.json').exists(),
        'receipt_exists': (out_dir / 'receipt.json').exists(),
        'usage_billing_semantics': bool(usage['billing_semantics']),
        'marker_found': marker_found,
        'production_runtime': bool(receipt['production_runtime']),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description='Check local Zephyr-base fixture flow.')
    parser.add_argument('--json', action='store_true')
    args = parser.parse_args(argv)
    root = Path(__file__).resolve().parents[1]
    file_code = _run(root, 'tests/fixtures/sample_request_file.json', '.tmp/local_fixture_flow')
    text_code = _run(root, 'tests/fixtures/sample_request_text.json', '.tmp/local_fixture_flow_text')
    file_result = _verify(root, '.tmp/local_fixture_flow', 'ZEPHYR_BASE_FIXTURE_MARKER_M3_S3')
    text_result = _verify(root, '.tmp/local_fixture_flow_text', 'ZEPHYR_BASE_FIXTURE_MARKER_M3_S3_TEXT')
    passed = file_code == 0 and text_code == 0 and file_result['marker_found'] and text_result['marker_found'] and (file_result['usage_billing_semantics'] is False) and (text_result['usage_billing_semantics'] is False) and (file_result['production_runtime'] is False) and (text_result['production_runtime'] is False)
    report = {
        'schema_version': 1,
        'report_id': 'zephyr.base.local_fixture_flow_check.v1',
        'summary': {
            'pass': passed,
            'file_fixture_pass': file_code == 0,
            'text_fixture_pass': text_code == 0,
            'marker_found': bool(file_result['marker_found'] and text_result['marker_found']),
            'production_runtime': False,
        },
        'file_fixture': file_result,
        'text_fixture': text_result,
    }
    out = root / '.tmp' / 'local_fixture_flow_check.json'
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if passed else 1


if __name__ == '__main__':
    raise SystemExit(main())
