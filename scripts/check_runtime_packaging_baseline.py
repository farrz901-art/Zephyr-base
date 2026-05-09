from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path

REQUIRED_PATHS = [
    Path("docs/PACKAGED_RUNTIME_BASELINE.md"),
    Path("runtime/python-runtime/base-runtime-requirements.in"),
    Path("runtime/python-runtime/base-runtime-requirements.txt"),
    Path("runtime/python-runtime/README.md"),
    Path("runtime/python-runtime/runtime_manifest.json"),
    Path("scripts/bootstrap_base_runtime.py"),
    Path("scripts/check_python_runtime_dependencies.py"),
    Path("scripts/check_managed_runtime_flow.py"),
    Path("scripts/build_base_runtime_wheelhouse.py"),
    Path("scripts/check_wheelhouse_runtime_install.py"),
]
TRACKED_FORBIDDEN_PREFIXES = (
    ".tmp/base_runtime_venv/",
    ".tmp/base_runtime_wheelhouse/",
    ".tmp/base_runtime_venv_from_wheelhouse/",
    ".venv/",
)


def _write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _load_json(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def _tracked_files(root: Path) -> list[str]:
    completed = subprocess.run(["git", "-C", str(root), "ls-files"], check=False, capture_output=True, text=True)
    if completed.returncode != 0:
        return []
    return [line.strip() for line in completed.stdout.splitlines() if line.strip()]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Check the Zephyr-base runtime packaging baseline.")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)

    root = Path(__file__).resolve().parents[1]
    missing = [path.as_posix() for path in REQUIRED_PATHS if not (root / path).exists()]
    manifest = _load_json(root / "runtime/python-runtime/runtime_manifest.json")
    tracked = _tracked_files(root)
    tracked_forbidden = [path for path in tracked if path.startswith(TRACKED_FORBIDDEN_PREFIXES)]
    venv_committed = any(path.startswith((".tmp/base_runtime_venv/", ".tmp/base_runtime_venv_from_wheelhouse/", ".venv/")) for path in tracked_forbidden)
    wheelhouse_committed = any(path.startswith(".tmp/base_runtime_wheelhouse/") for path in tracked_forbidden)

    manifest_ok = (
        manifest.get("installer_runtime_complete") is False
        and manifest.get("embedded_python_runtime") is False
        and manifest.get("managed_venv_supported") is True
    )

    report = {
        "schema_version": 1,
        "report_id": "zephyr.base.s11.runtime_packaging_baseline_check.v1",
        "summary": {
            "pass": not missing and manifest_ok and not venv_committed and not wheelhouse_committed,
            "runtime_manifest_exists": (root / "runtime/python-runtime/runtime_manifest.json").exists(),
            "requirements_exist": (root / "runtime/python-runtime/base-runtime-requirements.txt").exists(),
            "bootstrap_script_exists": (root / "scripts/bootstrap_base_runtime.py").exists(),
            "managed_runtime_checker_exists": (root / "scripts/check_managed_runtime_flow.py").exists(),
            "managed_venv_supported": manifest.get("managed_venv_supported") is True,
            "installer_runtime_complete": manifest.get("installer_runtime_complete"),
            "embedded_python_runtime": manifest.get("embedded_python_runtime"),
            "venv_committed": venv_committed,
            "wheelhouse_committed": wheelhouse_committed,
        },
        "missing_files": missing,
        "tracked_forbidden": tracked_forbidden,
        "manifest_excerpt": manifest,
    }
    out_path = root / ".tmp" / "runtime_packaging_baseline_check.json"
    _write_json(out_path, report)
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["summary"]["pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
