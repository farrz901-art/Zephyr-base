from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path


DEFAULT_LAYOUT_ROOT = Path(".tmp/base_install_layout/ZephyrBase")
MARKER = "ZEPHYR_BASE_S12_INSTALL_LAYOUT_MARKER"
LAYOUT_VENV = Path(".runtime/base_runtime_venv")
OUTPUT_DIR = Path(".tmp/s12_install_layout_runtime_smoke")


def _write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _run(command: list[str], cwd: Path, env: dict[str, str] | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(command, cwd=cwd, check=False, capture_output=True, text=True, env=env)


def _read_json(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run a runtime smoke from the Zephyr Base install layout root.")
    parser.add_argument("--layout-root", type=Path, default=DEFAULT_LAYOUT_ROOT)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)

    root = Path(__file__).resolve().parents[1]
    layout_root = args.layout_root if args.layout_root.is_absolute() else (root / args.layout_root).resolve()
    bootstrap_script = layout_root / "checks/bootstrap_base_runtime.py"
    if not bootstrap_script.exists():
        raise FileNotFoundError(f"Missing layout bootstrap script: {bootstrap_script}")

    env = os.environ.copy()
    bootstrap = _run(
        [sys.executable, str(bootstrap_script), "--venv-root", str(LAYOUT_VENV), "--json"],
        layout_root,
        env=env,
    )
    bootstrap_report_path = layout_root / ".tmp/base_runtime_bootstrap.json"
    bootstrap_report = _read_json(bootstrap_report_path) if bootstrap_report_path.exists() else {}
    managed_python = (
        _read_json(bootstrap_report_path).get("runtime", {}).get("managed_python")
        if bootstrap_report_path.exists()
        else None
    )
    if isinstance(managed_python, dict):
        managed_python = None
    managed_python_path = Path(str(managed_python)) if managed_python else None

    request_path = layout_root / ".tmp/s12_install_layout_request.json"
    output_dir = layout_root / OUTPUT_DIR
    output_dir.mkdir(parents=True, exist_ok=True)
    request = {
        "schema_version": 1,
        "request_id": "s12-install-layout-runtime-smoke",
        "input_kind": "local_text",
        "inline_text": MARKER,
        "output_dir": str(output_dir),
        "requested_outputs": [
            "normalized_text",
            "content_evidence",
            "receipt",
            "filesystem_output",
        ],
    }
    request_path.write_text(json.dumps(request, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    run_completed: subprocess.CompletedProcess[str] | None = None
    run_result_path = output_dir / "run_result.json"
    run_result: dict[str, object] = {}
    if managed_python_path is not None and managed_python_path.exists():
        run_env = env.copy()
        run_env["ZEPHYR_BASE_PYTHON"] = str(managed_python_path)
        run_completed = _run(
            [
                str(managed_python_path),
                str(layout_root / "public-core-bridge/run_public_core_adapter.py"),
                "--request",
                str(request_path),
                "--out-dir",
                str(output_dir),
                "--bundle-root",
                str(layout_root / "runtime/public-core-bundle"),
                "--json",
            ],
            layout_root,
            env=run_env,
        )
        if run_result_path.exists():
            run_result = _read_json(run_result_path)

    usage_fact = run_result.get("usage_fact", {}) if isinstance(run_result, dict) else {}
    if not isinstance(usage_fact, dict):
        usage_fact = {}
    report = {
        "schema_version": 1,
        "report_id": "zephyr.base.s12.install_layout_runtime_smoke.v1",
        "summary": {
            "pass": bootstrap.returncode == 0
            and managed_python_path is not None
            and managed_python_path.exists()
            and run_completed is not None
            and run_completed.returncode == 0
            and run_result_path.exists()
            and MARKER in str(run_result.get("normalized_text_preview", ""))
            and usage_fact.get("billing_semantics") is False
            and run_result.get("bundled_runtime_used") is True
            and run_result.get("fixture_runner_used") is False
            and run_result.get("zephyr_dev_working_tree_required") is False
            and run_result.get("requires_network") is False
            and run_result.get("requires_p45_substrate") is False,
            "layout_root": str(layout_root),
            "selected_python_is_managed_runtime": managed_python_path is not None
            and str(managed_python_path).startswith(str(layout_root)),
        },
        "bootstrap": bootstrap_report,
        "runtime": {
            "selected_python": str(managed_python_path) if managed_python_path is not None else None,
            "selected_python_is_managed_runtime": managed_python_path is not None
            and str(managed_python_path).startswith(str(layout_root)),
            "uses_current_shell_python_for_execution": False,
        },
        "evidence": {
            "run_result_exists": run_result_path.exists(),
            "marker_found": MARKER in str(run_result.get("normalized_text_preview", "")),
            "billing_semantics": usage_fact.get("billing_semantics"),
            "bundled_runtime_used": run_result.get("bundled_runtime_used"),
            "fixture_runner_used": run_result.get("fixture_runner_used"),
            "zephyr_dev_working_tree_required": run_result.get("zephyr_dev_working_tree_required"),
            "requires_network": run_result.get("requires_network"),
            "requires_p45_substrate": run_result.get("requires_p45_substrate"),
        },
        "adapter": {
            "stdout": None if run_completed is None else run_completed.stdout.strip(),
            "stderr": None if run_completed is None else run_completed.stderr.strip(),
            "returncode": None if run_completed is None else run_completed.returncode,
        },
    }
    _write_json(root / ".tmp/base_install_layout_runtime_smoke.json", report)
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["summary"]["pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
