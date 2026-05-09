from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path


def _write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build a local wheelhouse for the Zephyr-base runtime baseline.")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)

    root = Path(__file__).resolve().parents[1]
    requirements_path = root / "runtime/python-runtime/base-runtime-requirements.txt"
    wheelhouse_root = root / ".tmp/base_runtime_wheelhouse"
    if wheelhouse_root.exists():
        shutil.rmtree(wheelhouse_root)
    wheelhouse_root.mkdir(parents=True, exist_ok=True)
    selected_python = os.environ.get("ZEPHYR_BASE_PYTHON") or sys.executable
    completed = subprocess.run(
        [
            selected_python,
            "-m",
            "pip",
            "download",
            "--disable-pip-version-check",
            "--prefer-binary",
            "--timeout",
            "120",
            "--retries",
            "5",
            "-r",
            str(requirements_path),
            "-d",
            str(wheelhouse_root),
        ],
        check=False,
        capture_output=True,
        text=True,
    )
    wheel_files = sorted(path.name for path in wheelhouse_root.iterdir() if path.is_file())
    built = completed.returncode == 0 and len(wheel_files) > 0
    report = {
        "schema_version": 1,
        "report_id": "zephyr.base.s11.base_runtime_wheelhouse_build.v1",
        "summary": {
            "pass": built,
            "wheelhouse_build_attempted": True,
            "wheelhouse_built": built,
        },
        "selected_python": selected_python,
        "wheelhouse_root": str(wheelhouse_root),
        "wheel_files": wheel_files,
        "wheelhouse_bundled": False,
        "download_detail": (completed.stdout + "\n" + completed.stderr).strip(),
    }
    out_path = root / ".tmp" / "base_runtime_wheelhouse_manifest.json"
    _write_json(out_path, report)
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if built else 1


if __name__ == "__main__":
    raise SystemExit(main())
