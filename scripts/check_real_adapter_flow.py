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


def _run(root: Path, request: str, out_dir: str, zephyr_dev_root: Path) -> int:
    runner = root / 'public-core-bridge' / 'run_public_core_adapter.py'
    completed = subprocess.run(
        [
            sys.executable,
            str(runner),
            '--request',
            request,
            '--out-dir',
            out_dir,
            '--zephyr-dev-root',
            str(zephyr_dev_root),
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
        'usage_billing_semantics': usage.get('billing_semantics'),
        'marker_found': marker_found,
        'production_runtime': bool(run_result.get('production_runtime')),
        'fixture_runner_used': bool(run_result.get('fixture_runner_used')),
        'zephyr_dev_public_core_invoked': bool(run_result.get('zephyr_dev_public_core_invoked')),
        'content_evidence_kind': str(content.get('evidence_kind', '')),
        'adapter_runtime': str(run_result.get('adapter_runtime', '')),
        'local_text_bridge_mode': run_result.get('local_text_bridge_mode'),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description='Check Zephyr-base real adapter flow.')
    parser.add_argument('--zephyr-dev-root', type=Path, required=True)
    parser.add_argument('--json', action='store_true')
    args = parser.parse_args(argv)

    root = Path(__file__).resolve().parents[1]
    file_code = _run(root, 'tests/fixtures/real_adapter_request_file.json', '.tmp/local_adapter_flow', args.zephyr_dev_root)
    text_code = _run(root, 'tests/fixtures/real_adapter_request_text.json', '.tmp/local_adapter_flow_text', args.zephyr_dev_root)
    file_result = _verify(root, '.tmp/local_adapter_flow', 'ZEPHYR_BASE_REAL_ADAPTER_MARKER_M3_S4')
    text_result = _verify(root, '.tmp/local_adapter_flow_text', 'ZEPHYR_BASE_REAL_ADAPTER_MARKER_M3_S4_TEXT')
    passed = (
        file_code == 0
        and text_code == 0
        and bool(file_result['marker_found'])
        and bool(text_result['marker_found'])
        and file_result['usage_billing_semantics'] is False
        and text_result['usage_billing_semantics'] is False
        and file_result['fixture_runner_used'] is False
        and text_result['fixture_runner_used'] is False
        and file_result['zephyr_dev_public_core_invoked'] is True
        and text_result['zephyr_dev_public_core_invoked'] is True
        and file_result['content_evidence_kind'] != 'fixture_content_evidence_v1'
        and text_result['content_evidence_kind'] != 'fixture_content_evidence_v1'
        and bool(file_result['adapter_runtime'])
        and bool(text_result['adapter_runtime'])
    )
    report = {
        'schema_version': 1,
        'report_id': 'zephyr.base.local_adapter_flow_check.v1',
        'summary': {
            'pass': passed,
            'file_adapter_pass': file_code == 0,
            'text_adapter_pass': text_code == 0,
            'marker_found': bool(file_result['marker_found'] and text_result['marker_found']),
            'production_runtime': bool(file_result['production_runtime'] and text_result['production_runtime']),
            'fixture_runner_used_for_s4_pass': bool(file_result['fixture_runner_used'] or text_result['fixture_runner_used']),
            'zephyr_dev_public_core_invoked': bool(file_result['zephyr_dev_public_core_invoked'] and text_result['zephyr_dev_public_core_invoked']),
            'content_evidence_kind_is_fixture': bool(
                file_result['content_evidence_kind'] == 'fixture_content_evidence_v1'
                or text_result['content_evidence_kind'] == 'fixture_content_evidence_v1'
            ),
        },
        'file_adapter': file_result,
        'text_adapter': text_result,
    }
    out = root / '.tmp' / 'local_adapter_flow_check.json'
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if passed else 1


if __name__ == '__main__':
    raise SystemExit(main())
