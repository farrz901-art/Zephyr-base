from __future__ import annotations

import argparse
import json
import shutil
import subprocess
from pathlib import Path

from marker_detection import build_long_marker_text, detect_marker_in_output

MARKER = "ZEPHYR_BASE_S8_TAURI_BRIDGE_MARKER"
OUTPUT_DIR = Path(".tmp/s8_tauri_bridge_cli_flow")
REPORT_PATH = Path(".tmp/s8_tauri_bridge_cli_flow_check.json")


def _write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _cargo_check(root: Path) -> tuple[bool, bool, str]:
    cargo = shutil.which("cargo")
    if cargo is None:
        return False, False, "cargo not available"
    completed = subprocess.run(
        [cargo, "check", "--manifest-path", "src-tauri/Cargo.toml"],
        cwd=root,
        check=False,
        capture_output=True,
        text=True,
    )
    detail = (completed.stdout + "\n" + completed.stderr).strip()
    return True, completed.returncode == 0, detail


def _cargo_run(root: Path, output_dir: Path) -> tuple[bool, str, str]:
    cargo = shutil.which("cargo")
    if cargo is None:
        return False, "", "cargo not available"
    completed = subprocess.run(
        [
            cargo,
            "run",
            "--manifest-path",
            "src-tauri/Cargo.toml",
            "--",
            "run-local-text",
            build_long_marker_text(MARKER, "Rust bridge CLI flow"),
            output_dir.as_posix(),
        ],
        cwd=root,
        check=False,
        capture_output=True,
        text=True,
    )
    return completed.returncode == 0, completed.stdout.strip(), completed.stderr.strip()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run the Zephyr-base S8 Rust bridge CLI flow.")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)

    root = Path(__file__).resolve().parents[1]
    output_dir = root / OUTPUT_DIR
    if output_dir.exists():
        shutil.rmtree(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    cargo_available, cargo_check_pass, cargo_detail = _cargo_check(root)
    cargo_run_pass = False
    stdout_text = ""
    stderr_text = ""
    run_result: dict[str, object] = {}
    run_result_path = output_dir / "run_result.json"
    if cargo_available and cargo_check_pass:
        cargo_run_pass, stdout_text, stderr_text = _cargo_run(root, OUTPUT_DIR)
        if run_result_path.exists():
            run_result = json.loads(run_result_path.read_text(encoding="utf-8"))

    marker_report = detect_marker_in_output(output_dir=output_dir, run_result=run_result, marker=MARKER)
    marker_found = marker_report["marker_found"] is True
    usage_fact = run_result.get("usage_fact", {}) if isinstance(run_result, dict) else {}
    if not isinstance(usage_fact, dict):
        usage_fact = {}
    receipt = run_result.get("receipt", {}) if isinstance(run_result, dict) else {}
    if not isinstance(receipt, dict):
        receipt = {}

    report = {
        "schema_version": 1,
        "report_id": "zephyr.base.s8.tauri_bridge_cli_flow_check.v1",
        "summary": {
            "pass": all(
                (
                    cargo_available,
                    cargo_check_pass,
                    cargo_run_pass,
                    run_result_path.exists(),
                    marker_found,
                    usage_fact.get("billing_semantics") is False,
                    run_result.get("bundled_runtime_used") is True,
                    run_result.get("fixture_runner_used") is False,
                    run_result.get("zephyr_dev_working_tree_required") is False,
                    run_result.get("requires_network") is False,
                    run_result.get("requires_p45_substrate") is False,
                )
            ),
            "cargo_available": cargo_available,
            "cargo_check_pass": cargo_check_pass,
            "cargo_run_local_text_pass": cargo_run_pass,
            "run_result_exists": run_result_path.exists(),
            "marker_found": marker_found,
            "billing_semantics": usage_fact.get("billing_semantics"),
            "bundled_runtime_used": run_result.get("bundled_runtime_used"),
            "fixture_runner_used": run_result.get("fixture_runner_used"),
            "zephyr_dev_working_tree_required": run_result.get("zephyr_dev_working_tree_required"),
            "requires_network": run_result.get("requires_network"),
            "requires_p45_substrate": run_result.get("requires_p45_substrate"),
        },
        "cargo": {
            "check_detail": cargo_detail,
            "run_stdout": stdout_text,
            "run_stderr": stderr_text,
        },
        "marker_detection": marker_report,
        "receipt": receipt,
        "run_result_path": run_result_path.as_posix(),
    }
    _write_json(root / REPORT_PATH, report)
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["summary"]["pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
