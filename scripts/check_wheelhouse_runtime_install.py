from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

from marker_detection import build_long_marker_text, detect_marker_in_output


TEXT_MARKER = "ZEPHYR_BASE_S14_OFFLINE_WHEELHOUSE_TEXT_MARKER"
FILE_MARKER = "ZEPHYR_BASE_S14_OFFLINE_WHEELHOUSE_FILE_MARKER"
TEXT_OUTPUT_DIR = Path(".tmp/s14_offline_wheelhouse_text")
FILE_OUTPUT_DIR = Path(".tmp/s14_offline_wheelhouse_file")


def _write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _run(command: list[str], cwd: Path, env: dict[str, str] | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(command, cwd=cwd, check=False, capture_output=True, text=True, env=env)


def _load_json(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def _venv_python(venv_root: Path) -> Path:
    if os.name == "nt":
        return venv_root / "Scripts" / "python.exe"
    return venv_root / "bin" / "python"


def _importable(python_exe: Path, module_name: str, cwd: Path) -> bool:
    completed = _run([str(python_exe), "-c", f"import {module_name}"], cwd)
    return completed.returncode == 0


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
    run_result = _load_json(run_result_path) if run_result_path.exists() else {}
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
    parser = argparse.ArgumentParser(description="Validate the offline wheelhouse runtime install first slice.")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)

    root = Path(__file__).resolve().parents[1]
    wheelhouse_root = root / ".tmp/base_runtime_wheelhouse"
    requirements_path = root / "runtime/python-runtime/base-runtime-requirements.txt"
    venv_root = root / ".tmp/base_runtime_venv_from_wheelhouse"
    if venv_root.exists():
        shutil.rmtree(venv_root)

    create_completed = _run([sys.executable, "-m", "venv", str(venv_root)], root)
    wheel_python = _venv_python(venv_root)
    ensure_pip = _ensure_pip(wheel_python, root) if create_completed.returncode == 0 else None
    uses_no_index = True
    uses_find_links = True
    install_completed = _run(
        [
            str(wheel_python),
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
    ) if create_completed.returncode == 0 and ensure_pip is not None and ensure_pip.returncode == 0 and wheelhouse_root.exists() else None

    pydantic_importable = wheel_python.exists() and _importable(wheel_python, "pydantic", root)
    unstructured_importable = wheel_python.exists() and _importable(wheel_python, "unstructured", root)

    text_output_dir = root / TEXT_OUTPUT_DIR
    file_output_dir = root / FILE_OUTPUT_DIR
    for output_dir in (text_output_dir, file_output_dir):
        if output_dir.exists():
            shutil.rmtree(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

    sample_input = root / ".tmp/s14_offline_wheelhouse_sample.txt"
    sample_input.write_text(build_long_marker_text(FILE_MARKER, "Offline wheelhouse file proof"), encoding="utf-8")

    text_completed = None
    file_completed = None
    text_flow: dict[str, object] = {
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

    if install_completed is not None and install_completed.returncode == 0 and pydantic_importable and unstructured_importable:
        text_completed, text_flow = _run_flow(
            root=root,
            managed_python=wheel_python,
            request_payload=_request_payload(
                request_id="s14-offline-wheelhouse-text",
                output_dir=text_output_dir,
                inline_text=build_long_marker_text(TEXT_MARKER, "Offline wheelhouse text proof"),
            ),
            request_path=root / ".tmp/s14_offline_wheelhouse_text_request.json",
            output_dir=text_output_dir,
            marker=TEXT_MARKER,
        )
        file_completed, file_flow = _run_flow(
            root=root,
            managed_python=wheel_python,
            request_payload=_request_payload(
                request_id="s14-offline-wheelhouse-file",
                output_dir=file_output_dir,
                input_path=sample_input,
            ),
            request_path=root / ".tmp/s14_offline_wheelhouse_file_request.json",
            output_dir=file_output_dir,
            marker=FILE_MARKER,
        )

    passed = all(
        (
            create_completed.returncode == 0,
            install_completed is not None and install_completed.returncode == 0,
            pydantic_importable,
            unstructured_importable,
            text_flow["pass"],
            file_flow["pass"],
        )
    )
    report = {
        "schema_version": 1,
        "report_id": "zephyr.base.s14.wheelhouse_runtime_install_check.v1",
        "summary": {
            "pass": passed,
            "offline_install_pass": passed,
            "uses_no_index": uses_no_index,
            "uses_find_links": uses_find_links,
            "requires_network_for_dependency_install": False,
            "requires_network_at_runtime": False,
            "selected_python_is_wheelhouse_venv": True,
        },
        "wheelhouse_root": str(wheelhouse_root),
        "venv_root": str(venv_root),
        "selected_python": str(wheel_python),
        "selected_python_is_wheelhouse_venv": True,
        "pydantic_importable": pydantic_importable,
        "unstructured_importable": unstructured_importable,
        "text_flow": text_flow,
        "file_flow": file_flow,
        "commands": {
            "create_venv": [sys.executable, "-m", "venv", str(venv_root)],
            "install": [
                str(wheel_python),
                "-m",
                "pip",
                "install",
                "--no-index",
                "--find-links",
                str(wheelhouse_root),
                "-r",
                str(requirements_path),
            ],
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
    out_path = root / ".tmp" / "wheelhouse_runtime_install_check.json"
    _write_json(out_path, report)
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
