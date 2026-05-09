from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

MARKER = "ZEPHYR_BASE_S11_MANAGED_RUNTIME_MARKER"
OUTPUT_DIR = Path(".tmp/s11_managed_runtime_flow")
DEFAULT_MANAGED_VENV = Path(".tmp/base_runtime_venv")
FALLBACK_MANAGED_VENV = Path(".tmp/base_runtime_venv_managed")
POINTER_PATH = Path(".tmp/base_runtime_python_path.txt")


def _write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _run(command: list[str], cwd: Path, env: dict[str, str] | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(command, cwd=cwd, check=False, capture_output=True, text=True, env=env)


def _load_json(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def _candidate_managed_pythons(root: Path) -> list[Path]:
    candidates: list[Path] = []

    def add(candidate: Path) -> None:
        resolved = candidate.resolve()
        if resolved not in candidates:
            candidates.append(resolved)

    pointer = root / POINTER_PATH
    if pointer.exists():
        raw = pointer.read_text(encoding="utf-8").strip()
        if raw:
            add(Path(raw))
    if os.name == "nt":
        add((root / DEFAULT_MANAGED_VENV / "Scripts" / "python.exe").resolve())
        add((root / FALLBACK_MANAGED_VENV / "Scripts" / "python.exe").resolve())
    else:
        add((root / DEFAULT_MANAGED_VENV / "bin" / "python").resolve())
        add((root / FALLBACK_MANAGED_VENV / "bin" / "python").resolve())
    return candidates


def _preferred_managed_python(root: Path) -> Path:
    for candidate in _candidate_managed_pythons(root):
        if candidate.exists():
            return candidate
    return _candidate_managed_pythons(root)[0]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate the Zephyr-base managed runtime flow.")
    parser.add_argument("--bootstrap", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)

    root = Path(__file__).resolve().parents[1]
    cargo = shutil.which("cargo")
    cargo_available = cargo is not None
    managed_python = _preferred_managed_python(root)

    bootstrap_attempted = False
    bootstrap_pass = False
    if not managed_python.exists() and args.bootstrap:
        bootstrap_attempted = True
        bootstrap_completed = _run([sys.executable, "scripts/bootstrap_base_runtime.py", "--json"], root)
        bootstrap_pass = bootstrap_completed.returncode == 0
        managed_python = _preferred_managed_python(root)
    elif managed_python.exists():
        bootstrap_pass = True

    dep_check_completed = _run(
        [sys.executable, "scripts/check_python_runtime_dependencies.py", "--python", str(managed_python), "--json"],
        root,
    ) if managed_python.exists() else None
    dep_check_pass = dep_check_completed is not None and dep_check_completed.returncode == 0
    dep_report = _load_json(root / ".tmp/python_runtime_dependencies_check.json") if (root / ".tmp/python_runtime_dependencies_check.json").exists() else {}

    output_dir = root / OUTPUT_DIR
    if output_dir.exists():
        shutil.rmtree(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    lineage: dict[str, object] = {}
    run_result: dict[str, object] = {}
    cargo_check_pass = False
    cargo_run_pass = False
    lineage_read_pass = False
    cargo_check_detail = "cargo not available"
    run_stdout = ""
    run_stderr = ""
    if cargo_available and managed_python.exists() and dep_check_pass:
        env = os.environ.copy()
        env["ZEPHYR_BASE_PYTHON"] = str(managed_python)
        cargo_check = _run([cargo, "check", "--manifest-path", "src-tauri/Cargo.toml"], root, env=env)
        cargo_check_pass = cargo_check.returncode == 0
        cargo_check_detail = (cargo_check.stdout + "\n" + cargo_check.stderr).strip()
        lineage_completed = _run([cargo, "run", "--manifest-path", "src-tauri/Cargo.toml", "--", "read-lineage-snapshot"], root, env=env)
        lineage_read_pass = lineage_completed.returncode == 0
        if lineage_read_pass and lineage_completed.stdout.strip():
            lineage = json.loads(lineage_completed.stdout)
        run_completed = _run(
            [cargo, "run", "--manifest-path", "src-tauri/Cargo.toml", "--", "run-local-text", MARKER, OUTPUT_DIR.as_posix()],
            root,
            env=env,
        )
        cargo_run_pass = run_completed.returncode == 0
        run_stdout = run_completed.stdout.strip()
        run_stderr = run_completed.stderr.strip()
        run_result_path = output_dir / "run_result.json"
        if run_result_path.exists():
            run_result = _load_json(run_result_path)

    usage_fact = run_result.get("usage_fact", {}) if isinstance(run_result, dict) else {}
    if not isinstance(usage_fact, dict):
        usage_fact = {}
    selected_python_path = lineage.get("selected_python_path") if isinstance(lineage, dict) else None
    selected_python_is_managed_runtime = bool(lineage.get("managed_python_runtime_used")) if isinstance(lineage, dict) else False
    uses_current_shell_python = bool(lineage.get("uses_current_python_environment")) if isinstance(lineage, dict) else True
    marker_found = MARKER in str(run_result.get("normalized_text_preview", ""))
    run_result_exists = (output_dir / "run_result.json").exists()

    passed = all((
        managed_python.exists(),
        dep_check_pass,
        cargo_available,
        cargo_check_pass,
        lineage_read_pass,
        cargo_run_pass,
        run_result_exists,
        marker_found,
        usage_fact.get("billing_semantics") is False,
        run_result.get("bundled_runtime_used") is True,
        run_result.get("fixture_runner_used") is False,
        run_result.get("zephyr_dev_working_tree_required") is False,
        run_result.get("requires_network") is False,
        run_result.get("requires_p45_substrate") is False,
        selected_python_is_managed_runtime,
        selected_python_path == str(managed_python),
        uses_current_shell_python is False,
    ))

    report = {
        "schema_version": 1,
        "report_id": "zephyr.base.s11.managed_runtime_flow_check.v1",
        "summary": {
            "pass": passed,
            "managed_runtime_available": managed_python.exists(),
            "managed_runtime_flow_pass": passed,
            "selected_python_is_managed_runtime": selected_python_is_managed_runtime,
            "uses_current_shell_python_for_verified_flow": uses_current_shell_python,
        },
        "bootstrap": {
            "attempted": bootstrap_attempted,
            "pass": bootstrap_pass,
        },
        "runtime": {
            "managed_python": str(managed_python),
            "selected_python_path": selected_python_path,
            "selected_python_is_managed_runtime": selected_python_is_managed_runtime,
            "uses_current_shell_python_for_verified_flow": uses_current_shell_python,
            "embedded_python_runtime": False,
            "installer_runtime_complete": False,
        },
        "evidence": {
            "run_result_exists": run_result_exists,
            "marker_found": marker_found,
            "billing_semantics": usage_fact.get("billing_semantics"),
            "bundled_runtime_used": run_result.get("bundled_runtime_used"),
            "fixture_runner_used": run_result.get("fixture_runner_used"),
            "zephyr_dev_working_tree_required": run_result.get("zephyr_dev_working_tree_required"),
            "requires_network": run_result.get("requires_network"),
            "requires_p45_substrate": run_result.get("requires_p45_substrate"),
        },
        "cargo": {
            "available": cargo_available,
            "check_pass": cargo_check_pass,
            "check_detail": cargo_check_detail,
            "run_pass": cargo_run_pass,
            "run_stdout": run_stdout,
            "run_stderr": run_stderr,
        },
        "dependency_check": dep_report,
    }
    out_path = root / ".tmp" / "managed_runtime_flow_check.json"
    _write_json(out_path, report)
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
