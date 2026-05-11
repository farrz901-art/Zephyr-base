from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path


DEST_ROOT = Path(".tmp/imported_external_package_ux_proof")


def _write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _read_json(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def _load_validation_report(*, imported_root: Path, repo_root: Path, validator_stdout: str) -> dict[str, object]:
    preferred = imported_root / "external_package_ux_proof_validation.json"
    if preferred.exists():
        return _read_json(preferred)
    fallback = repo_root / ".tmp/external_package_ux_proof_validation.json"
    if fallback.exists():
        return _read_json(fallback)
    stdout = validator_stdout.strip()
    if stdout:
        loaded = json.loads(stdout)
        if isinstance(loaded, dict):
            return loaded
    return {}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Import an external package UX proof into the repo .tmp area.")
    parser.add_argument("--proof", type=Path, required=True)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)

    root = Path(__file__).resolve().parents[1]
    source_proof = args.proof.resolve()
    if not source_proof.exists():
        raise FileNotFoundError(source_proof)
    dest_root = (root / DEST_ROOT).resolve()
    if dest_root.exists():
        shutil.rmtree(dest_root)
    dest_root.mkdir(parents=True, exist_ok=True)
    dest_proof = dest_root / "external_package_ux_proof.json"
    shutil.copy2(source_proof, dest_proof)

    completed = subprocess.run(
        [
            sys.executable,
            str(root / "scripts/validate_external_package_ux_proof.py"),
            "--proof",
            str(dest_proof),
            "--json",
        ],
        cwd=root,
        check=False,
        capture_output=True,
        text=True,
    )
    validation = _load_validation_report(
        imported_root=dest_root,
        repo_root=root,
        validator_stdout=completed.stdout,
    )
    summary = validation.get("summary", {}) if isinstance(validation.get("summary"), dict) else {}
    validation_pass = summary.get("pass") is True
    report = {
        "schema_version": 1,
        "report_id": "zephyr.base.s17.import_external_package_ux_proof.v1",
        "summary": {
            "pass": completed.returncode == 0 and validation_pass,
            "manual_gui_proof_imported": True,
            "manual_gui_proof_pass": validation_pass,
        },
        "imported_proof_path": str(dest_proof),
        "validator": {
            "returncode": completed.returncode,
            "stdout": completed.stdout.strip(),
            "stderr": completed.stderr.strip(),
        },
        "validation_report": validation,
    }
    _write_json(root / ".tmp/imported_external_package_ux_proof_report.json", report)
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["summary"]["pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
