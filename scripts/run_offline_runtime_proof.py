from __future__ import annotations

import argparse
import json
import os
import platform
import shutil
import subprocess
import sys
from pathlib import Path

from marker_detection import build_long_marker_text, detect_marker_in_output


TEXT_MARKER = "ZEPHYR_BASE_S14_OFFLINE_WHEELHOUSE_TEXT_MARKER"
FILE_MARKER = "ZEPHYR_BASE_S14_OFFLINE_WHEELHOUSE_FILE_MARKER"


def _write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _read_json(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def _run(command: list[str], cwd: Path, env: dict[str, str] | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(command, cwd=cwd, check=False, capture_output=True, text=True, env=env)


def _venv_python(venv_root: Path) -> Path:
    if os.name == "nt":
        return venv_root / "Scripts" / "python.exe"
    return venv_root / "bin" / "python"


def _ensure_pip(python_exe: Path, cwd: Path) -> subprocess.CompletedProcess[str]:
    pip_version = _run([str(python_exe), "-m", "pip", "--version"], cwd)
    if pip_version.returncode == 0:
        return pip_version
    return _run([str(python_exe), "-m", "ensurepip", "--upgrade"], cwd)


def _request_payload(
    *,
    request_id: str,
    output_dir: Path,
    inline_text: str | None = None,
    input_path: Path | None = None,
) -> dict[str, object]:
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


def _run_flow(
    *,
    root: Path,
    managed_python: Path,
    request_payload: dict[str, object],
    request_path: Path,
    output_dir: Path,
    marker: str,
) -> tuple[subprocess.CompletedProcess[str], dict[str, object]]:
    request_path.parent.mkdir(parents=True, exist_ok=True)
    output_dir.mkdir(parents=True, exist_ok=True)
    request_path.write_text(json.dumps(request_payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
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
    )
    run_result_path = output_dir / "run_result.json"
    run_result = _read_json(run_result_path) if run_result_path.exists() else {}
    usage_fact = run_result.get("usage_fact", {}) if isinstance(run_result, dict) else {}
    if not isinstance(usage_fact, dict):
        usage_fact = {}
    marker_report = detect_marker_in_output(
        output_dir=output_dir,
        run_result=run_result,
        marker=marker,
    )
    return completed, {
        "pass": completed.returncode == 0
        and run_result_path.exists()
        and marker_report["marker_found"] is True
        and usage_fact.get("billing_semantics") is False
        and run_result.get("bundled_runtime_used") is True
        and run_result.get("fixture_runner_used") is False
        and run_result.get("zephyr_dev_working_tree_required") is False
        and run_result.get("requires_network") is False
        and run_result.get("requires_p45_substrate") is False,
        "run_result_exists": run_result_path.exists(),
        **marker_report,
        "billing_semantics": usage_fact.get("billing_semantics"),
        "bundled_runtime_used": run_result.get("bundled_runtime_used"),
        "fixture_runner_used": run_result.get("fixture_runner_used"),
        "zephyr_dev_working_tree_required": run_result.get("zephyr_dev_working_tree_required"),
        "requires_network": run_result.get("requires_network"),
        "requires_p45_substrate": run_result.get("requires_p45_substrate"),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run the offline runtime proof from an unpacked proof pack.")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)

    root = Path(__file__).resolve().parents[1]
    wheelhouse_root = root / "runtime/wheelhouse"
    requirements_path = root / "runtime/python-runtime/base-runtime-requirements.txt"
    venv_root = root / ".runtime/base_runtime_venv"
    if venv_root.exists():
        shutil.rmtree(venv_root)

    create_completed = _run([sys.executable, "-m", "venv", str(venv_root)], root)
    managed_python = _venv_python(venv_root)
    ensure_pip = _ensure_pip(managed_python, root) if create_completed.returncode == 0 else None
    install_completed = _run(
        [
            str(managed_python),
            "-m",
            "pip",
            "install",
            "--no-index",
            "--find-links",
            str(wheelhouse_root),
            "-r",
            str(requirements_path),
        ],
        root,
    ) if create_completed.returncode == 0 and ensure_pip is not None and ensure_pip.returncode == 0 else None

    proof_root = root / "proof"
    text_output_dir = proof_root / "offline_runtime_text"
    file_output_dir = proof_root / "offline_runtime_file"
    proof_input_dir = proof_root / "input"
    proof_input_dir.mkdir(parents=True, exist_ok=True)
    sample_file = proof_input_dir / "sample_offline_runtime.txt"
    sample_file.write_text(build_long_marker_text(FILE_MARKER, "Offline runtime file proof"), encoding="utf-8")

    text_flow = {
        "pass": False,
        "run_result_exists": False,
        "preview_marker_found": False,
        "full_text_marker_found": False,
        "marker_found": False,
        "processing_success": False,
        "marker_detection_failed": False,
        "normalized_text_exists": False,
        "billing_semantics": None,
        "bundled_runtime_used": None,
        "fixture_runner_used": None,
        "zephyr_dev_working_tree_required": None,
        "requires_network": None,
        "requires_p45_substrate": None,
    }
    file_flow = dict(text_flow)
    text_completed = None
    file_completed = None
    if install_completed is not None and install_completed.returncode == 0:
        text_completed, text_flow = _run_flow(
            root=root,
            managed_python=managed_python,
            request_payload=_request_payload(
                request_id="s14-offline-pack-text",
                output_dir=text_output_dir,
                inline_text=build_long_marker_text(TEXT_MARKER, "Offline runtime text proof"),
            ),
            request_path=root / ".tmp/s14_offline_pack_text_request.json",
            output_dir=text_output_dir,
            marker=TEXT_MARKER,
        )
        file_completed, file_flow = _run_flow(
            root=root,
            managed_python=managed_python,
            request_payload=_request_payload(
                request_id="s14-offline-pack-file",
                output_dir=file_output_dir,
                input_path=sample_file,
            ),
            request_path=root / ".tmp/s14_offline_pack_file_request.json",
            output_dir=file_output_dir,
            marker=FILE_MARKER,
        )

    proven = bool(text_flow["pass"] and file_flow["pass"])
    report = {
        "schema_version": 1,
        "report_id": "zephyr.base.s14.offline_runtime_proof.v1",
        "proof_level": "local_offline_pack",
        "machine": {
            "os": platform.platform(),
            "python": sys.executable,
            "node_available": shutil.which("node") is not None,
            "cargo_available": shutil.which("cargo") is not None,
            "git_available": shutil.which("git") is not None,
        },
        "runtime": {
            "managed_python": str(managed_python),
            "managed_runtime_created": create_completed.returncode == 0,
            "uses_current_shell_python_for_execution": False,
            "embedded_python_runtime": False,
            "wheelhouse_bundled": True,
            "installer_runtime_complete": False,
        },
        "offline_install": {
            "uses_no_index": True,
            "uses_find_links": True,
            "requires_network_for_dependency_install": False,
            "requires_network_at_runtime": False,
        },
        "text_flow": text_flow,
        "file_flow": file_flow,
        "scope": {
            "installer_built": False,
            "release_created": False,
            "signed_installer": False,
            "embedded_python_runtime": False,
            "wheelhouse_bundled": True,
            "offline_runtime_install_proven": proven,
            "external_clean_machine_offline_proven": False,
        },
        "create_venv": {
            "returncode": create_completed.returncode,
            "stdout": create_completed.stdout.strip(),
            "stderr": create_completed.stderr.strip(),
        },
        "install": {
            "returncode": install_completed.returncode if install_completed is not None else None,
            "stdout": install_completed.stdout.strip() if install_completed is not None else "",
            "stderr": install_completed.stderr.strip() if install_completed is not None else "",
        },
        "ensure_pip": {
            "returncode": ensure_pip.returncode if ensure_pip is not None else None,
            "stdout": ensure_pip.stdout.strip() if ensure_pip is not None else "",
            "stderr": ensure_pip.stderr.strip() if ensure_pip is not None else "",
        },
        "text_adapter": {
            "returncode": text_completed.returncode if text_completed is not None else None,
            "stdout": text_completed.stdout.strip() if text_completed is not None else "",
            "stderr": text_completed.stderr.strip() if text_completed is not None else "",
        },
        "file_adapter": {
            "returncode": file_completed.returncode if file_completed is not None else None,
            "stdout": file_completed.stdout.strip() if file_completed is not None else "",
            "stderr": file_completed.stderr.strip() if file_completed is not None else "",
        },
    }
    _write_json(proof_root / "offline_runtime_proof.json", report)
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if proven else 1


if __name__ == "__main__":
    raise SystemExit(main())
