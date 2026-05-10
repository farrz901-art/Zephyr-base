from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path


DEST_ROOT = Path(".tmp/imported_offline_runtime_proof")


def _write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _read_json(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def _resolve_proof_root(candidate: Path) -> Path:
    resolved = candidate.resolve()
    if (resolved / "offline_runtime_proof.json").exists():
        return resolved
    if (resolved / "proof/offline_runtime_proof.json").exists():
        return resolved / "proof"
    raise FileNotFoundError(f"Could not locate offline runtime proof under {candidate}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Import an external offline runtime proof into the repo .tmp area.")
    parser.add_argument("--proof-root", type=Path, required=True)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)

    root = Path(__file__).resolve().parents[1]
    source_proof_root = _resolve_proof_root(args.proof_root)
    dest_root = (root / DEST_ROOT).resolve()
    if dest_root.exists():
        shutil.rmtree(dest_root)
    (dest_root / "proof").mkdir(parents=True, exist_ok=True)
    shutil.copytree(source_proof_root, dest_root / "proof", dirs_exist_ok=True)

    completed = subprocess.run(
        [sys.executable, str(root / "scripts/validate_offline_runtime_proof.py"), "--proof-root", str(dest_root / "proof"), "--json"],
        cwd=root,
        check=False,
        capture_output=True,
        text=True,
    )
    validation_path = root / ".tmp/offline_runtime_proof_validation.json"
    validation = _read_json(validation_path) if validation_path.exists() else {}
    report = {
        "schema_version": 1,
        "report_id": "zephyr.base.s14.import_offline_runtime_proof.v1",
        "summary": {
            "pass": completed.returncode == 0 and validation.get("summary", {}).get("pass") is True,
            "external_offline_proof_imported": True,
            "external_offline_proof_pass": validation.get("summary", {}).get("pass") is True,
        },
        "imported_proof_root": str(dest_root / "proof"),
        "validator": {
            "returncode": completed.returncode,
            "stdout": completed.stdout.strip(),
            "stderr": completed.stderr.strip(),
        },
        "validation_report": validation,
    }
    _write_json(root / ".tmp/imported_offline_runtime_proof_report.json", report)
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["summary"]["pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
