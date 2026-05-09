from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path


REQUIRED_MODULES = ("pydantic", "unstructured")
DEFAULT_VENV_ROOT = Path(".tmp/base_runtime_venv")
FALLBACK_VENV_ROOT = Path(".tmp/base_runtime_venv_managed")
POINTER_PATH = Path(".tmp/base_runtime_python_path.txt")


def _managed_python_path(venv_root: Path) -> Path:
    if os.name == "nt":
        return venv_root / "Scripts" / "python.exe"
    return venv_root / "bin" / "python"


def _write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _run(command: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(command, check=False, capture_output=True, text=True)


def _importable(python_exe: Path, module_name: str) -> bool:
    completed = _run([str(python_exe), "-c", f"import {module_name}"])
    return completed.returncode == 0


def _runtime_ready(python_exe: Path) -> bool:
    return python_exe.exists() and all(_importable(python_exe, module_name) for module_name in REQUIRED_MODULES)


def _create_venv(selected_python: str, venv_root: Path) -> subprocess.CompletedProcess[str]:
    return _run([selected_python, "-m", "venv", str(venv_root)])


def _install_requirements(managed_python: Path, requirements_path: Path) -> subprocess.CompletedProcess[str]:
    return _run(
        [
            str(managed_python),
            "-m",
            "pip",
            "install",
            "--disable-pip-version-check",
            "--prefer-binary",
            "--timeout",
            "120",
            "--retries",
            "5",
            "-r",
            str(requirements_path),
        ]
    )


def _remove_tree_with_retries(path: Path) -> tuple[bool, str | None]:
    if not path.exists():
        return True, None
    last_error: str | None = None
    for _ in range(5):
        try:
            shutil.rmtree(path)
            return True, None
        except PermissionError as exc:
            last_error = str(exc)
            time.sleep(1.0)
    return False, last_error


def _pointer_file(root: Path) -> Path:
    return root / POINTER_PATH


def _load_pointer_python(root: Path) -> Path | None:
    pointer = _pointer_file(root)
    if not pointer.exists():
        return None
    raw = pointer.read_text(encoding="utf-8").strip()
    if not raw:
        return None
    return Path(raw)


def _write_pointer_python(root: Path, python_path: Path) -> None:
    pointer = _pointer_file(root)
    pointer.parent.mkdir(parents=True, exist_ok=True)
    pointer.write_text(str(python_path) + "\n", encoding="utf-8")


def _venv_root_for_python(python_path: Path) -> Path:
    return python_path.parent.parent


def _candidate_roots(root: Path, primary_root: Path) -> list[Path]:
    candidates: list[Path] = []

    def add(candidate: Path) -> None:
        resolved = candidate.resolve()
        if resolved not in candidates:
            candidates.append(resolved)

    add(primary_root)
    pointer_python = _load_pointer_python(root)
    if pointer_python is not None:
        add(_venv_root_for_python(pointer_python))
    add((root / FALLBACK_VENV_ROOT).resolve())
    return candidates


def _ensure_runtime_on_root(
    *,
    selected_python: str,
    venv_root: Path,
    requirements_path: Path,
) -> tuple[bool, dict[str, object]]:
    managed_python = _managed_python_path(venv_root)
    create_detail = ""
    install_detail: str | None = None
    remove_detail: str | None = None
    install_strategy = "uninitialized"

    if managed_python.exists() and _runtime_ready(managed_python):
        return True, {
            "managed_venv_created": True,
            "managed_python": str(managed_python),
            "managed_runtime_root": str(venv_root),
            "create_detail": "Reusing existing managed runtime path.",
            "install_detail": None,
            "remove_detail": None,
            "install_strategy": "reuse_existing_managed_runtime",
            "requirements_installed": True,
        }

    if managed_python.exists():
        install_completed = _install_requirements(managed_python, requirements_path)
        install_detail = (install_completed.stdout + "\n" + install_completed.stderr).strip()
        if install_completed.returncode == 0 and _runtime_ready(managed_python):
            return True, {
                "managed_venv_created": True,
                "managed_python": str(managed_python),
                "managed_runtime_root": str(venv_root),
                "create_detail": "Repaired an existing managed runtime path.",
                "install_detail": install_detail,
                "remove_detail": None,
                "install_strategy": "repair_existing_managed_runtime",
                "requirements_installed": True,
            }

    if venv_root.exists():
        removed, remove_detail = _remove_tree_with_retries(venv_root)
        if not removed:
            return False, {
                "managed_venv_created": False,
                "managed_python": str(managed_python),
                "managed_runtime_root": str(venv_root),
                "create_detail": "Managed runtime bootstrap could not clear an incomplete runtime directory.",
                "install_detail": install_detail,
                "remove_detail": remove_detail,
                "install_strategy": "failed_to_remove_existing_runtime",
                "requirements_installed": False,
            }

    create_completed = _create_venv(selected_python, venv_root)
    create_detail = (create_completed.stdout + "\n" + create_completed.stderr).strip()
    managed_venv_created = create_completed.returncode == 0 and managed_python.exists()
    if not managed_venv_created:
        return False, {
            "managed_venv_created": False,
            "managed_python": str(managed_python),
            "managed_runtime_root": str(venv_root),
            "create_detail": create_detail,
            "install_detail": None,
            "remove_detail": remove_detail,
            "install_strategy": "create_fresh_managed_runtime_failed",
            "requirements_installed": False,
        }

    install_completed = _install_requirements(managed_python, requirements_path)
    install_detail = (install_completed.stdout + "\n" + install_completed.stderr).strip()
    requirements_installed = install_completed.returncode == 0 and _runtime_ready(managed_python)
    return requirements_installed, {
        "managed_venv_created": True,
        "managed_python": str(managed_python),
        "managed_runtime_root": str(venv_root),
        "create_detail": create_detail,
        "install_detail": install_detail,
        "remove_detail": remove_detail,
        "install_strategy": "create_fresh_managed_runtime",
        "requirements_installed": requirements_installed,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Bootstrap the Zephyr-base managed runtime.")
    parser.add_argument("--python", dest="selected_python", default=None)
    parser.add_argument("--venv-root", type=Path, default=DEFAULT_VENV_ROOT)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)

    root = Path(__file__).resolve().parents[1]
    requirements_path = root / "runtime/python-runtime/base-runtime-requirements.txt"
    selected_python = args.selected_python or os.environ.get("ZEPHYR_BASE_PYTHON") or sys.executable
    primary_root = args.venv_root if args.venv_root.is_absolute() else (root / args.venv_root).resolve()

    chosen_report: dict[str, object] | None = None
    chosen_pass = False
    for candidate_root in _candidate_roots(root, primary_root):
        attempt_pass, attempt_report = _ensure_runtime_on_root(
            selected_python=selected_python,
            venv_root=candidate_root,
            requirements_path=requirements_path,
        )
        chosen_report = attempt_report
        if attempt_pass:
            chosen_pass = True
            _write_pointer_python(root, Path(str(attempt_report["managed_python"])))
            break

    if chosen_report is None:
        chosen_report = {
            "managed_venv_created": False,
            "managed_python": str(_managed_python_path(primary_root)),
            "managed_runtime_root": str(primary_root),
            "create_detail": "No managed runtime candidate root was available.",
            "install_detail": None,
            "remove_detail": None,
            "install_strategy": "no_candidate_root",
            "requirements_installed": False,
        }

    managed_python = str(chosen_report["managed_python"])
    managed_runtime_root = str(chosen_report["managed_runtime_root"])
    requirements_installed = bool(chosen_report["requirements_installed"])
    fallback_root = (root / FALLBACK_VENV_ROOT).resolve()
    fallback_used = Path(managed_runtime_root) == fallback_root

    report = {
        "schema_version": 1,
        "report_id": "zephyr.base.s11.bootstrap_base_runtime.v1",
        "summary": {
            "pass": chosen_pass,
            "managed_venv_created": bool(chosen_report["managed_venv_created"]),
            "selected_python": selected_python,
            "requirements_installed": requirements_installed,
        },
        "runtime": {
            "managed_python": managed_python,
            "managed_runtime_root": managed_runtime_root,
            "uses_current_shell_python_for_execution": False,
            "embedded_python_runtime": False,
            "installer_runtime_complete": False,
        },
        "create_detail": chosen_report["create_detail"],
        "install_detail": chosen_report["install_detail"],
        "install_strategy": chosen_report["install_strategy"],
        "remove_detail": chosen_report["remove_detail"],
        "fallback_managed_root_used": fallback_used,
        "pointer_file": str(_pointer_file(root)),
        "recommendation": (
            "Managed runtime bootstrap succeeded. Use the managed Python for local Base validation."
            if chosen_pass and not fallback_used
            else "Managed runtime bootstrap succeeded through the repo-local fallback managed runtime path. This proves a managed interpreter first slice, not a clean-machine installer-complete runtime."
            if chosen_pass
            else "Managed runtime bootstrap did not complete. This is not installer-complete runtime proof."
        ),
    }
    out_path = root / ".tmp" / "base_runtime_bootstrap.json"
    _write_json(out_path, report)
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if chosen_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
