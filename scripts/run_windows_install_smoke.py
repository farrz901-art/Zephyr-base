from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path


DEFAULT_PACKAGE = Path(".tmp/windows_installer_package/ZephyrBase-windows-unsigned.zip")
DEFAULT_INSTALL_ROOT = Path(".tmp/windows_install_smoke/InstallRoot")


def _write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _run(command: list[str], cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(command, cwd=cwd, check=False, capture_output=True, text=True)


def _read_json(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run the S15 Windows install smoke from the packaged zip.")
    parser.add_argument("--package", type=Path, default=DEFAULT_PACKAGE)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)

    root = Path(__file__).resolve().parents[1]
    package_path = args.package if args.package.is_absolute() else (root / args.package).resolve()
    if not package_path.exists():
        raise FileNotFoundError(package_path)

    install_root = (root / DEFAULT_INSTALL_ROOT).resolve()
    if install_root.exists():
        shutil.rmtree(install_root)
    install_root.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(package_path) as archive:
        archive.extractall(install_root)

    unpacked_root = install_root / "ZephyrBase"
    proof_runner = unpacked_root / "checks/run_windows_package_install_proof.py"
    proof_validator = unpacked_root / "checks/validate_windows_package_install_proof.py"
    exe_path = unpacked_root / "app/zephyr-base-tauri-bridge.exe"

    run_completed = _run([sys.executable, str(proof_runner), "--json"], unpacked_root)
    validate_completed = _run([sys.executable, str(proof_validator), "--json"], unpacked_root)

    proof_path = unpacked_root / "proof/windows_install_proof.json"
    validation_path = unpacked_root / "proof/windows_install_proof_validation.json"
    proof = _read_json(proof_path) if proof_path.exists() else {}
    validation = _read_json(validation_path) if validation_path.exists() else {}
    text_flow = proof.get("text_flow", {}) if isinstance(proof.get("text_flow"), dict) else {}
    file_flow = proof.get("file_flow", {}) if isinstance(proof.get("file_flow"), dict) else {}
    offline_install = proof.get("offline_install", {}) if isinstance(proof.get("offline_install"), dict) else {}
    runtime = proof.get("runtime", {}) if isinstance(proof.get("runtime"), dict) else {}
    passed = bool(
        run_completed.returncode == 0
        and validate_completed.returncode == 0
        and isinstance(validation.get("summary"), dict)
        and validation["summary"].get("pass") is True
    )
    report = {
        "schema_version": 1,
        "report_id": "zephyr.base.s15.windows_install_smoke.v1",
        "summary": {
            "pass": passed,
            "package_path": str(package_path),
            "install_root": str(unpacked_root),
            "install_smoke_pass": passed,
        },
        "selected_python": runtime.get("managed_python"),
        "uses_wheelhouse": True,
        "uses_no_index": offline_install.get("uses_no_index"),
        "uses_find_links": offline_install.get("uses_find_links"),
        "tauri_executable_exists": exe_path.exists(),
        "text_flow": text_flow,
        "file_flow": file_flow,
        "runtime": runtime,
        "proof": proof,
        "validation": validation,
        "run": {
            "returncode": run_completed.returncode,
            "stdout": run_completed.stdout.strip(),
            "stderr": run_completed.stderr.strip(),
        },
        "validate": {
            "returncode": validate_completed.returncode,
            "stdout": validate_completed.stdout.strip(),
            "stderr": validate_completed.stderr.strip(),
        },
    }
    _write_json(root / ".tmp/windows_install_smoke_report.json", report)
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
