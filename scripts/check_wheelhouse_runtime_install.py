from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

MARKER = "ZEPHYR_BASE_S11_WHEELHOUSE_RUNTIME_MARKER"
OUTPUT_DIR = Path(".tmp/s11_wheelhouse_runtime_flow")


def _write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _run(command: list[str], cwd: Path, env: dict[str, str] | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(command, cwd=cwd, check=False, capture_output=True, text=True, env=env)


def _load_json(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def _venv_python(venv_root: Path) -> Path:
    if os.name == "nt":
        return venv_root / "Scripts" / "python.exe"
    return venv_root / "bin" / "python"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate offline wheelhouse installation for the Base runtime baseline.")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)

    root = Path(__file__).resolve().parents[1]
    wheelhouse_root = root / ".tmp/base_runtime_wheelhouse"
    requirements_path = root / "runtime/python-runtime/base-runtime-requirements.txt"
    venv_root = root / ".tmp/base_runtime_venv_from_wheelhouse"
    if venv_root.exists():
        shutil.rmtree(venv_root)

    python_exe = sys.executable
    created = False
    install_pass = False
    cargo_run_pass = False
    run_result: dict[str, object] = {}
    if wheelhouse_root.exists() and any(wheelhouse_root.iterdir()):
        create_completed = _run([python_exe, "-m", "venv", str(venv_root)], root)
        created = create_completed.returncode == 0
        wheel_python = _venv_python(venv_root)
        if created and wheel_python.exists():
            install_completed = _run(
                [
                    str(wheel_python),
                    "-m",
                    "pip",
                    "install",
                    "--no-index",
                    "--find-links",
                    str(wheelhouse_root),
                    "-r",
                    str(requirements_path),
                ],
                root,
            )
            install_pass = install_completed.returncode == 0
            cargo_path = shutil.which("cargo")
            if install_pass and cargo_path:
                output_dir = root / OUTPUT_DIR
                if output_dir.exists():
                    shutil.rmtree(output_dir)
                output_dir.mkdir(parents=True, exist_ok=True)
                env = os.environ.copy()
                env["ZEPHYR_BASE_PYTHON"] = str(wheel_python)
                run_completed = _run(
                    [
                        cargo_path,
                        "run",
                        "--manifest-path",
                        "src-tauri/Cargo.toml",
                        "--",
                        "run-local-text",
                        MARKER,
                        OUTPUT_DIR.as_posix(),
                    ],
                    root,
                    env=env,
                )
                cargo_run_pass = run_completed.returncode == 0
                run_result_path = output_dir / "run_result.json"
                if run_result_path.exists():
                    run_result = _load_json(run_result_path)

    usage_fact = run_result.get("usage_fact", {}) if isinstance(run_result, dict) else {}
    if not isinstance(usage_fact, dict):
        usage_fact = {}
    marker_found = MARKER in str(run_result.get("normalized_text_preview", ""))
    wheelhouse_install_pass = all((
        created,
        install_pass,
        cargo_run_pass,
        marker_found,
        usage_fact.get("billing_semantics") is False,
    ))
    report = {
        "schema_version": 1,
        "report_id": "zephyr.base.s11.wheelhouse_runtime_install_check.v1",
        "summary": {
            "pass": wheelhouse_install_pass,
            "wheelhouse_install_pass": wheelhouse_install_pass,
            "offline_runtime_install_proven_locally": wheelhouse_install_pass,
        },
        "wheelhouse_bundled": False,
        "wheelhouse_root": str(wheelhouse_root),
        "venv_root": str(venv_root),
        "marker_found": marker_found,
        "run_result_exists": bool(run_result),
    }
    out_path = root / ".tmp" / "wheelhouse_runtime_install_check.json"
    _write_json(out_path, report)
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if wheelhouse_install_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
