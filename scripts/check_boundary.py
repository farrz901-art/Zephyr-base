from __future__ import annotations

import json
from pathlib import Path

FORBIDDEN_TERMS = (
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
ALLOWED_NEGATIVE = ('must not', 'not ', 'no ', 'forbidden', 'does not include')
ALLOWED_DOCS = {'README.md', 'PRODUCT_BOUNDARY.md'}
BLOCKED_PREFIXES = ('src-tauri/', 'ui/', 'public-core-bridge/')


def classify(path: Path, text: str) -> list[dict[str, object]]:
    findings: list[dict[str, object]] = []
    rel = path.as_posix()
    lines = text.splitlines()
    for line_no, line in enumerate(lines, start=1):
        lowered = line.lower()
        for term in FORBIDDEN_TERMS:
            if term not in lowered:
                continue
            allowed = path.name in ALLOWED_DOCS and any(marker in lowered for marker in ALLOWED_NEGATIVE)
            blocked = rel.startswith(BLOCKED_PREFIXES)
            classification = 'allowed_boundary' if allowed else 'blocked' if blocked else 'review_required'
            findings.append({
                'path': rel,
                'line': line_no,
                'term': term,
                'classification': classification,
            })
    return findings


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    findings: list[dict[str, object]] = []
    for path in root.rglob('*'):
        if path.is_dir():
            continue
        rel = path.relative_to(root)
        if '.git' in rel.parts or '.tmp' in rel.parts or '__pycache__' in rel.parts:
            continue
        if path.suffix.lower() not in {'.md', '.py', '.json', '.rs', '.tsx', '.ts', '.jsx', '.js', '.html', '.toml', '.css', '.yml', '.yaml'}:
            continue
        text = path.read_text(encoding='utf-8', errors='ignore')
        findings.extend(classify(rel, text))
    blocked = [item for item in findings if item['classification'] == 'blocked']
    report = {
        'schema_version': 1,
        'report_id': 'zephyr.base.boundary_check.v1',
        'summary': {
            'pass': len(blocked) == 0,
            'blocked_count': len(blocked),
            'review_required_count': sum(1 for item in findings if item['classification'] == 'review_required'),
            'allowed_boundary_count': sum(1 for item in findings if item['classification'] == 'allowed_boundary'),
        },
        'findings': findings,
    }
    out = root / '.tmp' / 'base_boundary_check.json'
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if len(blocked) == 0 else 1


if __name__ == '__main__':
    raise SystemExit(main())
