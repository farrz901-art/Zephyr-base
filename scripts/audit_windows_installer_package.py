from __future__ import annotations

import argparse
import json
from pathlib import Path


DEFAULT_PACKAGE_ROOT = Path(".tmp/windows_installer_package/ZephyrBase")
DEFAULT_MANIFEST = Path(".tmp/windows_installer_package/installer_manifest.json")
DEFAULT_ZIP = Path(".tmp/windows_installer_package/ZephyrBase-windows-unsigned.zip")
FORBIDDEN_TERMS = [
    "license_verify",
    "entitlement_server",
    "payment_callback",
    "billing_decision",
    "quota_authority",
    "risk_score",
    "web_core.internal",
    "private_core_export",
    "zephyr_pro",
]
FORBIDDEN_DIRS = [
    ".git",
    "node_modules",
    "target",
    ".tmp/base_runtime_venv",
    ".tmp/imported_clean_machine_proof",
    ".tmp/imported_offline_runtime_proof",
    "src-tauri/gen",
    ".idea",
]


def _write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _read_json(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def _text_files(root: Path) -> list[Path]:
    allowed = {".md", ".txt", ".json", ".py", ".cmd", ".html", ".css", ".js"}
    return [path for path in root.rglob("*") if path.is_file() and path.suffix.lower() in allowed]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Audit the S15 Windows installer package contents.")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)

    root = Path(__file__).resolve().parents[1]
    package_root = (root / DEFAULT_PACKAGE_ROOT).resolve()
    manifest_path = (root / DEFAULT_MANIFEST).resolve()
    zip_path = (root / DEFAULT_ZIP).resolve()
    manifest = _read_json(manifest_path) if manifest_path.exists() else {}

    required = {
        "ui_dist": package_root / "app/ui/dist/index.html",
        "tauri_app": package_root / "app/zephyr-base-tauri-bridge.exe",
        "public_core_bundle": package_root / "runtime/public-core-bundle",
        "runtime_manifest": package_root / "runtime/python-runtime/runtime_manifest.json",
        "wheelhouse": package_root / "runtime/wheelhouse",
        "bootstrap": package_root / "checks/run_windows_package_install_proof.py",
        "docs": package_root / "docs/WINDOWS_INSTALLER_PACKAGING_POLICY.md",
    }
    missing = [name for name, path in required.items() if not path.exists()]
    forbidden_present = [
        item
        for item in FORBIDDEN_DIRS
        if (package_root / item).exists()
    ]
    findings: list[dict[str, object]] = []
    for text_path in _text_files(package_root):
        relative = text_path.relative_to(package_root)
        if relative.parts and relative.parts[0].lower() == "docs":
            continue
        try:
            content = text_path.read_text(encoding="utf-8", errors="ignore").lower()
        except OSError:
            continue
        for term in FORBIDDEN_TERMS:
            if term in content:
                findings.append({"path": str(relative), "term": term})
    passed = (
        zip_path.exists()
        and manifest_path.exists()
        and not missing
        and not forbidden_present
        and not findings
        and manifest.get("signed_installer") is False
        and manifest.get("release_created") is False
    )
    report = {
        "schema_version": 1,
        "report_id": "zephyr.base.s15.windows_installer_package_audit.v1",
        "summary": {
            "pass": passed,
            "zip_exists": zip_path.exists(),
            "manifest_exists": manifest_path.exists(),
            "required_files_present": not missing,
            "forbidden_dirs_present": bool(forbidden_present),
            "findings_count": len(findings),
        },
        "missing": missing,
        "forbidden_dirs_present": forbidden_present,
        "findings": findings,
    }
    _write_json(root / ".tmp/windows_installer_package_audit.json", report)
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
