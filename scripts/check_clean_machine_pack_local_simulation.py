from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path


ZIP_PATH = Path(".tmp/clean_machine_proof_pack/ZephyrBase-clean-machine-proof.zip")


def _write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _read_json(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def _run(command: list[str], cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(command, cwd=cwd, check=False, capture_output=True, text=True)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run a local unzip simulation for the clean-machine proof pack.")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)

    root = Path(__file__).resolve().parents[1]
    zip_path = (root / ZIP_PATH).resolve()
    if not zip_path.exists():
        raise FileNotFoundError(f"Missing clean-machine proof zip: {zip_path}")

    simulation_root = Path(tempfile.gettempdir()).resolve() / "zephyr_base_clean_machine_pack_local_simulation"
    if simulation_root.exists():
        shutil.rmtree(simulation_root)
    simulation_root.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(zip_path) as archive:
        archive.extractall(simulation_root)

    unpacked_root = simulation_root / "ZephyrBase"
    run_completed = _run([sys.executable, "checks/run_clean_machine_runtime_proof.py", "--json"], unpacked_root)
    validate_completed = _run([sys.executable, "checks/validate_clean_machine_runtime_proof.py", "--json"], unpacked_root)
    validation_path = unpacked_root / "proof/clean_machine_runtime_proof_validation.json"
    validation = _read_json(validation_path) if validation_path.exists() else {}

    report = {
        "schema_version": 1,
        "report_id": "zephyr.base.s13.clean_machine_pack_local_simulation_check.v1",
        "summary": {
            "pass": run_completed.returncode == 0 and validate_completed.returncode == 0 and validation.get("summary", {}).get("pass") is True,
            "local_simulation_pass": run_completed.returncode == 0 and validate_completed.returncode == 0 and validation.get("summary", {}).get("pass") is True,
            "clean_machine_runtime_proven": False,
            "external_clean_machine_proof_required": True,
        },
        "simulation_root": str(unpacked_root),
        "runner": {
            "returncode": run_completed.returncode,
            "stdout": run_completed.stdout.strip(),
            "stderr": run_completed.stderr.strip(),
        },
        "validator": {
            "returncode": validate_completed.returncode,
            "stdout": validate_completed.stdout.strip(),
            "stderr": validate_completed.stderr.strip(),
        },
        "validation_report": validation,
    }
    _write_json(root / ".tmp/clean_machine_pack_local_simulation_check.json", report)
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["summary"]["pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
