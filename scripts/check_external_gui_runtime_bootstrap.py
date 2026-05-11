from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import zipfile
from pathlib import Path


DEFAULT_PACKAGE = Path(".tmp/windows_installer_package/ZephyrBase-windows-unsigned.zip")
DEFAULT_EXTRACT_ROOT = Path(".tmp/external_gui_runtime_bootstrap")
TEXT_MARKER = "ZEPHYR_BASE_S17_GUI_BOOTSTRAP_TEXT_MARKER"
FILE_MARKER = "ZEPHYR_BASE_S17_GUI_BOOTSTRAP_FILE_MARKER"


def _write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _run(command: list[str], cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(command, cwd=cwd, check=False, capture_output=True, text=True)


def _read_json(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


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
    pointer_exists = pointer_path.exists()
    selected_python = str(prepare_json.get("selected_python_path", "")).strip()
    selected_python_path = Path(selected_python) if selected_python else None
    import_check = (
        _run(
            [str(selected_python_path), "-c", "import pydantic, unstructured"],
            package_root,
        )
        if selected_python_path is not None and selected_python_path.exists()
        else None
    )

    text_output = package_root / ".tmp/s17_gui_bootstrap_text"
    file_output = package_root / ".tmp/s17_gui_bootstrap_file"
    sample_file = package_root / ".tmp/s17_gui_bootstrap_input.txt"
    sample_file.parent.mkdir(parents=True, exist_ok=True)
    sample_file.write_text(f"External GUI bootstrap file smoke\n\n{FILE_MARKER}\n", encoding="utf-8")

    text_run = _run([str(app_exe), "run-local-text", TEXT_MARKER, text_output.as_posix()], package_root)
    file_run = _run([str(app_exe), "run-local-file", sample_file.as_posix(), file_output.as_posix()], package_root)

    text_result = _read_json(text_output / "run_result.json") if (text_output / "run_result.json").exists() else {}
    file_result = _read_json(file_output / "run_result.json") if (file_output / "run_result.json").exists() else {}
    text_usage = text_result.get("usage_fact", {}) if isinstance(text_result.get("usage_fact"), dict) else {}
    file_usage = file_result.get("usage_fact", {}) if isinstance(file_result.get("usage_fact"), dict) else {}

    report = {
        "schema_version": 1,
        "report_id": "zephyr.base.s17.external_gui_runtime_bootstrap_check.v1",
        "summary": {
            "pass": (
                prepare.returncode == 0
                and prepare_json.get("managed_runtime_available") is True
                and prepare_json.get("managed_python_runtime_used") is True
                and prepare_json.get("uses_current_python_environment") is False
                and prepare_json.get("uses_no_index") is True
                and prepare_json.get("uses_find_links") is True
                and prepare_json.get("requires_network_for_dependency_install") is False
                and pointer_exists
                and import_check is not None
                and import_check.returncode == 0
                and text_run.returncode == 0
                and file_run.returncode == 0
                and TEXT_MARKER in str(text_result.get("normalized_text_preview", ""))
                and FILE_MARKER in str(file_result.get("normalized_text_preview", ""))
                and text_usage.get("billing_semantics") is False
                and file_usage.get("billing_semantics") is False
                and text_result.get("bundled_runtime_used") is True
                and file_result.get("bundled_runtime_used") is True
                and text_result.get("fixture_runner_used") is False
                and file_result.get("fixture_runner_used") is False
                and text_result.get("zephyr_dev_working_tree_required") is False
                and file_result.get("zephyr_dev_working_tree_required") is False
                and text_result.get("requires_network") is False
                and file_result.get("requires_network") is False
                and text_result.get("requires_p45_substrate") is False
                and file_result.get("requires_p45_substrate") is False
            ),
            "managed_runtime_created": prepare_json.get("managed_runtime_created") is True,
            "pointer_exists": pointer_exists,
            "text_flow_pass": TEXT_MARKER in str(text_result.get("normalized_text_preview", "")),
            "file_flow_pass": FILE_MARKER in str(file_result.get("normalized_text_preview", "")),
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
