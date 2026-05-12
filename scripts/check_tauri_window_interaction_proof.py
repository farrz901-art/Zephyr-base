from __future__ import annotations

import argparse
import json
from pathlib import Path

from marker_detection import detect_marker_in_output

OUTPUT_ROOT = Path(".tmp/s10_tauri_window_interaction")
PROOF_NAME = "ui_interaction_proof.json"
RUN_RESULT_NAME = "run_result.json"


def _write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _load_json(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Check S10 Tauri window interaction proof artifacts.")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)

    root = Path(__file__).resolve().parents[1]
    proof_path = root / OUTPUT_ROOT / PROOF_NAME
    run_result_path = root / OUTPUT_ROOT / RUN_RESULT_NAME
    proof_exists = proof_path.exists()
    run_result_exists = run_result_path.exists()

    proof = _load_json(proof_path) if proof_exists else {}
    run_result = _load_json(run_result_path) if run_result_exists else {}
    usage_fact = run_result.get("usage_fact", {}) if isinstance(run_result, dict) else {}
    if not isinstance(usage_fact, dict):
        usage_fact = {}

    marker = str(proof.get("marker", ""))
    marker_report = detect_marker_in_output(output_dir=root / OUTPUT_ROOT, run_result=run_result, marker=marker)
    marker_found = marker_report["marker_found"] is True

    pass_checks = all(
        (
            proof_exists,
            run_result_exists,
            proof.get("window_launched") is True,
            proof.get("user_clicked_run") is True,
            proof.get("tauri_invoke_used") is True,
            proof.get("direct_python_call") is False,
            proof.get("network_call") is False,
            proof.get("normalized_preview_visible") is True,
            proof.get("evidence_visible") is True,
            proof.get("receipt_visible") is True,
            proof.get("usage_fact_visible") is True,
            proof.get("billing_semantics_displayed_false") is True,
            proof.get("output_folder_plan_visible") is True,
            proof.get("error_panel_available") is True,
            usage_fact.get("billing_semantics") is False,
            run_result.get("bundled_runtime_used") is True,
            run_result.get("fixture_runner_used") is False,
            run_result.get("zephyr_dev_working_tree_required") is False,
            run_result.get("requires_network") is False,
            run_result.get("requires_p45_substrate") is False,
            marker_found,
        )
    )

    report = {
        "schema_version": 1,
        "report_id": "zephyr.base.s10.window_interaction_proof_check.v1",
        "summary": {
            "pass": pass_checks,
            "proof_exists": proof_exists,
            "run_result_exists": run_result_exists,
            "marker_found": marker_found,
        },
        "proof": proof,
        "marker_detection": marker_report,
        "run_result_path": run_result_path.as_posix(),
    }
    out_path = root / ".tmp" / "tauri_window_interaction_proof_check.json"
    _write_json(out_path, report)
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if pass_checks else 1


if __name__ == "__main__":
    raise SystemExit(main())
