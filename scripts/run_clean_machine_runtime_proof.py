from __future__ import annotations

import argparse
import json
import os
import platform
import shutil
import subprocess
import sys
from pathlib import Path


TEXT_MARKER = "ZEPHYR_BASE_S13_CLEAN_MACHINE_TEXT_MARKER"
FILE_MARKER = "ZEPHYR_BASE_S13_CLEAN_MACHINE_FILE_MARKER"


def _write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _read_json(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def _run(command: list[str], cwd: Path, env: dict[str, str] | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(command, cwd=cwd, check=False, capture_output=True, text=True, env=env)


def _request_payload(*, request_id: str, output_dir: Path, inline_text: str | None = None, input_path: Path | None = None) -> dict[str, object]:
    payload: dict[str, object] = {
        "schema_version": 1,
        "request_id": request_id,
        "output_dir": str(output_dir),
        "requested_outputs": [
            "normalized_text",
            "content_evidence",
            "receipt",
            "filesystem_output",
        ],
    }
    if inline_text is not None:
        payload["input_kind"] = "local_text"
        payload["inline_text"] = inline_text
    if input_path is not None:
        payload["input_kind"] = "local_file"
        payload["input_path"] = str(input_path)
    return payload


def _run_flow(*, root: Path, managed_python: Path, request_payload: dict[str, object], request_path: Path, output_dir: Path, marker: str) -> tuple[subprocess.CompletedProcess[str], dict[str, object]]:
    request_path.write_text(json.dumps(request_payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    env = os.environ.copy()
    env["ZEPHYR_BASE_PYTHON"] = str(managed_python)
    completed = _run(
        [
            str(managed_python),
            str(root / "public-core-bridge/run_public_core_adapter.py"),
            "--request",
            str(request_path),
            "--out-dir",
            str(output_dir),
            "--bundle-root",
            str(root / "runtime/public-core-bundle"),
            "--json",
        ],
        root,
        env=env,
    )
    run_result_path = output_dir / "run_result.json"
    run_result = _read_json(run_result_path) if run_result_path.exists() else {}
    usage_fact = run_result.get("usage_fact", {}) if isinstance(run_result, dict) else {}
    if not isinstance(usage_fact, dict):
        usage_fact = {}
    return completed, {
        "pass": completed.returncode == 0
        and run_result_path.exists()
        and marker in str(run_result.get("normalized_text_preview", ""))
        and usage_fact.get("billing_semantics") is False
        and run_result.get("bundled_runtime_used") is True
        and run_result.get("fixture_runner_used") is False
        and run_result.get("zephyr_dev_working_tree_required") is False
        and run_result.get("requires_network") is False
        and run_result.get("requires_p45_substrate") is False,
        "run_result_exists": run_result_path.exists(),
        "marker_found": marker in str(run_result.get("normalized_text_preview", "")),
        "billing_semantics": usage_fact.get("billing_semantics"),
        "bundled_runtime_used": run_result.get("bundled_runtime_used"),
        "fixture_runner_used": run_result.get("fixture_runner_used"),
        "zephyr_dev_working_tree_required": run_result.get("zephyr_dev_working_tree_required"),
        "requires_network": run_result.get("requires_network"),
        "requires_p45_substrate": run_result.get("requires_p45_substrate"),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run the Zephyr Base clean-machine runtime proof.")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)

    root = Path(__file__).resolve().parents[1]
    bootstrap_script = root / "checks/bootstrap_base_runtime.py"
    if not bootstrap_script.exists():
        raise FileNotFoundError(f"Missing bootstrap script: {bootstrap_script}")

    bootstrap = _run([sys.executable, str(bootstrap_script), "--venv-root", ".runtime/base_runtime_venv", "--json"], root)
    bootstrap_report_path = root / ".tmp/base_runtime_bootstrap.json"
    bootstrap_report = _read_json(bootstrap_report_path) if bootstrap_report_path.exists() else {}
    managed_python_raw = bootstrap_report.get("runtime", {}).get("managed_python") if isinstance(bootstrap_report.get("runtime"), dict) else None
    managed_python = Path(str(managed_python_raw)) if managed_python_raw else None
    if managed_python is None or not managed_python.exists():
        raise FileNotFoundError("Managed runtime bootstrap did not produce a Python executable")

    proof_root = root / "proof"
    text_output_dir = proof_root / "clean_machine_text"
    file_output_dir = proof_root / "clean_machine_file"
    proof_input_dir = proof_root / "input"
    proof_input_dir.mkdir(parents=True, exist_ok=True)
    sample_file = proof_input_dir / "sample_clean_machine.txt"
    sample_file.write_text(f"Clean machine proof\n\n{FILE_MARKER}\n", encoding="utf-8")

    text_request_path = root / ".tmp/s13_clean_machine_text_request.json"
    file_request_path = root / ".tmp/s13_clean_machine_file_request.json"
    text_completed, text_flow = _run_flow(
        root=root,
        managed_python=managed_python,
        request_payload=_request_payload(
            request_id="s13-clean-machine-text",
            output_dir=text_output_dir,
            inline_text=TEXT_MARKER,
        ),
        request_path=text_request_path,
        output_dir=text_output_dir,
        marker=TEXT_MARKER,
    )
    file_completed, file_flow = _run_flow(
        root=root,
        managed_python=managed_python,
        request_payload=_request_payload(
            request_id="s13-clean-machine-file",
            output_dir=file_output_dir,
            input_path=sample_file,
        ),
        request_path=file_request_path,
        output_dir=file_output_dir,
        marker=FILE_MARKER,
    )

    report = {
        "schema_version": 1,
        "report_id": "zephyr.base.s13.clean_machine_runtime_proof.v1",
        "proof_level": "L1",
        "machine": {
            "os": platform.platform(),
            "python": sys.executable,
            "node_available": shutil.which("node") is not None,
            "cargo_available": shutil.which("cargo") is not None,
            "git_available": shutil.which("git") is not None,
        },
        "runtime": {
            "managed_python": str(managed_python),
            "managed_runtime_created": bootstrap.returncode == 0,
            "uses_current_shell_python_for_execution": False,
            "embedded_python_runtime": False,
            "wheelhouse_bundled": False,
            "installer_runtime_complete": False,
        },
        "text_flow": text_flow,
        "file_flow": file_flow,
        "scope": {
            "installer_built": False,
            "release_created": False,
            "clean_machine_runtime_proven": bool(text_flow["pass"] and file_flow["pass"]),
            "clean_machine_installer_proven": False,
        },
        "bootstrap": {
            "returncode": bootstrap.returncode,
            "stdout": bootstrap.stdout.strip(),
            "stderr": bootstrap.stderr.strip(),
        },
        "text_adapter": {
            "returncode": text_completed.returncode,
            "stdout": text_completed.stdout.strip(),
            "stderr": text_completed.stderr.strip(),
        },
        "file_adapter": {
            "returncode": file_completed.returncode,
            "stdout": file_completed.stdout.strip(),
            "stderr": file_completed.stderr.strip(),
        },
    }
    _write_json(proof_root / "clean_machine_runtime_proof.json", report)
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["scope"]["clean_machine_runtime_proven"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
