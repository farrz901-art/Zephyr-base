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
    parser = argparse.ArgumentParser(description="Validate an external package UX proof.")
    parser.add_argument("--proof", type=Path, required=True)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)

    root = Path(__file__).resolve().parents[1]
    proof_path = args.proof if args.proof.is_absolute() else (root / args.proof).resolve()
    if not proof_path.exists():
        raise FileNotFoundError(proof_path)

    proof = _read_json(proof_path)
    package = proof.get("package", {}) if isinstance(proof.get("package"), dict) else {}
    ui = proof.get("ui", {}) if isinstance(proof.get("ui"), dict) else {}
    runtime = proof.get("runtime", {}) if isinstance(proof.get("runtime"), dict) else {}
    truth_boundary = proof.get("truth_boundary", {}) if isinstance(proof.get("truth_boundary"), dict) else {}
    scope = proof.get("scope", {}) if isinstance(proof.get("scope"), dict) else {}

    passed = all(
        (
            package.get("package_kind") == "portable_zip",
            package.get("launched_from_external_dir") is True,
            package.get("git_repo_required") is False,
            package.get("zephyr_dev_required") is False,
            ui.get("window_launched") is True,
            ui.get("language_toggle_visible") is True,
            ui.get("english_visible") is True,
            ui.get("chinese_visible") is True,
            ui.get("switched_to_chinese") is True,
            ui.get("switched_back_to_english") is True,
            ui.get("primary_run_button_visible") is True,
            ui.get("advanced_collapsed_by_default") is True,
            ui.get("advanced_expanded") is True,
            runtime.get("text_flow_pass") is True,
            runtime.get("file_flow_pass") is True,
            runtime.get("text_marker_found") is True,
            runtime.get("file_marker_found") is True,
            runtime.get("normalized_preview_visible") is True,
            runtime.get("output_location_visible") is True,
            runtime.get("receipt_visible_in_advanced") is True,
            runtime.get("evidence_visible_in_advanced") is True,
            runtime.get("usage_fact_visible_in_advanced") is True,
            runtime.get("lineage_visible_in_advanced") is True,
            runtime.get("billing_semantics") is False,
            runtime.get("requires_network_at_runtime") is False,
            runtime.get("requires_p45_substrate") is False,
            truth_boundary.get("pdf_claimed") is False,
            truth_boundary.get("docx_claimed") is False,
            truth_boundary.get("image_or_ocr_claimed") is False,
            truth_boundary.get("cloud_claimed") is False,
            truth_boundary.get("login_claimed") is False,
            truth_boundary.get("license_or_entitlement_claimed") is False,
            truth_boundary.get("payment_or_billing_claimed") is False,
            scope.get("signed_installer") is False,
            scope.get("official_release") is False,
            scope.get("auto_update") is False,
            scope.get("runtime_capability_changed") is False,
        )
    )
    report = {
        "schema_version": 1,
        "report_id": "zephyr.base.s17.external_package_ux_proof_validation.v1",
        "summary": {
            "pass": passed,
            "window_launched": ui.get("window_launched") is True,
            "language_toggle_visible": ui.get("language_toggle_visible") is True,
            "text_flow_pass": runtime.get("text_flow_pass") is True,
            "file_flow_pass": runtime.get("file_flow_pass") is True,
        },
        "proof_path": str(proof_path),
        "proof": proof,
    }
    _write_json(root / ".tmp/external_package_ux_proof_validation.json", report)
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
