from __future__ import annotations

import argparse
import json
from pathlib import Path


def _write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _read_json(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Check the S15 Windows installer baseline.")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)

    root = Path(__file__).resolve().parents[1]
    policy = root / "docs/WINDOWS_INSTALLER_PACKAGING_POLICY.md"
    schema = root / "packaging/windows/installer_manifest.schema.json"
    readme = root / "packaging/windows/README.md"
    builder = root / "scripts/build_windows_installer_package.py"
    audit = root / "scripts/audit_windows_installer_package.py"
    smoke = root / "scripts/run_windows_install_smoke.py"
    manifest_path = root / ".tmp/windows_installer_package/installer_manifest.json"
    zip_path = root / ".tmp/windows_installer_package/ZephyrBase-windows-unsigned.zip"
    manifest = _read_json(manifest_path) if manifest_path.exists() else {}
    passed = all(
        (
            policy.exists(),
            schema.exists(),
            readme.exists(),
            builder.exists(),
            audit.exists(),
            smoke.exists(),
            manifest_path.exists(),
            zip_path.exists(),
            manifest.get("installer_built") is True,
            manifest.get("signed_installer") is False,
            manifest.get("release_created") is False,
            manifest.get("embedded_python_runtime") is False,
        )
    )
    report = {
        "schema_version": 1,
        "report_id": "zephyr.base.s15.windows_installer_baseline_check.v1",
        "summary": {
            "pass": passed,
            "policy_exists": policy.exists(),
            "schema_exists": schema.exists(),
            "builder_exists": builder.exists(),
            "audit_exists": audit.exists(),
            "smoke_exists": smoke.exists(),
            "package_exists": zip_path.exists(),
            "manifest_exists": manifest_path.exists(),
        },
    }
    _write_json(root / ".tmp/windows_installer_baseline_check.json", report)
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
