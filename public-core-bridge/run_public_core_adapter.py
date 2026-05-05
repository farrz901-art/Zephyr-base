from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path


OUTPUT_FILES = [
    'normalized_text.txt',
    'content_evidence.json',
    'receipt.json',
    'usage_fact.json',
    'run_result.json',
]


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


def _write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def _resolve_repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def _resolve_path(root: Path, value: Path) -> Path:
    return value if value.is_absolute() else (root / value).resolve()


def _build_error(*, code: str, category: str, message: str, detail: str) -> dict[str, object]:
    return {
        'schema_version': 1,
        'error_code': code,
        'category': category,
        'user_message': message,
        'technical_detail_safe': detail,
        'secret_safe': True,
    }


def _write_failure_outputs(
    *,
    out_dir: Path,
    request_id: str,
    error: dict[str, object],
    adapter_runtime: str,
    bundled_runtime_used: bool,
    zephyr_dev_working_tree_required: bool,
) -> dict[str, object]:
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / 'normalized_text.txt').write_text('', encoding='utf-8')
    content_evidence = {
        'schema_version': 1,
        'evidence_kind': 'artifact_reference_only_v1',
        'normalized_text_status': 'missing',
        'production_runtime': False,
        'adapter_runtime': adapter_runtime,
        'real_adapter_runtime': False,
        'fixture_runner_used': False,
        'bundled_runtime_used': bundled_runtime_used,
        'zephyr_dev_public_core_invoked': False,
        'zephyr_dev_working_tree_required': zephyr_dev_working_tree_required,
        'installer_runtime_complete': False,
        'requires_network': False,
        'requires_p45_substrate': False,
    }
    receipt = {
        'schema_version': 1,
        'run_id': f'failed-{request_id}',
        'request_id': request_id,
        'status': 'failed',
        'delivery_outcome': 'failed',
        'output_root': str(out_dir),
        'artifacts': OUTPUT_FILES,
        'created_by': 'Zephyr-base public core adapter',
        'production_runtime': False,
        'real_adapter_runtime': False,
        'adapter_runtime': adapter_runtime,
        'fixture_runner_used': False,
        'bundled_runtime_used': bundled_runtime_used,
        'zephyr_dev_public_core_invoked': False,
        'zephyr_dev_working_tree_required': zephyr_dev_working_tree_required,
        'installer_runtime_complete': False,
        'requires_network': False,
        'requires_p45_substrate': False,
    }
    usage_fact = {
        'schema_version': 1,
        'fact_kind': 'technical_usage_fact',
        'billing_semantics': False,
        'output_files_count': len(OUTPUT_FILES),
        'production_runtime': False,
        'real_adapter_runtime': False,
        'adapter_runtime': adapter_runtime,
        'fixture_runner_used': False,
        'bundled_runtime_used': bundled_runtime_used,
        'zephyr_dev_public_core_invoked': False,
        'zephyr_dev_working_tree_required': zephyr_dev_working_tree_required,
        'installer_runtime_complete': False,
        'requires_network': False,
        'requires_p45_substrate': False,
    }
    run_result = {
        'schema_version': 1,
        'request_id': request_id,
        'status': 'failed',
        'normalized_text_preview': '',
        'content_evidence_summary': {
            'elements_count': 0,
            'has_normalized_text': False,
            'evidence_kind': 'artifact_reference_only_v1',
        },
        'receipt': receipt,
        'usage_fact': usage_fact,
        'output_files': OUTPUT_FILES,
        'error': error,
        'fixture_runner_used': False,
        'bundled_runtime_used': bundled_runtime_used,
        'zephyr_dev_public_core_invoked': False,
        'zephyr_dev_working_tree_required': zephyr_dev_working_tree_required,
        'adapter_runtime': adapter_runtime,
        'real_adapter_runtime': False,
        'production_runtime': False,
        'installer_runtime_complete': False,
        'requires_network': False,
        'requires_p45_substrate': False,
    }
    _write_json(out_dir / 'content_evidence.json', content_evidence)
    _write_json(out_dir / 'receipt.json', receipt)
    _write_json(out_dir / 'usage_fact.json', usage_fact)
    _write_json(out_dir / 'run_result.json', run_result)
    return run_result


def _validate_against_contract(*, contract_path: Path, run_result: dict[str, object]) -> None:
    contract = _read_json(contract_path)
    contracts = contract.get('contracts')
    if not isinstance(contracts, dict):
        raise ValueError('bridge_contract_missing_contracts')
    result_contract = contracts.get('base_run_result_v1')
    error_contract = contracts.get('base_error_v1')
    if not isinstance(result_contract, dict) or not isinstance(error_contract, dict):
        raise ValueError('bridge_contract_missing_result_or_error')
    required_fields = result_contract.get('required_fields')
    if not isinstance(required_fields, list):
        raise ValueError('bridge_contract_missing_required_fields')
    for field in required_fields:
        if not isinstance(field, str):
            raise ValueError('bridge_contract_invalid_required_field')
        if field not in run_result:
            raise ValueError(f'run_result_missing_field:{field}')
    usage_fact = run_result.get('usage_fact')
    if not isinstance(usage_fact, dict) or usage_fact.get('billing_semantics') is not False:
        raise ValueError('run_result_usage_fact_billing_semantics_must_be_false')
    error_obj = run_result.get('error')
    if error_obj is not None:
        if not isinstance(error_obj, dict):
            raise ValueError('run_result_error_must_be_object_or_null')
        if error_obj.get('secret_safe') is not True:
            raise ValueError('run_result_error_secret_safe_must_be_true')


