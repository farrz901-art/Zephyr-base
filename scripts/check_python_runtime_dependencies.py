from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
from pathlib import Path


def _write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _importable(python_exe: str, module_name: str) -> bool:
    completed = subprocess.run(
        [python_exe, "-c", f"import {module_name}"],
        check=False,
        capture_output=True,
        text=True,
    )
    return completed.returncode == 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Check Python runtime dependencies for Zephyr-base.")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)

    root = Path(__file__).resolve().parents[1]
    selected_python = os.environ.get("ZEPHYR_BASE_PYTHON") or shutil.which("python") or "python"
    pydantic_importable = _importable(selected_python, "pydantic")
    unstructured_importable = _importable(selected_python, "unstructured")
    passed = pydantic_importable and unstructured_importable

    report = {
        "schema_version": 1,
        "report_id": "zephyr.base.s10p.python_runtime_dependencies_check.v1",
        "summary": {
            "pass": passed,
            "selected_python": selected_python,
            "pydantic_importable": pydantic_importable,
            "unstructured_importable": unstructured_importable,
        },
        "selected_python": selected_python,
        "pydantic_importable": pydantic_importable,
        "unstructured_importable": unstructured_importable,
        "recommendation": (
            "Set ZEPHYR_BASE_PYTHON to a Python executable with Base runtime dependencies installed. "
            "This is not installer-complete runtime proof."
            if not passed
            else "Selected Python already exposes the Base runtime dependencies."
        ),
    }
    out_path = root / ".tmp" / "python_runtime_dependencies_check.json"
    _write_json(out_path, report)
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
