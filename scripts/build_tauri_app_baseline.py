from __future__ import annotations

import argparse
import json
import shutil
import subprocess
from pathlib import Path


OUTPUT_PATH = Path(".tmp/tauri_app_build_baseline.json")
VCVARS64 = Path(r"E:/vs_buildtools/2022/BuildTools/VC/Auxiliary/Build/vcvars64.bat")


def _write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _run(command: list[str], cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(command, cwd=cwd, check=False, capture_output=True, text=True)


def _run_windows_shell(command: str, cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["cmd.exe", "/c", command],
        cwd=cwd,
        check=False,
        capture_output=True,
        text=True,
    )


def _run_npm_build(cwd: Path) -> subprocess.CompletedProcess[str]:
    npm_cmd = shutil.which("npm.cmd") or shutil.which("npm")
    if npm_cmd:
        return _run([npm_cmd, "--prefix", "ui", "run", "build"], cwd)
    return _run_windows_shell("npm --prefix ui run build", cwd)


def _run_cargo(args: list[str], cwd: Path) -> subprocess.CompletedProcess[str]:
    cargo = shutil.which("cargo")
    if cargo:
        direct = _run([cargo, *args], cwd)
        if direct.returncode == 0:
            return direct
    if VCVARS64.exists():
        cargo_args = " ".join(args)
        command = f'"{VCVARS64}" && cd /d "{cwd}" && cargo {cargo_args}'
        return _run_windows_shell(command, cwd)
    if cargo:
        return _run([cargo, *args], cwd)
    return subprocess.CompletedProcess(args=["cargo", *args], returncode=1, stdout="", stderr="cargo not found")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build the Zephyr Base Tauri app baseline.")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)

    root = Path(__file__).resolve().parents[1]
    ui_build = _run_npm_build(root)
    cargo_check = _run_cargo(["check", "--manifest-path", "src-tauri/Cargo.toml"], root)
    cargo_release = _run_cargo(["build", "--manifest-path", "src-tauri/Cargo.toml", "--release"], root)

    release_binary = root / "src-tauri/target/release/zephyr-base-tauri-bridge.exe"
    if not release_binary.exists():
        release_binary = root / "target/release/zephyr-base-tauri-bridge.exe"
    tauri_app_present = release_binary.exists()
    report = {
        "schema_version": 1,
        "report_id": "zephyr.base.s15.tauri_app_build_baseline.v1",
        "summary": {
            "pass": ui_build.returncode == 0 and cargo_check.returncode == 0 and cargo_release.returncode == 0 and tauri_app_present,
            "ui_build_pass": ui_build.returncode == 0,
            "cargo_check_pass": cargo_check.returncode == 0,
            "cargo_release_build_pass": cargo_release.returncode == 0,
            "tauri_bundle_built": False,
            "tauri_app_present": tauri_app_present,
        },
        "release_binary_path": str(release_binary) if tauri_app_present else "",
        "tauri_bundle_built": False,
        "commands": {
            "ui_build": ["npm", "--prefix", "ui", "run", "build"],
            "cargo_check": ["cargo", "check", "--manifest-path", "src-tauri/Cargo.toml"],
            "cargo_release": ["cargo", "build", "--manifest-path", "src-tauri/Cargo.toml", "--release"],
        },
        "ui_build": {
            "returncode": ui_build.returncode,
            "stdout": ui_build.stdout.strip(),
            "stderr": ui_build.stderr.strip(),
        },
        "cargo_check": {
            "returncode": cargo_check.returncode,
            "stdout": cargo_check.stdout.strip(),
            "stderr": cargo_check.stderr.strip(),
        },
        "cargo_release": {
            "returncode": cargo_release.returncode,
            "stdout": cargo_release.stdout.strip(),
            "stderr": cargo_release.stderr.strip(),
        },
    }
    _write_json(root / OUTPUT_PATH, report)
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["summary"]["pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
