from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import zipfile
from pathlib import Path

from marker_detection import detect_marker_in_output


DEFAULT_PACKAGE = Path(".tmp/windows_installer_package/ZephyrBase-windows-unsigned.zip")
DEFAULT_EXTRACT_ROOT = Path(".tmp/egui_short")
TEXT_MARKER = "ZEPHYR_BASE_S17_GUI_BOOTSTRAP_TEXT_MARKER"
FILE_MARKER = "ZEPHYR_BASE_S17_GUI_BOOTSTRAP_FILE_MARKER"


def _build_bootstrap_long_text(marker: str, label: str) -> str:
    lines = [f"{label} line {index:02d}." for index in range(1, 55)]
    lines.extend(["", "Marker:", marker, f"{label} complete."])
    return "\n".join(lines) + "\n"


def _write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _run(command: list[str], cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(command, cwd=cwd, check=False, capture_output=True, text=True)


def _read_json(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def _read_completed_json(completed: subprocess.CompletedProcess[str]) -> dict[str, object]:
    payload = completed.stdout.strip()
    if not payload:
        return {}
    loaded = json.loads(payload)
    return loaded if isinstance(loaded, dict) else {}


def _flow_report(output_dir: Path, run_result: dict[str, object], marker: str) -> dict[str, object]:
    usage_fact = run_result.get("usage_fact", {}) if isinstance(run_result.get("usage_fact"), dict) else {}
    marker_report = detect_marker_in_output(output_dir=output_dir, run_result=run_result, marker=marker)
    return {
        "pass": (
            marker_report["marker_found"] is True
            and usage_fact.get("billing_semantics") is False
            and run_result.get("bundled_runtime_used") is True
            and run_result.get("fixture_runner_used") is False
            and run_result.get("zephyr_dev_working_tree_required") is False
            and run_result.get("requires_network") is False
            and run_result.get("requires_p45_substrate") is False
        ),
        **marker_report,
        "billing_semantics": usage_fact.get("billing_semantics"),
        "bundled_runtime_used": run_result.get("bundled_runtime_used"),
        "fixture_runner_used": run_result.get("fixture_runner_used"),
        "zephyr_dev_working_tree_required": run_result.get("zephyr_dev_working_tree_required"),
        "requires_network": run_result.get("requires_network"),
        "requires_p45_substrate": run_result.get("requires_p45_substrate"),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Check external package GUI runtime bootstrap through the packaged Tauri bridge.")
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
    app_exe = package_root / "app/zephyr-base-tauri-bridge.exe"
    if not app_exe.exists():
        raise FileNotFoundError(app_exe)

    for rel in (
        ".tmp/base_runtime_python_path.txt",
        ".tmp/base_runtime_venv",
        ".tmp/base_runtime_venv_managed",
    ):
        target = package_root / rel
        if target.is_dir():
            shutil.rmtree(target)
        elif target.exists():
            target.unlink()

    prepare = _run([str(app_exe), "prepare-local-runtime"], package_root)
    prepare_json = json.loads(prepare.stdout) if prepare.stdout.strip() else {}
    pointer_path = package_root / ".tmp/base_runtime_python_path.txt"

    text_output = package_root / ".tmp/s17_short_text"
    file_output = package_root / ".tmp/s17_short_file"
    sample_file = package_root / ".tmp/sample.txt"
    sample_file.parent.mkdir(parents=True, exist_ok=True)
    sample_file.write_text(_build_bootstrap_long_text(FILE_MARKER, "Short path GUI file smoke"), encoding="utf-8")
    text_input = _build_bootstrap_long_text(TEXT_MARKER, "Short path GUI smoke")

    text_run = _run([str(app_exe), "run-local-text", text_input, text_output.as_posix()], package_root)
    file_run = _run([str(app_exe), "run-local-file", sample_file.as_posix(), file_output.as_posix()], package_root)

    text_file_result = _read_json(text_output / "run_result.json") if (text_output / "run_result.json").exists() else {}
    file_file_result = _read_json(file_output / "run_result.json") if (file_output / "run_result.json").exists() else {}
    text_result = _read_completed_json(text_run) or text_file_result
    file_result = _read_completed_json(file_run) or file_file_result
    text_flow = _flow_report(text_output, text_result, TEXT_MARKER)
    file_flow = _flow_report(file_output, file_result, FILE_MARKER)

    pointer_exists = pointer_path.exists()
    selected_python = str(
        prepare_json.get("selected_python_path")
        or text_result.get("selected_python_path")
        or file_result.get("selected_python_path")
        or ""
    ).strip()
    selected_python_path = Path(selected_python) if selected_python else None
    import_check = (
        _run([str(selected_python_path), "-c", "import pydantic, unstructured"], package_root)
        if selected_python_path is not None and selected_python_path.exists()
        else None
    )

    report = {
        "schema_version": 1,
        "report_id": "zephyr.base.s17.external_gui_runtime_bootstrap_check.v1",
        "summary": {
            "pass": (
                pointer_exists
                and import_check is not None
                and import_check.returncode == 0
                and text_run.returncode == 0
                and file_run.returncode == 0
                and text_flow["pass"] is True
                and file_flow["pass"] is True
                and text_result.get("managed_python_runtime_used") is True
                and file_result.get("managed_python_runtime_used") is True
                and text_result.get("uses_current_python_environment") is False
                and file_result.get("uses_current_python_environment") is False
            ),
            "managed_runtime_created": bool(
                prepare_json.get("managed_runtime_created") is True
                or text_result.get("managed_runtime_available") is True
                or file_result.get("managed_runtime_available") is True
            ),
            "pointer_exists": pointer_exists,
            "text_flow_pass": text_flow["pass"] is True,
            "file_flow_pass": file_flow["pass"] is True,
        },
        "prepare": {
            "returncode": prepare.returncode,
            "stdout": prepare.stdout.strip(),
            "stderr": prepare.stderr.strip(),
            "json": prepare_json,
        },
        "selected_python": selected_python,
        "text_run": {
            "returncode": text_run.returncode,
            "stdout": text_run.stdout.strip(),
            "stderr": text_run.stderr.strip(),
        },
        "file_run": {
            "returncode": file_run.returncode,
            "stdout": file_run.stdout.strip(),
            "stderr": file_run.stderr.strip(),
        },
        "text_flow": text_flow,
        "file_flow": file_flow,
        "text_result": text_result,
        "file_result": file_result,
        "import_check": {
            "returncode": import_check.returncode if import_check is not None else None,
            "stdout": import_check.stdout.strip() if import_check is not None else "",
            "stderr": import_check.stderr.strip() if import_check is not None else "",
        },
    }
    _write_json(root / ".tmp/external_gui_runtime_bootstrap_check.json", report)
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["summary"]["pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
