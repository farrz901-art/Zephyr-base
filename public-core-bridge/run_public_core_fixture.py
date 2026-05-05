from __future__ import annotations

import argparse
import json
from pathlib import Path


def _read_text(path: Path) -> str:
    raw = path.read_bytes()
    if raw.startswith(b"\xff\xfe") or raw.startswith(b"\xfe\xff"):
        return raw.decode('utf-16')
    if raw.startswith(b"\xef\xbb\xbf"):
        return raw.decode('utf-8-sig')
    return raw.decode('utf-8')


def _read_request(path: Path) -> dict[str, object]:
    return json.loads(_read_text(path))


def _normalize_text(text: str) -> str:
    return '\n'.join(text.replace('\r\n', '\n').replace('\r', '\n').splitlines()).strip()


def _write_json(path: Path, payload: dict[str, object]) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def _build_error(request_id: str, code: str, category: str, message: str, detail: str) -> dict[str, object]:
    return {
        'schema_version': 1,
        'error_code': code,
        'category': category,
        'user_message': message,
        'technical_detail_safe': detail,
        'secret_safe': True,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description='Run the Zephyr-base fixture public-core bridge.')
    parser.add_argument('--request', type=Path, required=True)
    parser.add_argument('--out-dir', type=Path, required=True)
    parser.add_argument('--json', action='store_true')
    args = parser.parse_args(argv)

    root = Path(__file__).resolve().parents[1]
    request_path = args.request if args.request.is_absolute() else (root / args.request)
    out_dir = args.out_dir if args.out_dir.is_absolute() else (root / args.out_dir)
    request = _read_request(request_path)
    request_id = str(request.get('request_id', 'unknown-request'))
    input_kind = str(request.get('input_kind', 'unknown'))
    out_dir.mkdir(parents=True, exist_ok=True)

    error: dict[str, object] | None = None
    source_text = ''
    source_kind = input_kind
    if input_kind == 'local_file':
        input_path_value = str(request.get('input_path', ''))
        input_path = Path(input_path_value) if Path(input_path_value).is_absolute() else (root / input_path_value)
        if not input_path.exists():
            error = _build_error(request_id, 'base_input_missing', 'input', 'Input file was not found.', f'Missing local fixture file: {input_path.as_posix()}')
        else:
            source_text = _read_text(input_path)
    elif input_kind == 'local_text':
        source_text = str(request.get('inline_text', ''))
    else:
        error = _build_error(request_id, 'base_input_kind_unsupported', 'input', 'Input kind is not supported by the fixture runner.', f'Unsupported fixture input kind: {input_kind}')

    normalized = _normalize_text(source_text) if error is None else ''
    marker_found = 'ZEPHYR_BASE_FIXTURE_MARKER_M3_S3' in source_text
    preview = normalized[:160]
    input_bytes = len(source_text.encode('utf-8')) if error is None else 0
    content_evidence = {
        'schema_version': 1,
        'evidence_kind': 'fixture_content_evidence_v1',
        'normalized_text_preview': preview,
        'source_kind': source_kind,
        'input_bytes': input_bytes,
        'elements_count': 1 if normalized else 0,
        'token_marker_found': marker_found,
        'production_runtime': False,
    }
    receipt = {
        'schema_version': 1,
        'run_id': f'fixture-{request_id}',
        'request_id': request_id,
        'status': 'failed' if error else 'success',
        'delivery_outcome': 'failed' if error else 'success',
        'output_root': str(out_dir),
        'artifacts': ['normalized_text.txt', 'content_evidence.json', 'receipt.json', 'usage_fact.json', 'run_result.json'],
        'created_by': 'Zephyr-base fixture runner',
        'production_runtime': False,
    }
    usage_fact = {
        'schema_version': 1,
        'fact_kind': 'technical_usage_fact',
        'billing_semantics': False,
        'input_bytes': input_bytes,
        'output_files_count': 5,
        'production_runtime': False,
    }
    run_result = {
        'schema_version': 1,
        'request_id': request_id,
        'status': 'failed' if error else 'success',
        'normalized_text_preview': preview,
        'content_evidence_summary': content_evidence,
        'receipt': receipt,
        'usage_fact': usage_fact,
        'output_files': ['normalized_text.txt', 'content_evidence.json', 'receipt.json', 'usage_fact.json', 'run_result.json'],
        'error': error,
    }

    (out_dir / 'normalized_text.txt').write_text(normalized + ('\n' if normalized else ''), encoding='utf-8')
    _write_json(out_dir / 'content_evidence.json', content_evidence)
    _write_json(out_dir / 'receipt.json', receipt)
    _write_json(out_dir / 'usage_fact.json', usage_fact)
    _write_json(out_dir / 'run_result.json', run_result)
    if args.json:
        print(json.dumps(run_result, ensure_ascii=False, indent=2))
    return 1 if error else 0


if __name__ == '__main__':
    raise SystemExit(main())
