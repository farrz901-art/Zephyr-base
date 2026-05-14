from __future__ import annotations

import argparse
import json
from pathlib import Path


REQUIRED_DOCS = (
    Path("docs/BASE_MVP_PRODUCT_TRUTH.md"),
    Path("docs/BASE_M3_DISTRIBUTION_DECISION.md"),
    Path("docs/BASE_M3_EVIDENCE_MATRIX.md"),
    Path("docs/BASE_M3_READINESS_REPORT.md"),
    Path("docs/BASE_M3_FINAL_SEAL.md"),
    Path("docs/BASE_M3_REAL_USER_PROOF_REUSE.md"),
)


def _write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _read_json(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Check the Base M3 final seal state.")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)

    root = Path(__file__).resolve().parents[1]
    final_manifest_path = root / "manifests/base_m3_final_seal.json"
    imported_proof_path = root / ".tmp/imported_external_package_ux_proof_report.json"
    readiness_path = root / ".tmp/base_m3_readiness/report.json"
    overclaim_path = root / ".tmp/base_m3_overclaim_check.json"
    package_report_path = root / ".tmp/windows_installer_package_report.json"

    missing = [path.as_posix() for path in REQUIRED_DOCS if not (root / path).exists()]
    for required in (
        final_manifest_path,
        imported_proof_path,
        readiness_path,
        overclaim_path,
        package_report_path,
    ):
        if not required.exists():
            missing.append(required.relative_to(root).as_posix())

    final_manifest = _read_json(final_manifest_path) if final_manifest_path.exists() else {}
    imported_proof = _read_json(imported_proof_path) if imported_proof_path.exists() else {}
    readiness = _read_json(readiness_path) if readiness_path.exists() else {}
    overclaim = _read_json(overclaim_path) if overclaim_path.exists() else {}
    package_report = _read_json(package_report_path) if package_report_path.exists() else {}

    summary = final_manifest.get("summary", {})
    proof_reuse = final_manifest.get("proof_reuse", {})
    delivery = final_manifest.get("delivery", {})
    scope = final_manifest.get("scope", {})
    capability = final_manifest.get("capability", {})

    unsupported_claims = {
        "pdf_claimed": capability.get("pdf") is not False,
        "docx_claimed": capability.get("docx") is not False,
        "image_or_ocr_claimed": capability.get("image_or_ocr") is not False,
        "html_claimed": capability.get("html") is not False,
        "cloud_claimed": capability.get("cloud") is not False,
        "pro_claimed": capability.get("pro") is not False,
        "license_or_entitlement_claimed": capability.get("license_or_entitlement") is not False,
        "payment_or_billing_claimed": capability.get("payment_or_billing") is not False,
    }

    pass_state = (
        not missing
        and imported_proof.get("summary", {}).get("manual_gui_proof_pass") is True
        and readiness.get("summary", {}).get("pass") is True
        and overclaim.get("summary", {}).get("pass") is True
        and package_report.get("manifest", {}).get("package_kind") == "portable_zip"
        and summary.get("go") is True
        and summary.get("p6_m3_final_status") == "sealed"
        and summary.get("allowed_next_phase") == "P6-M4"
        and proof_reuse.get("manual_gui_retest_required") is False
        and scope.get("signed_installer") is False
        and scope.get("official_release") is False
        and scope.get("auto_update") is False
        and scope.get("runtime_capability_changed") is False
        and not any(unsupported_claims.values())
        and delivery.get("artifact_kind") == "unsigned_portable_zip_preview"
    )

    report = {
        "schema_version": 1,
        "report_id": "zephyr.base.s19.base_m3_final_seal_check.v1",
        "summary": {
            "pass": pass_state,
            "go": summary.get("go") is True,
            "p6_m3_final_status": summary.get("p6_m3_final_status"),
            "allowed_next_phase": summary.get("allowed_next_phase"),
        },
        "missing_files": missing,
        "proof_reuse": {
            "s17_external_user_proof_reused": proof_reuse.get("s17_external_user_proof_reused"),
            "s17_external_user_proof_pass": proof_reuse.get("s17_external_user_proof_pass"),
            "s18_closure_audit_pass": proof_reuse.get("s18_closure_audit_pass"),
            "manual_gui_retest_required": proof_reuse.get("manual_gui_retest_required"),
        },
        "scope": scope,
        "delivery": delivery,
        "unsupported_claims": unsupported_claims,
    }

    out = root / ".tmp/base_m3_final_seal_check.json"
    _write_json(out, report)
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if pass_state else 1


if __name__ == "__main__":
    raise SystemExit(main())
