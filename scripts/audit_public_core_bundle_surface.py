from __future__ import annotations

import argparse
import json
from pathlib import Path

ALLOWED_SUPPORTED_EXTENSIONS = ['.txt', '.md']
ALLOWED_PARTITION_KINDS = ['text', 'md']
ALLOWED_SOURCES = ['local_file']
ALLOWED_DESTINATIONS = ['filesystem']
ALLOWED_PARTITION_FILES = {
    '__init__.py',
    'auto.py',
    'text.py',
    'md.py',
    'strategies.py',
    'text_type.py',
    'model_init.py',
}
FORBIDDEN_PARTITION_FILES = {
    'api.py',
    'audio.py',
    'csv.py',
    'doc.py',
    'docx.py',
    'email.py',
    'epub.py',
    'html.py',
    'image.py',
    'json.py',
    'msg.py',
    'ndjson.py',
    'odt.py',
    'org.py',
    'pdf.py',
    'ppt.py',
    'pptx.py',
    'rst.py',
    'rtf.py',
    'tsv.py',
    'xlsx.py',
    'xml.py',
}
FORBIDDEN_AUTO_EXTS = (
    '.html', '.xml', '.eml', '.msg', '.json', '.pdf', '.png', '.jpg', '.jpeg', '.csv', '.tsv',
    '.xlsx', '.xls', '.doc', '.docx', '.ppt', '.pptx', '.rtf', '.epub', '.odt', '.org', '.ndjson', '.jsonl'
)
FORBIDDEN_EXTRA_KINDS = (
    'pdf', 'doc', 'docx', 'ppt', 'pptx', 'xlsx', 'csv', 'tsv', 'rtf', 'rst', 'epub', 'odt',
    'org', 'image', 'email', 'html', 'xml', 'ndjson', 'json', 'msg'
)
FORBIDDEN_DESTINATION_FILES = {
    'clickhouse.py', 'kafka.py', 'loki.py', 'mongodb.py', 'opensearch.py', 's3.py', 'sqlite.py',
    'weaviate.py', 'webhook.py', 'fanout.py'
}
FORBIDDEN_BUNDLE_FILES = {
    'packages/zephyr-ingest/src/zephyr_ingest/queue_backend.py',
    'packages/zephyr-ingest/src/zephyr_ingest/queue_backend_factory.py',
    'packages/zephyr-ingest/src/zephyr_ingest/queue_inspect.py',
    'packages/zephyr-ingest/src/zephyr_ingest/queue_recover.py',
    'packages/zephyr-ingest/src/zephyr_ingest/sqlite_queue.py',
    'packages/zephyr-ingest/src/zephyr_ingest/worker_runtime.py',
    'packages/zephyr-ingest/src/zephyr_ingest/health_server.py',
    'packages/zephyr-ingest/src/zephyr_ingest/obs/prom_export.py',
    'packages/zephyr-ingest/src/zephyr_ingest/governance_action.py',
    'packages/zephyr-ingest/src/zephyr_ingest/replay_delivery.py',
    'packages/zephyr-ingest/src/zephyr_ingest/dlq_prune.py',
    'packages/zephyr-ingest/src/zephyr_ingest/lock_provider.py',
    'packages/zephyr-ingest/src/zephyr_ingest/lock_provider_factory.py',
    'packages/zephyr-ingest/src/zephyr_ingest/sqlite_lock_provider.py',
}
FORBIDDEN_TERMS = (
    'kafka',
    's3',
    'clickhouse',
    'mongodb',
    'opensearch',
    'weaviate',
    'webhook',
    'confluence',
    'google_drive',
    'license_verify',
    'paid_user',
    'entitlement_server',
    'payment_callback',
    'billing_decision',
    'quota_authority',
    'risk_score',
    'web_core.internal',
    'private_core_export',
    'zephyr_pro',
)
TEXT_SUFFIXES = {'.py', '.json', '.md', '.toml', '.txt', '.yml', '.yaml'}


def _read_text(path: Path) -> str:
    raw = path.read_bytes()
    if raw.startswith(b'\xff\xfe') or raw.startswith(b'\xfe\xff'):
        return raw.decode('utf-16')
    if raw.startswith(b'\xef\xbb\xbf'):
        return raw.decode('utf-8-sig')
    return raw.decode('utf-8')


def _load_json(path: Path) -> dict[str, object]:
    loaded = json.loads(_read_text(path))
    if not isinstance(loaded, dict):
        raise ValueError(f'Expected JSON object at {path}')
    return loaded


