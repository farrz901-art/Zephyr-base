from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import time
from pathlib import Path


def _write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _run(command: list[str], cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(command, cwd=cwd, check=False, capture_output=True, text=True)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Attempt a bounded Tauri window launch for S10.")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)

    root = Path(__file__).resolve().parents[1]
    cargo = shutil.which("cargo")
    cargo_available = cargo is not None

    ui_build = _run(["python", "scripts/check_ui_build.py", "--json"], root)
    ui_build_pass = ui_build.returncode == 0

    cargo_check_pass = False
    cargo_check_detail = "cargo not available"
    if cargo_available:
        cargo_check = _run([cargo, "check", "--manifest-path", "src-tauri/Cargo.toml"], root)
        cargo_check_pass = cargo_check.returncode == 0
        cargo_check_detail = (cargo_check.stdout + "\n" + cargo_check.stderr).strip()

    tauri_window_launch_attempted = cargo_available and cargo_check_pass and ui_build_pass
    tauri_window_launch_process_started = False
    tauri_window_click_e2e_verified = False
    launch_reason = "launch not attempted"

    if tauri_window_launch_attempted:
        process = None
        try:
            process = subprocess.Popen(
                [cargo, "run", "--manifest-path", "src-tauri/Cargo.toml"],
                cwd=root,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )
            deadline = time.time() + 20
            while time.time() < deadline:
                if process.poll() is not None:
                    break
                time.sleep(1)
            tauri_window_launch_process_started = process.poll() is None
            launch_reason = (
                "cargo run started a visible Tauri process; click automation is still not claimed."
                if tauri_window_launch_process_started
                else "cargo run exited before a stable visible launch could be confirmed."
            )
        except OSError as error:
            launch_reason = f"Environment limitation during launch attempt: {error}"
        finally:
            if process is not None and process.poll() is None:
                process.terminate()
                try:
                    process.wait(timeout=8)
                except subprocess.TimeoutExpired:
                    process.kill()

    report = {
        "schema_version": 1,
        "report_id": "zephyr.base.s10.tauri_window_launch_attempt.v1",
        "summary": {
            "pass": ui_build_pass and cargo_check_pass,
            "ui_build_pass": ui_build_pass,
            "cargo_check_pass": cargo_check_pass,
            "tauri_window_launch_attempted": tauri_window_launch_attempted,
            "tauri_window_launch_process_started": tauri_window_launch_process_started,
            "tauri_window_click_e2e_verified": tauri_window_click_e2e_verified,
        },
        "launch": {
            "cargo_available": cargo_available,
            "tauri_window_launch_attempted": tauri_window_launch_attempted,
            "tauri_window_launch_process_started": tauri_window_launch_process_started,
            "tauri_window_click_e2e_verified": tauri_window_click_e2e_verified,
            "reason": launch_reason,
        },
        "cargo": {
            "cargo_check_detail": cargo_check_detail,
        },
    }
    out_path = root / ".tmp" / "tauri_window_launch_attempt.json"
    _write_json(out_path, report)
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["summary"]["pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