def _invoke_fixture(root: Path, request_path: Path, out_dir: Path) -> int:
    runner = root / 'public-core-bridge' / 'run_public_core_fixture.py'
    completed = subprocess.run(
        [
            sys.executable,
            str(runner),
            '--request',
            str(request_path),
            '--out-dir',
            str(out_dir),
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


def _prepare_upstream_request(*, root: Path, request: dict[str, object], staging_dir: Path) -> Path:
    payload = dict(request)
    input_kind = str(payload.get('input_kind', 'unknown'))
    if input_kind == 'local_file':
        input_path_value = str(payload.get('input_path', ''))
        resolved_input_path = _resolve_path(root, Path(input_path_value))
        payload['input_path'] = str(resolved_input_path)
    payload['output_dir'] = str(staging_dir)
    request_path = staging_dir / 'request.json'
    _write_json(request_path, payload)
    return request_path


def _finalize_outputs(
    *,
    out_dir: Path,
    staging_dir: Path,
    invocation_succeeded: bool,
    adapter_runtime: str,
    bundled_runtime_used: bool,
    zephyr_dev_public_core_invoked: bool,
    zephyr_dev_working_tree_required: bool,
    installer_runtime_complete: bool,
    bundle_root: Path | None,
) -> dict[str, object]:
    contract_path = _resolve_repo_root() / 'public-core-bridge' / 'bridge_contract.json'
    run_result = _read_json(staging_dir / 'run_result.json')
    _validate_against_contract(contract_path=contract_path, run_result=run_result)
    content_evidence = _read_json(staging_dir / 'content_evidence.json')
    receipt = _read_json(staging_dir / 'receipt.json')
    usage_fact = _read_json(staging_dir / 'usage_fact.json')
    normalized_text = _read_text(staging_dir / 'normalized_text.txt')

    shared = {
        'adapter_runtime': adapter_runtime,
        'real_adapter_runtime': invocation_succeeded,
        'production_runtime': invocation_succeeded,
        'fixture_runner_used': False,
        'bundled_runtime_used': bundled_runtime_used,
        'zephyr_dev_public_core_invoked': zephyr_dev_public_core_invoked,
        'zephyr_dev_working_tree_required': zephyr_dev_working_tree_required,
        'installer_runtime_complete': installer_runtime_complete,
        'requires_network': False,
        'requires_p45_substrate': False,
    }
    if bundle_root is not None:
        shared['bundle_root'] = str(bundle_root)

    content_evidence.update(shared)
    receipt.update(shared)
    receipt['output_root'] = str(out_dir)
    usage_fact.update(shared)
    run_result.update(shared)
    run_result['receipt'] = receipt
    run_result['usage_fact'] = usage_fact

    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / 'normalized_text.txt').write_text(normalized_text, encoding='utf-8')
    _write_json(out_dir / 'content_evidence.json', content_evidence)
    _write_json(out_dir / 'receipt.json', receipt)
    _write_json(out_dir / 'usage_fact.json', usage_fact)
    _write_json(out_dir / 'run_result.json', run_result)
    return run_result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description='Run the Zephyr-base public-core adapter.')
    parser.add_argument('--request', type=Path, required=True)
    parser.add_argument('--out-dir', type=Path, required=True)
    parser.add_argument('--zephyr-dev-root', type=Path, default=None)
    parser.add_argument('--bundle-root', type=Path, default=None)
    parser.add_argument('--allow-fixture-fallback', action='store_true')
    parser.add_argument('--json', action='store_true')
    args = parser.parse_args(argv)

    root = _resolve_repo_root()
    request_path = _resolve_path(root, args.request)
    out_dir = _resolve_path(root, args.out_dir)
    request = _read_json(request_path)
    request_id = str(request.get('request_id', 'unknown-request'))

    if args.bundle_root is not None:
        bundle_root = _resolve_path(root, args.bundle_root)
        runner = bundle_root / 'run_bundle_public_core.py'
        if not runner.exists():
            error = _build_error(
                code='base_dependency_missing',
                category='dependency',
                message='Bundled public-core runtime is missing.',
                detail=f'Missing bundle entrypoint: {runner.as_posix()}',
            )
            run_result = _write_failure_outputs(
                out_dir=out_dir,
                request_id=request_id,
                error=error,
                adapter_runtime='zephyr_base_bundled_public_core_adapter_v1',
                bundled_runtime_used=False,
                zephyr_dev_working_tree_required=False,
            )
            if args.json:
                print(json.dumps(run_result, ensure_ascii=False, indent=2))
            return 1
        staging_dir = out_dir / '_bundled_public_core_runner'
        if staging_dir.exists():
            shutil.rmtree(staging_dir)
        staging_dir.mkdir(parents=True, exist_ok=True)
        upstream_request_path = _prepare_upstream_request(root=root, request=request, staging_dir=staging_dir)
        completed = subprocess.run(
            [
                sys.executable,
                str(runner),
                '--request',
                str(upstream_request_path),
                '--out-dir',
                str(staging_dir),
                '--json',
            ],
            cwd=bundle_root,
            check=False,
            capture_output=True,
            text=True,
        )
        if completed.stdout:
            print(completed.stdout)
        if completed.stderr:
            print(completed.stderr, file=sys.stderr)
        run_result = _finalize_outputs(
            out_dir=out_dir,
            staging_dir=staging_dir,
            invocation_succeeded=completed.returncode == 0,
            adapter_runtime='zephyr_base_bundled_public_core_adapter_v1',
            bundled_runtime_used=True,
            zephyr_dev_public_core_invoked=False,
            zephyr_dev_working_tree_required=False,
            installer_runtime_complete=False,
            bundle_root=bundle_root,
        )
        if args.json:
            print(json.dumps(run_result, ensure_ascii=False, indent=2))
        return 0 if completed.returncode == 0 and str(run_result.get('status')) == 'success' else 1

    requested_root = args.zephyr_dev_root
    if requested_root is None:
        env_raw = os.environ.get('ZEPHYR_DEV_ROOT')
        if env_raw:
            requested_root = Path(env_raw)
    if requested_root is None:
        if args.allow_fixture_fallback:
            code = _invoke_fixture(root, request_path, out_dir)
            run_result = _read_json(out_dir / 'run_result.json')
            run_result['adapter_runtime'] = 'zephyr_base_public_core_adapter_v1'
            run_result['fixture_runner_used'] = True
            run_result['bundled_runtime_used'] = False
            run_result['zephyr_dev_public_core_invoked'] = False
            run_result['zephyr_dev_working_tree_required'] = False
            run_result['installer_runtime_complete'] = False
            _write_json(out_dir / 'run_result.json', run_result)
            if args.json:
                print(json.dumps(run_result, ensure_ascii=False, indent=2))
            return code
        error = _build_error(
            code='base_dependency_missing',
            category='dependency',
            message='A bundled runtime or Zephyr-dev root is required for the adapter.',
            detail='Provide --bundle-root or --zephyr-dev-root; fixture fallback is disabled by default.',
        )
        run_result = _write_failure_outputs(
            out_dir=out_dir,
            request_id=request_id,
            error=error,
            adapter_runtime='zephyr_base_public_core_adapter_v1',
            bundled_runtime_used=False,
            zephyr_dev_working_tree_required=False,
        )
        if args.json:
            print(json.dumps(run_result, ensure_ascii=False, indent=2))
        return 1

    zephyr_dev_root = requested_root.resolve()
    runner = zephyr_dev_root / 'tools' / 'p6_m3_public_core_local_runner.py'
    if not runner.exists():
        error = _build_error(
            code='base_dependency_missing',
            category='dependency',
            message='Zephyr-dev public core local runner is missing.',
            detail=f'Missing runner: {runner.as_posix()}',
        )
        run_result = _write_failure_outputs(
            out_dir=out_dir,
            request_id=request_id,
            error=error,
            adapter_runtime='zephyr_base_public_core_adapter_v1',
            bundled_runtime_used=False,
            zephyr_dev_working_tree_required=True,
        )
        if args.json:
            print(json.dumps(run_result, ensure_ascii=False, indent=2))
        return 1

    staging_dir = out_dir / '_zephyr_dev_runner'
    if staging_dir.exists():
        shutil.rmtree(staging_dir)
    staging_dir.mkdir(parents=True, exist_ok=True)
    upstream_request_path = _prepare_upstream_request(root=root, request=request, staging_dir=staging_dir)

    completed = subprocess.run(
        [
            sys.executable,
            str(runner),
            '--root',
            str(zephyr_dev_root),
            '--request',
            str(upstream_request_path),
            '--out-dir',
            str(staging_dir),
            '--json',
        ],
        cwd=zephyr_dev_root,
        check=False,
        capture_output=True,
        text=True,
    )
    if completed.stdout:
        print(completed.stdout)
    if completed.stderr:
        print(completed.stderr, file=sys.stderr)

    run_result = _finalize_outputs(
        out_dir=out_dir,
        staging_dir=staging_dir,
        invocation_succeeded=completed.returncode == 0,
        adapter_runtime='zephyr_base_public_core_adapter_v1',
        bundled_runtime_used=False,
        zephyr_dev_public_core_invoked=True,
        zephyr_dev_working_tree_required=True,
        installer_runtime_complete=False,
        bundle_root=None,
    )
    if args.json:
        print(json.dumps(run_result, ensure_ascii=False, indent=2))
    return 0 if completed.returncode == 0 and str(run_result.get('status')) == 'success' else 1


if __name__ == '__main__':
    raise SystemExit(main())
