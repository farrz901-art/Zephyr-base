from __future__ import annotations

import argparse
import json
from pathlib import Path

PATTERNS = (
    '.github/workflows/*.yml',
    'scripts/*.py',
    'ui/src/**/*.ts',
    'ui/src/**/*.tsx',
    'src-tauri/src/**/*.rs',
    'docs/**/*.md',
    'manifests/**/*.json',
    'runtime/**/*.json',
)


def _write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding='utf-8')


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description='Remove UTF-8 BOM markers from Zephyr-base text files.')
    parser.add_argument('--json', action='store_true')
    args = parser.parse_args(argv)

    root = Path(__file__).resolve().parents[1]
    matched: dict[str, Path] = {}
    for pattern in PATTERNS:
        for path in root.glob(pattern):
            if path.is_file():
                matched[path.relative_to(root).as_posix()] = path

    fixed_files: list[str] = []
    bom_found_count = 0
    bom_prefix = b"\xef\xbb\xbf"
    for relative_path, path in sorted(matched.items()):
        raw = path.read_bytes()
        if raw.startswith(bom_prefix):
            bom_found_count += 1
            path.write_bytes(raw[3:])
            fixed_files.append(relative_path)

    residual_bom = 0
    for path in matched.values():
        if path.read_bytes().startswith(bom_prefix):
            residual_bom += 1

    report = {
        'schema_version': 1,
        'report_id': 'zephyr.base.s9.no_bom_check.v1',
        'summary': {
            'pass': residual_bom == 0,
            'bom_count': residual_bom,
            'bom_found_count_before_fix': bom_found_count,
            'files_fixed_count': len(fixed_files),
        },
        'files_fixed': fixed_files,
    }
    out_path = root / '.tmp' / 'no_bom_check.json'
    _write_json(out_path, report)
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if residual_bom == 0 else 1


if __name__ == '__main__':
    raise SystemExit(main())
