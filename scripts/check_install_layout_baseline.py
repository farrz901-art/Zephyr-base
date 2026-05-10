from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path


REQUIRED_FILES = [
    Path("docs/TAURI_GENERATED_ARTIFACTS.md"),
    Path("docs/BASE_INSTALL_LAYOUT_POLICY.md"),
    Path("docs/CLEAN_MACHINE_RUNTIME_PROOF_PLAN.md"),
    Path("docs/CLEAN_MACHINE_RUNTIME_PROOF.md"),
    Path("docs/MANUAL_CLEAN_MACHINE_RUNTIME_PROOF.md"),
    Path("docs/OFFLINE_RUNTIME_WHEELHOUSE_PROOF.md"),
    Path("runtime/python-runtime/WHEELHOUSE_POLICY.md"),
    Path("scripts/check_generated_artifact_hygiene.py"),
    Path("scripts/build_base_install_layout.py"),
    Path("scripts/audit_base_install_layout.py"),
    Path("scripts/check_base_install_layout_runtime_smoke.py"),
    Path("scripts/build_clean_machine_proof_pack.py"),
    Path("scripts/run_clean_machine_runtime_proof.py"),
    Path("scripts/validate_clean_machine_runtime_proof.py"),
    Path("scripts/audit_clean_machine_pack_relocation.py"),
    Path("scripts/check_clean_machine_pack_local_simulation.py"),
    Path("scripts/import_clean_machine_proof.py"),
    Path("scripts/check_clean_machine_proof_pack_baseline.py"),
    Path("scripts/build_clean_machine_offline_proof_pack.py"),
    Path("scripts/check_offline_proof_pack_local_simulation.py"),
    Path("scripts/import_offline_runtime_proof.py"),
]


def _write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _tracked_files(root: Path) -> list[str]:
    completed = subprocess.run(
        ["git", "-c", f"safe.directory={root}", "-C", str(root), "ls-files"],
        check=False,
        capture_output=True,
        text=True,
    )
    if completed.returncode != 0:
        return []
    return [line.strip() for line in completed.stdout.splitlines() if line.strip()]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Check the install-layout and clean-machine baseline slice.")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)

    root = Path(__file__).resolve().parents[1]
    missing = [path.as_posix() for path in REQUIRED_FILES if not (root / path).exists()]
    tracked = _tracked_files(root)
    src_tauri_gen_tracked = any(path.startswith("src-tauri/gen/") for path in tracked)
    venv_or_wheelhouse_tracked = any(
        path.startswith(prefix)
        for prefix in (
            ".tmp/base_runtime_venv/",
            ".tmp/base_runtime_venv_managed/",
            ".tmp/base_runtime_wheelhouse/",
            ".tmp/base_runtime_venv_from_wheelhouse/",
            ".venv/",
        )
        for path in tracked
    )
    report = {
        "schema_version": 1,
        "report_id": "zephyr.base.s13.install_layout_baseline_check.v1",
        "summary": {
            "pass": not missing and not src_tauri_gen_tracked and not venv_or_wheelhouse_tracked,
            "install_layout_policy_exists": (root / "docs/BASE_INSTALL_LAYOUT_POLICY.md").exists(),
            "clean_machine_policy_exists": (root / "docs/CLEAN_MACHINE_RUNTIME_PROOF.md").exists(),
            "manual_clean_machine_doc_exists": (root / "docs/MANUAL_CLEAN_MACHINE_RUNTIME_PROOF.md").exists(),
            "generated_artifact_doc_exists": (root / "docs/TAURI_GENERATED_ARTIFACTS.md").exists(),
            "clean_machine_plan_exists": (root / "docs/CLEAN_MACHINE_RUNTIME_PROOF_PLAN.md").exists(),
            "generated_artifact_hygiene_checker_exists": (root / "scripts/check_generated_artifact_hygiene.py").exists(),
            "build_script_exists": (root / "scripts/build_base_install_layout.py").exists(),
            "audit_script_exists": (root / "scripts/audit_base_install_layout.py").exists(),
            "runtime_smoke_script_exists": (root / "scripts/check_base_install_layout_runtime_smoke.py").exists(),
            "clean_machine_pack_builder_exists": (root / "scripts/build_clean_machine_proof_pack.py").exists(),
            "clean_machine_validator_exists": (root / "scripts/validate_clean_machine_runtime_proof.py").exists(),
            "offline_pack_builder_exists": (root / "scripts/build_clean_machine_offline_proof_pack.py").exists(),
            "offline_pack_simulation_exists": (root / "scripts/check_offline_proof_pack_local_simulation.py").exists(),
            "src_tauri_gen_tracked": src_tauri_gen_tracked,
            "venv_or_wheelhouse_tracked": venv_or_wheelhouse_tracked,
        },
        "missing_files": missing,
    }
    _write_json(root / ".tmp/install_layout_baseline_check.json", report)
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["summary"]["pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
