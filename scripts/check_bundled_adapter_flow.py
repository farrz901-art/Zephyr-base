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


def _run(root: Path, request: str, out_dir: str, bundle_root: Path) -> int:
    runner = root / 'public-core-bridge' / 'run_public_core_adapter.py'
    completed = subprocess.run(
        [
            sys.executable,
            str(runner),
            '--request',
            request,
            '--out-dir',
            out_dir,
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
    return completed.returncode


def _verify(root: Path, rel_out_dir: str, expected_marker: str) -> dict[str, object]:
    out_dir = root / rel_out_dir
    run_result = _read_json(out_dir / 'run_result.json')
    content = _read_json(out_dir / 'content_evidence.json')
    receipt = _read_json(out_dir / 'receipt.json')
    usage = _read_json(out_dir / 'usage_fact.json')
    normalized = _read_text(out_dir / 'normalized_text.txt')
    preview = str(run_result['normalized_text_preview'])
    joined = json.dumps({'run_result': run_result, 'content': content, 'receipt': receipt}, ensure_ascii=False)
    marker_found = expected_marker in normalized or expected_marker in preview or expected_marker in joined
    contains_dev_root = 'E:\\\\Github_Projects\\\\Zephyr' in joined or '/Github_Projects/Zephyr' in joined
    return {
        'run_result_exists': (out_dir / 'run_result.json').exists(),
        'normalized_text_exists': (out_dir / 'normalized_text.txt').exists(),
        'content_evidence_exists': (out_dir / 'content_evidence.json').exists(),
        'receipt_exists': (out_dir / 'receipt.json').exists(),
        'usage_billing_semantics': usage.get('billing_semantics'),
        'marker_found': marker_found,
        'production_runtime': bool(run_result.get('production_runtime')),
        'fixture_runner_used': bool(run_result.get('fixture_runner_used')),
        'bundled_runtime_used': bool(run_result.get('bundled_runtime_used')),
        'zephyr_dev_working_tree_required': bool(run_result.get('zephyr_dev_working_tree_required')),
        'content_evidence_kind': str(content.get('evidence_kind', '')),
        'adapter_runtime': str(run_result.get('adapter_runtime', '')),
        'requires_network': bool(run_result.get('requires_network')),
        'requires_p45_substrate': bool(run_result.get('requires_p45_substrate')),
        'installer_runtime_complete': bool(run_result.get('installer_runtime_complete')),
        'contains_dev_root': contains_dev_root,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description='Check Zephyr-base bundled adapter flow.')
    parser.add_argument('--bundle-root', type=Path, default=Path('runtime/public-core-bundle'))
    parser.add_argument('--json', action='store_true')
    args = parser.parse_args(argv)

    root = Path(__file__).resolve().parents[1]
    bundle_root = args.bundle_root if args.bundle_root.is_absolute() else (root / args.bundle_root).resolve()
    file_code = _run(root, 'tests/fixtures/real_adapter_request_file.json', '.tmp/bundled_adapter_flow', bundle_root)
    text_code = _run(root, 'tests/fixtures/real_adapter_request_text.json', '.tmp/bundled_adapter_flow_text', bundle_root)
    file_result = _verify(root, '.tmp/bundled_adapter_flow', 'ZEPHYR_BASE_REAL_ADAPTER_MARKER_M3_S4')
    text_result = _verify(root, '.tmp/bundled_adapter_flow_text', 'ZEPHYR_BASE_REAL_ADAPTER_MARKER_M3_S4_TEXT')
    passed = (
        file_code == 0
        and text_code == 0
        and bool(file_result['marker_found'])
        and bool(text_result['marker_found'])
        and file_result['usage_billing_semantics'] is False
        and text_result['usage_billing_semantics'] is False
        and file_result['fixture_runner_used'] is False
        and text_result['fixture_runner_used'] is False
        and file_result['bundled_runtime_used'] is True
        and text_result['bundled_runtime_used'] is True
        and file_result['zephyr_dev_working_tree_required'] is False
        and text_result['zephyr_dev_working_tree_required'] is False
        and file_result['content_evidence_kind'] != 'fixture_content_evidence_v1'
        and text_result['content_evidence_kind'] != 'fixture_content_evidence_v1'
        and bool(file_result['adapter_runtime'])
        and bool(text_result['adapter_runtime'])
        and file_result['requires_network'] is False
        and text_result['requires_network'] is False
        and file_result['requires_p45_substrate'] is False
        and text_result['requires_p45_substrate'] is False
        and file_result['installer_runtime_complete'] is False
        and text_result['installer_runtime_complete'] is False
        and file_result['contains_dev_root'] is False
        and text_result['contains_dev_root'] is False
    )
    report = {
        'schema_version': 1,
        'report_id': 'zephyr.base.bundled_adapter_flow_check.v1',
        'summary': {
            'pass': passed,
            'file_bundled_pass': file_code == 0,
            'text_bundled_pass': text_code == 0,
            'marker_found': bool(file_result['marker_found'] and text_result['marker_found']),
            'bundled_runtime_used': bool(file_result['bundled_runtime_used'] and text_result['bundled_runtime_used']),
            'zephyr_dev_working_tree_required': bool(file_result['zephyr_dev_working_tree_required'] or text_result['zephyr_dev_working_tree_required']),
            'fixture_runner_used_for_s5_pass': bool(file_result['fixture_runner_used'] or text_result['fixture_runner_used']),
            'content_evidence_kind_is_fixture': bool(
                file_result['content_evidence_kind'] == 'fixture_content_evidence_v1'
                or text_result['content_evidence_kind'] == 'fixture_content_evidence_v1'
            ),
            'requires_network': bool(file_result['requires_network'] or text_result['requires_network']),
            'requires_p45_substrate': bool(file_result['requires_p45_substrate'] or text_result['requires_p45_substrate']),
            'installer_runtime_complete': bool(file_result['installer_runtime_complete'] and text_result['installer_runtime_complete']),
            'contains_dev_root': bool(file_result['contains_dev_root'] or text_result['contains_dev_root']),
        },
        'file_bundled': file_result,
        'text_bundled': text_result,
    }
    out = root / '.tmp' / 'bundled_adapter_flow_check.json'
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if passed else 1


if __name__ == '__main__':
    raise SystemExit(main())
