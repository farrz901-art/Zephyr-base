from __future__ import annotations

import argparse
import json
from pathlib import Path


REQUIRED_FILES = [
    Path("docs/CLEAN_MACHINE_RUNTIME_PROOF.md"),
    Path("docs/MANUAL_CLEAN_MACHINE_RUNTIME_PROOF.md"),
    Path("scripts/build_clean_machine_proof_pack.py"),
    Path("scripts/run_clean_machine_runtime_proof.py"),
    Path("scripts/validate_clean_machine_runtime_proof.py"),
    Path("scripts/audit_clean_machine_pack_relocation.py"),
    Path("scripts/check_clean_machine_pack_local_simulation.py"),
    Path("scripts/import_clean_machine_proof.py"),
]


def _write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Check the clean-machine proof pack baseline.")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)

    root = Path(__file__).resolve().parents[1]
    missing = [path.as_posix() for path in REQUIRED_FILES if not (root / path).exists()]
    pack_manifest_path = root / ".tmp/clean_machine_proof_pack/clean_machine_proof_pack_manifest.json"
    pack_manifest = json.loads(pack_manifest_path.read_text(encoding="utf-8")) if pack_manifest_path.exists() else {}
    report = {
        "schema_version": 1,
        "report_id": "zephyr.base.s13.clean_machine_proof_pack_baseline.v1",
        "summary": {
            "pass": not missing
            and (not pack_manifest or (
                pack_manifest.get("installer_built") is False
                and pack_manifest.get("release_created") is False
                and pack_manifest.get("embedded_python_runtime") is False
                and pack_manifest.get("wheelhouse_bundled") is False
                and pack_manifest.get("clean_machine_runtime_proven") is False
            )),
            "pack_manifest_exists": pack_manifest_path.exists(),
        },
        "missing_files": missing,
        "pack_manifest": pack_manifest,
    }
    _write_json(root / ".tmp/clean_machine_proof_pack_baseline_check.json", report)
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["summary"]["pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
