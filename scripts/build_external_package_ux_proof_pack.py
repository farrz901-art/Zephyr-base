from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path


DEFAULT_PROOF_ROOT = Path(".tmp/external_package_ux_proof")
DEFAULT_PACKAGE = Path(".tmp/windows_installer_package/ZephyrBase-windows-unsigned.zip")


def _write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _run(command: list[str], cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(command, cwd=cwd, check=False, capture_output=True, text=True)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build the S17 external package UX proof pack.")
    parser.add_argument("--proof-root", type=Path, default=DEFAULT_PROOF_ROOT)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)

    root = Path(__file__).resolve().parents[1]
    package_path = root / DEFAULT_PACKAGE
    if not package_path.exists():
        completed = _run([sys.executable, str(root / "scripts/build_windows_installer_package.py"), "--json"], root)
        if completed.returncode != 0:
            raise RuntimeError(completed.stderr.strip() or "build_windows_installer_package.py failed")
    if not package_path.exists():
        raise FileNotFoundError(package_path)

    proof_root = args.proof_root if args.proof_root.is_absolute() else (root / args.proof_root).resolve()
    if proof_root.exists():
        shutil.rmtree(proof_root)
    proof_root.mkdir(parents=True, exist_ok=True)

    shutil.copy2(package_path, proof_root / package_path.name)
    shutil.copy2(root / "docs/MANUAL_BASE_UX_SMOKE.md", proof_root / "MANUAL_BASE_UX_SMOKE.md")
    shutil.copy2(root / "docs/BASE_EXTERNAL_UX_SMOKE_POLICY.md", proof_root / "BASE_EXTERNAL_UX_SMOKE_POLICY.md")
    shutil.copy2(root / "docs/MANUAL_EXTERNAL_PACKAGE_UX_PROOF.md", proof_root / "MANUAL_EXTERNAL_PACKAGE_UX_PROOF.md")

    template = {
        "schema_version": 1,
        "report_id": "zephyr.base.s17.external_package_ux_proof.v1",
        "proof_kind": "manual_external_package_ux",
        "package": {
            "package_kind": "portable_zip",
            "package_path": str(package_path),
            "external_extract_root": "D:/ZephyrBaseUxProof/ZephyrBase",
            "launched_from_external_dir": False,
            "git_repo_required": False,
            "zephyr_dev_required": False,
        },
        "ui": {
            "window_launched": False,
            "language_toggle_visible": False,
            "english_visible": False,
            "chinese_visible": False,
            "switched_to_chinese": False,
            "switched_back_to_english": False,
            "primary_run_button_visible": False,
            "advanced_collapsed_by_default": False,
            "advanced_expanded": False,
        },
        "runtime": {
            "text_flow_pass": False,
            "file_flow_pass": False,
            "text_marker_found": False,
            "file_marker_found": False,
            "normalized_preview_visible": False,
            "output_location_visible": False,
            "receipt_visible_in_advanced": False,
            "evidence_visible_in_advanced": False,
            "usage_fact_visible_in_advanced": False,
            "lineage_visible_in_advanced": False,
            "billing_semantics": False,
            "requires_network_at_runtime": False,
            "requires_p45_substrate": False,
        },
        "truth_boundary": {
            "pdf_claimed": False,
            "docx_claimed": False,
            "image_or_ocr_claimed": False,
            "cloud_claimed": False,
            "login_claimed": False,
            "license_or_entitlement_claimed": False,
            "payment_or_billing_claimed": False,
        },
        "scope": {
            "signed_installer": False,
            "official_release": False,
            "auto_update": False,
            "runtime_capability_changed": False,
        },
        "attachments": {
            "screenshots": [],
            "notes": [],
        },
    }
    _write_json(proof_root / "external_package_ux_proof.template.json", template)

    manifest = {
        "schema_version": 1,
        "report_id": "zephyr.base.s17.external_package_ux_proof_pack_manifest.v1",
        "base_repo_sha": json.loads((root / ".tmp/windows_installer_package_report.json").read_text(encoding="utf-8")).get("manifest", {}).get("base_repo_sha", "unknown")
        if (root / ".tmp/windows_installer_package_report.json").exists()
        else "unknown",
        "package_path": str(package_path),
        "proof_level": "manual_or_semiautomated_external_ux",
        "requires_signed_installer": False,
        "requires_release": False,
        "requires_network_runtime": False,
        "requires_login": False,
        "runtime_capability_changed": False,
    }
    report = {
        "schema_version": 1,
        "report_id": "zephyr.base.s17.external_package_ux_proof_pack.v1",
        "summary": {
            "pass": True,
            "package_exists": True,
            "proof_pack_built": True,
        },
        "proof_root": str(proof_root),
        "manifest": manifest,
    }
    _write_json(root / ".tmp/external_package_ux_proof_pack_manifest.json", manifest)
    _write_json(root / ".tmp/external_package_ux_proof_pack_report.json", report)
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
