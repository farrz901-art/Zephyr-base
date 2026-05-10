from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path


REQUIRED_FILES = [
    Path("docs/OFFLINE_RUNTIME_WHEELHOUSE_PROOF.md"),
    Path("runtime/python-runtime/WHEELHOUSE_POLICY.md"),
    Path("runtime/python-runtime/wheelhouse_manifest.schema.json"),
    Path("scripts/build_base_runtime_wheelhouse.py"),
    Path("scripts/check_wheelhouse_runtime_install.py"),
    Path("scripts/check_offline_install_network_guard.py"),
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
    parser = argparse.ArgumentParser(description="Check the offline wheelhouse runtime baseline.")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)

    root = Path(__file__).resolve().parents[1]
    missing = [path.as_posix() for path in REQUIRED_FILES if not (root / path).exists()]
    tracked = _tracked_files(root)
    wheelhouse_tracked = any(path.endswith(".whl") or path.endswith(".tar.gz") for path in tracked)
    venv_tracked = any(
        path.startswith(prefix)
        for path in tracked
        for prefix in (
            ".tmp/base_runtime_venv/",
            ".tmp/base_runtime_venv_managed/",
            ".tmp/base_runtime_venv_from_wheelhouse/",
            ".venv/",
        )
    )

    report = {
        "schema_version": 1,
        "report_id": "zephyr.base.s14.offline_runtime_baseline_check.v1",
        "summary": {
            "pass": not missing and not wheelhouse_tracked and not venv_tracked,
            "offline_runtime_policy_exists": (root / "docs/OFFLINE_RUNTIME_WHEELHOUSE_PROOF.md").exists(),
            "wheelhouse_builder_exists": (root / "scripts/build_base_runtime_wheelhouse.py").exists(),
            "wheelhouse_install_checker_exists": (root / "scripts/check_wheelhouse_runtime_install.py").exists(),
            "offline_network_guard_exists": (root / "scripts/check_offline_install_network_guard.py").exists(),
            "offline_proof_pack_builder_exists": (root / "scripts/build_clean_machine_offline_proof_pack.py").exists(),
            "wheelhouse_committed": wheelhouse_tracked,
            "venv_committed": venv_tracked,
        },
        "missing_files": missing,
        "tracked_wheel_files": [path for path in tracked if path.endswith(".whl") or path.endswith(".tar.gz")],
    }
    _write_json(root / ".tmp/offline_runtime_baseline_check.json", report)
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["summary"]["pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