def _iter_files(root: Path) -> list[Path]:
    files: list[Path] = []
    for path in root.rglob('*'):
        if path.is_dir():
            continue
        rel = path.relative_to(root)
        if '__pycache__' in rel.parts or path.suffix == '.pyc':
            continue
        files.append(path)
    return sorted(files)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description='Audit the trimmed public-core bundle surface.')
    parser.add_argument('--bundle-root', type=Path, default=Path('runtime/public-core-bundle'))
    parser.add_argument('--json', action='store_true')
    args = parser.parse_args(argv)

    repo_root = Path(__file__).resolve().parents[1]
    bundle_root = args.bundle_root if args.bundle_root.is_absolute() else (repo_root / args.bundle_root).resolve()
    manifest_path = bundle_root / 'manifest/public_core_bundle_manifest.json'
    manifest = _load_json(manifest_path)

    blocked_files: list[dict[str, object]] = []
    review_required_files: list[dict[str, object]] = []
    blocked_terms: list[dict[str, object]] = []
    allowed_files: list[str] = []
    notes: list[str] = []

    supported_input_extensions = manifest.get('supported_input_extensions')
    if supported_input_extensions != ALLOWED_SUPPORTED_EXTENSIONS:
        blocked_files.append({'path': 'manifest/public_core_bundle_manifest.json', 'reason': 'supported_input_extensions_mismatch'})
    if manifest.get('allowed_partition_kinds') != ALLOWED_PARTITION_KINDS:
        blocked_files.append({'path': 'manifest/public_core_bundle_manifest.json', 'reason': 'allowed_partition_kinds_mismatch'})
    if manifest.get('allowed_sources') != ALLOWED_SOURCES:
        blocked_files.append({'path': 'manifest/public_core_bundle_manifest.json', 'reason': 'allowed_sources_mismatch'})
    if manifest.get('allowed_destinations') != ALLOWED_DESTINATIONS:
        blocked_files.append({'path': 'manifest/public_core_bundle_manifest.json', 'reason': 'allowed_destinations_mismatch'})

    removed_surface = manifest.get('removed_surface')
    if not isinstance(removed_surface, dict):
        blocked_files.append({'path': 'manifest/public_core_bundle_manifest.json', 'reason': 'removed_surface_missing'})
    else:
        expected_removed = {
            'non_txt_md_partition_modules_removed': True,
            'remote_sources_removed': True,
            'remote_destinations_removed': True,
            'testing_helpers_removed': True,
            'queue_worker_observability_governance_removed': True,
        }
        for key, expected in expected_removed.items():
            if removed_surface.get(key) is not expected:
                blocked_files.append({'path': 'manifest/public_core_bundle_manifest.json', 'reason': f'{key}_mismatch'})

    partition_root = bundle_root / 'packages/uns-stream/src/uns_stream/partition'
    partition_names = {
        path.name
        for path in partition_root.iterdir()
        if path.is_file() and path.suffix == '.py'
    }
    allowed_files.extend(sorted(f'packages/uns-stream/src/uns_stream/partition/{name}' for name in partition_names if name in ALLOWED_PARTITION_FILES))
    for forbidden in sorted(FORBIDDEN_PARTITION_FILES):
        if (partition_root / forbidden).exists():
            blocked_files.append({'path': f'packages/uns-stream/src/uns_stream/partition/{forbidden}', 'reason': 'forbidden_partition_module_present'})
    unexpected_partition = sorted(name for name in partition_names if name not in ALLOWED_PARTITION_FILES)
    for name in unexpected_partition:
        blocked_files.append({'path': f'packages/uns-stream/src/uns_stream/partition/{name}', 'reason': 'unexpected_partition_module'})

    auto_text = _read_text(partition_root / 'auto.py')
    for ext in ALLOWED_SUPPORTED_EXTENSIONS + ['.text', '.log', '.markdown']:
        if ext not in auto_text:
            blocked_files.append({'path': 'packages/uns-stream/src/uns_stream/partition/auto.py', 'reason': f'missing_allowed_extension:{ext}'})
    for ext in FORBIDDEN_AUTO_EXTS:
        if ext in auto_text:
            blocked_files.append({'path': 'packages/uns-stream/src/uns_stream/partition/auto.py', 'reason': f'forbidden_extension_route:{ext}'})

    local_unstructured = _read_text(bundle_root / 'packages/uns-stream/src/uns_stream/backends/local_unstructured.py')
    for kind in ('"text"', '"md"'):
        if kind not in local_unstructured:
            blocked_files.append({'path': 'packages/uns-stream/src/uns_stream/backends/local_unstructured.py', 'reason': f'missing_allowed_kind:{kind}'})
    for kind in FORBIDDEN_EXTRA_KINDS:
        if f'"{kind}"' in local_unstructured:
            blocked_files.append({'path': 'packages/uns-stream/src/uns_stream/backends/local_unstructured.py', 'reason': f'forbidden_extra_kind:{kind}'})

    uns_sources_root = bundle_root / 'packages/uns-stream/src/uns_stream/sources'
    uns_source_names = {
        path.name for path in uns_sources_root.iterdir() if path.is_file() and path.suffix == '.py'
    }
    for name in sorted(uns_source_names):
        if name == '__init__.py':
            allowed_files.append(f'packages/uns-stream/src/uns_stream/sources/{name}')
        else:
            blocked_files.append({'path': f'packages/uns-stream/src/uns_stream/sources/{name}', 'reason': 'remote_source_retained'})

    ingest_sources_root = bundle_root / 'packages/zephyr-ingest/src/zephyr_ingest/sources'
    ingest_source_names = {
        path.name for path in ingest_sources_root.iterdir() if path.is_file() and path.suffix == '.py'
    }
    for name in sorted(ingest_source_names):
        if name in {'__init__.py', 'local_file.py'}:
            allowed_files.append(f'packages/zephyr-ingest/src/zephyr_ingest/sources/{name}')
        else:
            blocked_files.append({'path': f'packages/zephyr-ingest/src/zephyr_ingest/sources/{name}', 'reason': 'unexpected_ingest_source'})

    destinations_root = bundle_root / 'packages/zephyr-ingest/src/zephyr_ingest/destinations'
    destination_names = {
        path.name for path in destinations_root.iterdir() if path.is_file() and path.suffix == '.py'
    }
    for name in sorted(destination_names):
        if name in {'__init__.py', 'base.py', 'filesystem.py'}:
            allowed_files.append(f'packages/zephyr-ingest/src/zephyr_ingest/destinations/{name}')
        else:
            blocked_files.append({'path': f'packages/zephyr-ingest/src/zephyr_ingest/destinations/{name}', 'reason': 'unexpected_destination'})
    for name in sorted(FORBIDDEN_DESTINATION_FILES):
        if (destinations_root / name).exists():
            blocked_files.append({'path': f'packages/zephyr-ingest/src/zephyr_ingest/destinations/{name}', 'reason': 'forbidden_destination_present'})

    for rel in sorted(FORBIDDEN_BUNDLE_FILES):
        if (bundle_root / rel).exists():
            blocked_files.append({'path': rel, 'reason': 'forbidden_bundle_file_present'})
    if (bundle_root / 'packages/zephyr-ingest/src/zephyr_ingest/testing').exists():
        blocked_files.append({'path': 'packages/zephyr-ingest/src/zephyr_ingest/testing', 'reason': 'testing_helpers_retained'})

    for path in _iter_files(bundle_root):
        rel = path.relative_to(bundle_root).as_posix()
        if path.suffix.lower() not in TEXT_SUFFIXES:
            continue
        text = _read_text(path).lower()
        for term in FORBIDDEN_TERMS:
            if term in text:
                blocked_terms.append({'path': rel, 'term': term})

    summary = {
        'overall': 'pass' if not blocked_files and not blocked_terms else 'fail',
        'blocked_count': len(blocked_files) + len(blocked_terms),
        'review_required_count': len(review_required_files),
        'bundle_surface_matches_manifest': not blocked_files and not blocked_terms,
        'supported_input_extensions': ALLOWED_SUPPORTED_EXTENSIONS,
    }
    report = {
        'schema_version': 1,
        'report_id': 'zephyr.base.s5r.public_core_bundle_surface_audit.v1',
        'summary': summary,
        'allowed_files': allowed_files,
        'blocked_files': blocked_files,
        'blocked_terms': blocked_terms,
        'review_required_files': review_required_files,
        'notes': notes,
    }
    out_path = repo_root / '.tmp' / 'public_core_bundle_surface_audit.json'
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if summary['blocked_count'] == 0 else 1


if __name__ == '__main__':
    raise SystemExit(main())
