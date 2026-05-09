from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path


DEFAULT_MANAGED_VENV = Path(".tmp/base_runtime_venv")
FALLBACK_MANAGED_VENV = Path(".tmp/base_runtime_venv_managed")
POINTER_PATH = Path(".tmp/base_runtime_python_path.txt")


def _write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _managed_python_from_root(venv_root: Path) -> Path:
    if os.name == "nt":
        return venv_root / "Scripts" / "python.exe"
    return venv_root / "bin" / "python"


def _normalize_python(raw: str) -> str:
    candidate = Path(raw)
    if candidate.is_absolute():
        return str(candidate)
    resolved = shutil.which(raw)
    return resolved or raw


def _pointer_python(root: Path) -> Path | None:
    pointer = root / POINTER_PATH
    if not pointer.exists():
        return None
    raw = pointer.read_text(encoding="utf-8").strip()
    if not raw:
        return None
    return Path(raw)


def _managed_python_candidates(root: Path) -> list[Path]:
    candidates: list[Path] = []

    def add(candidate: Path) -> None:
        resolved = candidate.resolve()
        if resolved not in candidates:
            candidates.append(resolved)

    pointer_python = _pointer_python(root)
    if pointer_python is not None:
        add(pointer_python)
    add(_managed_python_from_root(root / DEFAULT_MANAGED_VENV))
    add(_managed_python_from_root(root / FALLBACK_MANAGED_VENV))
    return candidates


def _preferred_managed_python(root: Path) -> Path:
    for candidate in _managed_python_candidates(root):
        if candidate.exists():
            return candidate
    return _managed_python_from_root(root / DEFAULT_MANAGED_VENV)


def _selected_python(root: Path, *, explicit_python: str | None, prefer_managed: bool) -> tuple[str, bool]:
    managed_candidates = _managed_python_candidates(root)
    preferred_managed = _preferred_managed_python(root)
    env_python = os.environ.get("ZEPHYR_BASE_PYTHON")

    def is_managed(raw: str) -> bool:
        candidate = Path(_normalize_python(raw))
        return any(existing == candidate for existing in managed_candidates)

    if explicit_python:
        normalized = _normalize_python(explicit_python)
        return normalized, is_managed(normalized)
    if env_python:
        normalized = _normalize_python(env_python)
        return normalized, is_managed(normalized)
    if prefer_managed and preferred_managed.exists():
        return str(preferred_managed), True
    fallback = shutil.which("python") or sys.executable or "python"
    normalized_fallback = _normalize_python(fallback)
    return normalized_fallback, is_managed(normalized_fallback)


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
    parser.add_argument("--python", dest="explicit_python", default=None)
    parser.add_argument("--prefer-managed", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)

    root = Path(__file__).resolve().parents[1]
    managed_candidates = _managed_python_candidates(root)
    preferred_managed = _preferred_managed_python(root)
    selected_python, selected_is_managed = _selected_python(
        root,
        explicit_python=args.explicit_python,
        prefer_managed=args.prefer_managed,
    )
    selected_exists = Path(selected_python).exists() if Path(selected_python).is_absolute() else shutil.which(selected_python) is not None
    shell_python = str(Path(sys.executable).resolve())
    selected_differs_from_shell_python = selected_python != shell_python
    pydantic_importable = selected_exists and _importable(selected_python, "pydantic")
    unstructured_importable = selected_exists and _importable(selected_python, "unstructured")
    passed = selected_exists and pydantic_importable and unstructured_importable

    report = {
        "schema_version": 1,
        "report_id": "zephyr.base.s11.python_runtime_dependencies_check.v1",
        "summary": {
            "pass": passed,
            "selected_python": selected_python,
            "selected_python_is_managed_runtime": selected_is_managed,
            "selected_python_differs_from_current_shell_python": selected_differs_from_shell_python,
            "pydantic_importable": pydantic_importable,
            "unstructured_importable": unstructured_importable,
        },
        "selected_python": selected_python,
        "managed_python_candidate": str(preferred_managed),
        "managed_python_candidates": [str(candidate) for candidate in managed_candidates],
        "selected_python_exists": selected_exists,
        "selected_python_is_managed_runtime": selected_is_managed,
        "selected_python_differs_from_current_shell_python": selected_differs_from_shell_python,
        "current_shell_python": shell_python,
        "pydantic_importable": pydantic_importable,
        "unstructured_importable": unstructured_importable,
        "recommendation": (
            "Set ZEPHYR_BASE_PYTHON to a Python executable with Base runtime dependencies installed. This is not installer-complete runtime proof."
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
