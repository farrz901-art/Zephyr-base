from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path

from marker_detection import build_long_marker_text, detect_marker_in_output


DEFAULT_PACKAGE = Path(".tmp/windows_installer_package/ZephyrBase-windows-unsigned.zip")
DEFAULT_EXTRACT_ROOT = Path(".tmp/external_package_runtime_smoke")
TEXT_MARKER = "ZEPHYR_BASE_S17_EXTERNAL_PACKAGE_TEXT_MARKER"
FILE_MARKER = "ZEPHYR_BASE_S17_EXTERNAL_PACKAGE_FILE_MARKER"


def _write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _read_json(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def _run(command: list[str], cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(command, cwd=cwd, check=False, capture_output=True, text=True)


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
    package_root: Path,
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
            str(package_root / "public-core-bridge/run_public_core_adapter.py"),
            "--request",
            str(request_path),
            "--out-dir",
            str(output_dir),
            "--bundle-root",
            str(package_root / "runtime/public-core-bundle"),
            "--json",
        ],
        package_root,
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
    parser = argparse.ArgumentParser(description="Run the S17 external package runtime smoke from an extracted portable package.")
    parser.add_argument("--package", type=Path, default=DEFAULT_PACKAGE)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)

    root = Path(__file__).resolve().parents[1]
    package_path = args.package if args.package.is_absolute() else (root / args.package).resolve()
    if not package_path.exists():
        raise FileNotFoundError(package_path)

    extract_root = (root / DEFAULT_EXTRACT_ROOT).resolve()
    if extract_root.exists():
        shutil.rmtree(extract_root)
    extract_root.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(package_path) as archive:
        archive.extractall(extract_root)

    package_root = extract_root / "ZephyrBase"
    runtime_root = package_root / ".runtime/base_runtime_venv"
    wheelhouse_root = package_root / "runtime/wheelhouse"
    requirements_path = package_root / "runtime/python-runtime/base-runtime-requirements.txt"
    proof_root = package_root / "proof"

    create_completed = _run([sys.executable, "-m", "venv", str(runtime_root)], package_root)
    managed_python = _venv_python(runtime_root)
    ensure_pip = _ensure_pip(managed_python, package_root) if create_completed.returncode == 0 else None
    install_completed = (
        _run(
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
            package_root,
        )
        if create_completed.returncode == 0 and ensure_pip is not None and ensure_pip.returncode == 0
        else None
    )

    input_dir = proof_root / "input"
    input_dir.mkdir(parents=True, exist_ok=True)
    sample_file = input_dir / "external_package_sample.txt"
    sample_file.write_text(build_long_marker_text(FILE_MARKER, "External package file smoke"), encoding="utf-8")

    base_flow = {
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
    text_flow = dict(base_flow)
    file_flow = dict(base_flow)
    text_completed = None
    file_completed = None
    if install_completed is not None and install_completed.returncode == 0:
        text_completed, text_flow = _run_flow(
            package_root=package_root,
            managed_python=managed_python,
            request_payload=_request_payload(
                request_id="s17-external-package-text",
                output_dir=proof_root / "external_package_text",
                inline_text=build_long_marker_text(TEXT_MARKER, "External package text smoke"),
            ),
            request_path=package_root / ".tmp/s17_external_package_text_request.json",
            output_dir=proof_root / "external_package_text",
            marker=TEXT_MARKER,
        )
        file_completed, file_flow = _run_flow(
            package_root=package_root,
            managed_python=managed_python,
            request_payload=_request_payload(
                request_id="s17-external-package-file",
                output_dir=proof_root / "external_package_file",
                input_path=sample_file,
            ),
            request_path=package_root / ".tmp/s17_external_package_file_request.json",
            output_dir=proof_root / "external_package_file",
            marker=FILE_MARKER,
        )

    passed = bool(text_flow["pass"] and file_flow["pass"])
    report = {
        "schema_version": 1,
        "report_id": "zephyr.base.s17.external_package_runtime_smoke.v1",
        "summary": {
            "pass": passed,
            "external_runtime_smoke_pass": passed,
            "package_path": str(package_path),
            "extract_root": str(package_root),
        },
        "selected_python": str(managed_python),
        "uses_wheelhouse": True,
        "uses_no_index": True,
        "uses_find_links": True,
        "text_flow": text_flow,
        "file_flow": file_flow,
        "runtime": {
            "managed_runtime_created": create_completed.returncode == 0,
            "uses_current_shell_python_for_execution": False,
            "requires_network_for_dependency_install": False,
            "requires_network_at_runtime": False,
        },
        "create_venv": {
            "returncode": create_completed.returncode,
            "stdout": create_completed.stdout.strip(),
            "stderr": create_completed.stderr.strip(),
        },
        "ensure_pip": {
            "returncode": ensure_pip.returncode if ensure_pip is not None else None,
            "stdout": ensure_pip.stdout.strip() if ensure_pip is not None else "",
            "stderr": ensure_pip.stderr.strip() if ensure_pip is not None else "",
        },
        "install": {
            "returncode": install_completed.returncode if install_completed is not None else None,
            "stdout": install_completed.stdout.strip() if install_completed is not None else "",
            "stderr": install_completed.stderr.strip() if install_completed is not None else "",
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
    _write_json(root / ".tmp/external_package_runtime_smoke_report.json", report)
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
