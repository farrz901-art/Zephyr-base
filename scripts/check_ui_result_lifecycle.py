from __future__ import annotations

import argparse
import json
from pathlib import Path

REQUIRED_CONTRACT_MARKERS = (
    "BaseRunResultV1",
    "BaseReceiptViewV1",
    "BaseUsageFactV1",
    "BaseContentEvidenceV1",
    "BaseErrorV1",
    "LineageSnapshotV1",
    "RuntimeModeSummary",
)
REQUIRED_RESULT_FIELDS = (
    "schema_version",
    "request_id",
    "status",
    "normalized_text_preview",
    "receipt",
    "usage_fact",
    "output_files",
    "error",
)


def _read_text(path: Path) -> str:
    raw = path.read_bytes()
    if raw.startswith(b"\xff\xfe") or raw.startswith(b"\xfe\xff"):
        return raw.decode("utf-16")
    if raw.startswith(b"\xef\xbb\xbf"):
        return raw.decode("utf-8-sig")
    return raw.decode("utf-8")


def _write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _load_json(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def _has_required_result_shape(payload: dict[str, object]) -> bool:
    return all(field in payload for field in REQUIRED_RESULT_FIELDS) and (
        "content_evidence_summary" in payload or "content_evidence" in payload
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Check the Zephyr-base UI result lifecycle coverage.")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)

    root = Path(__file__).resolve().parents[1]
    contract_text = _read_text(root / "ui/src/contracts/baseRunResult.ts")
    sample_success_text = _read_text(root / "ui/src/fixtures/sampleRunResult.ts")
    sample_error_text = _read_text(root / "ui/src/fixtures/sampleErrorResult.ts")
    ui_text = "\n".join(
        _read_text(path)
        for path in (root / "ui/src").rglob("*")
        if path.is_file()
    )

    candidates = [
        root / ".tmp/s9_tauri_app_path/run_result.json",
        root / ".tmp/s8_tauri_bridge_cli_flow/run_result.json",
    ]
    real_run_result_path = next((path for path in candidates if path.exists()), None)
    real_run_result = _load_json(real_run_result_path) if real_run_result_path else None

    lifecycle_pass = all(marker in contract_text for marker in REQUIRED_CONTRACT_MARKERS)
    sample_success_consumed = 'status: "success"' in sample_success_text and "billing_semantics: false" in sample_success_text
    sample_error_consumed = 'status: "failed"' in sample_error_text and "secret_safe: true" in sample_error_text
    real_run_result_consumed = real_run_result is not None and _has_required_result_shape(real_run_result)
    display_model_fields_covered = all(
        marker in ui_text
        for marker in (
            "ResultSummary",
            "NormalizedTextPreview",
            "EvidenceCard",
            "ReceiptCard",
            "UsageFactCard",
            "ErrorDiagnosisPanel",
            "OutputFolderPlan",
            "LineageStatusCard",
            "extractDisplayModel",
        )
    )
    error_display_covered = "ErrorDiagnosisPanel" in ui_text
    output_folder_plan_covered = "OutputFolderPlan" in ui_text

    if real_run_result is not None:
        usage_fact = real_run_result.get("usage_fact", {})
        if not isinstance(usage_fact, dict) or usage_fact.get("billing_semantics") is not False:
            lifecycle_pass = False

    report = {
        "schema_version": 1,
        "report_id": "zephyr.base.s16.ui_result_lifecycle_check.v1",
        "summary": {
            "pass": all(
                (
                    lifecycle_pass,
                    sample_success_consumed,
                    sample_error_consumed,
                    display_model_fields_covered,
                    error_display_covered,
                    output_folder_plan_covered,
                )
            ) and (real_run_result_consumed if real_run_result_path else True),
            "real_run_result_consumed": real_run_result_consumed,
            "sample_success_consumed": sample_success_consumed,
            "sample_error_consumed": sample_error_consumed,
            "display_model_fields_covered": display_model_fields_covered,
            "error_display_covered": error_display_covered,
            "output_folder_plan_covered": output_folder_plan_covered,
        },
        "real_run_result_path": real_run_result_path.as_posix() if real_run_result_path else None,
    }
    _write_json(root / ".tmp/ui_result_lifecycle_check.json", report)
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["summary"]["pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
