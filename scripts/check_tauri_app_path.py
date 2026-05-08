from __future__ import annotations

import argparse
import json
import shutil
import subprocess
from pathlib import Path

MARKER = "ZEPHYR_BASE_S9_TAURI_APP_PATH_MARKER"
OUTPUT_DIR = Path(".tmp/s9_tauri_app_path")


def _write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _run(command: list[str], cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        command,
        cwd=cwd,
        check=False,
        capture_output=True,
        text=True,
    )


def _load_json(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Check the Zephyr-base visible Tauri app path.")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)

    root = Path(__file__).resolve().parents[1]
    cargo = shutil.which("cargo")
    cargo_available = cargo is not None

    ui_build_script = root / "scripts/check_ui_build.py"
    ui_build_completed = _run(["python", str(ui_build_script), "--json"], root)
    ui_build_pass = ui_build_completed.returncode == 0
    ui_build_report = _load_json(root / ".tmp/ui_build_check.json") if (root / ".tmp/ui_build_check.json").exists() else {}

    cargo_check_pass = False
    cargo_check_detail = "cargo not available"
    if cargo_available:
        cargo_check_completed = _run([cargo, "check", "--manifest-path", "src-tauri/Cargo.toml"], root)
        cargo_check_pass = cargo_check_completed.returncode == 0
        cargo_check_detail = (cargo_check_completed.stdout + "\n" + cargo_check_completed.stderr).strip()

    commands_text = (root / "src-tauri/src/commands.rs").read_text(encoding="utf-8", errors="ignore")
    main_text = (root / "src-tauri/src/main.rs").read_text(encoding="utf-8", errors="ignore")
    tauri_conf_text = (root / "src-tauri/tauri.conf.json").read_text(encoding="utf-8", errors="ignore")
    tauri_command_registration_pass = (
        "#[tauri::command]" in commands_text
        and "tauri::Builder::default()" in main_text
        and "tauri::generate_handler!" in main_text
        and "../ui/dist" in tauri_conf_text
        and "commands::write_interaction_proof" in main_text
    )

    output_dir = root / OUTPUT_DIR
    if output_dir.exists():
        shutil.rmtree(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    cargo_run_local_text_pass = False
    run_stdout = ""
    run_stderr = ""
    if cargo_available and cargo_check_pass:
        cargo_run_completed = _run(
            [
                cargo,
                "run",
                "--manifest-path",
                "src-tauri/Cargo.toml",
                "--",
                "run-local-text",
                MARKER,
                OUTPUT_DIR.as_posix(),
            ],
            root,
        )
        cargo_run_local_text_pass = cargo_run_completed.returncode == 0
        run_stdout = cargo_run_completed.stdout.strip()
        run_stderr = cargo_run_completed.stderr.strip()

    launch_report_path = root / ".tmp" / "tauri_window_launch_attempt.json"
    launch_report = _load_json(launch_report_path) if launch_report_path.exists() else {}
    launch_summary = launch_report.get("summary", {}) if isinstance(launch_report, dict) else {}
    if not isinstance(launch_summary, dict):
        launch_summary = {}

    run_result_path = output_dir / "run_result.json"
    run_result = _load_json(run_result_path) if run_result_path.exists() else {}
    usage_fact = run_result.get("usage_fact", {}) if isinstance(run_result, dict) else {}
    if not isinstance(usage_fact, dict):
        usage_fact = {}

    marker_found = MARKER in str(run_result.get("normalized_text_preview", ""))
    rust_cli_lifecycle_pass = all(
        (
            cargo_available,
            cargo_check_pass,
            cargo_run_local_text_pass,
            run_result_path.exists(),
            marker_found,
            usage_fact.get("billing_semantics") is False,
            run_result.get("bundled_runtime_used") is True,
            run_result.get("fixture_runner_used") is False,
            run_result.get("zephyr_dev_working_tree_required") is False,
            run_result.get("requires_network") is False,
            run_result.get("requires_p45_substrate") is False,
        )
    )

    report = {
        "schema_version": 1,
        "report_id": "zephyr.base.s10.tauri_app_path_check.v1",
        "summary": {
            "pass": ui_build_pass and cargo_check_pass and tauri_command_registration_pass and rust_cli_lifecycle_pass,
            "ui_build_pass": ui_build_pass,
            "cargo_check_pass": cargo_check_pass,
            "tauri_command_registration_pass": tauri_command_registration_pass,
            "rust_cli_lifecycle_pass": rust_cli_lifecycle_pass,
            "tauri_window_launch_attempted": launch_summary.get("tauri_window_launch_attempted", False),
            "tauri_window_click_e2e_verified": launch_summary.get("tauri_window_click_e2e_verified", False),
        },
        "ui_build": ui_build_report.get("summary", {}),
        "tauri_app_path": {
            "cargo_available": cargo_available,
            "cargo_check_pass": cargo_check_pass,
            "tauri_command_registration_pass": tauri_command_registration_pass,
            "rust_cli_lifecycle_pass": rust_cli_lifecycle_pass,
            "tauri_window_launch_attempted": launch_summary.get("tauri_window_launch_attempted", False),
            "tauri_window_click_e2e_verified": launch_summary.get("tauri_window_click_e2e_verified", False),
            "launch_process_started": launch_summary.get("tauri_window_launch_process_started", False),
            "launch_reason": launch_report.get("launch", {}).get("reason") if isinstance(launch_report.get("launch"), dict) else None,
        },
        "local_run_lifecycle": {
            "marker_found": marker_found,
            "run_result_exists": run_result_path.exists(),
            "billing_semantics": usage_fact.get("billing_semantics"),
            "bundled_runtime_used": run_result.get("bundled_runtime_used"),
            "fixture_runner_used": run_result.get("fixture_runner_used"),
            "zephyr_dev_working_tree_required": run_result.get("zephyr_dev_working_tree_required"),
        },
        "runtime": {
            "uses_bundled_adapter": True,
            "uses_current_python_environment": True,
            "embedded_python_runtime": False,
            "wheelhouse_bundled": False,
            "installer_runtime_complete": False,
        },
        "boundary": {
            "requires_network": False,
            "requires_p45_substrate": False,
            "fixture_runner_used": False,
            "zephyr_dev_working_tree_required": False,
        },
        "cargo": {
            "check_detail": cargo_check_detail,
            "run_stdout": run_stdout,
            "run_stderr": run_stderr,
        },
    }
    out_path = root / ".tmp" / "tauri_app_path_check.json"
    _write_json(out_path, report)
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["summary"]["pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
