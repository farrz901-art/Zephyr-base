from __future__ import annotations

import argparse
import json
import platform
import shutil
import subprocess
import sys
from pathlib import Path


DEFAULT_WHEELHOUSE_ROOT = Path(".tmp/base_runtime_wheelhouse")
DEFAULT_MANIFEST_PATH = Path(".tmp/base_runtime_wheelhouse_manifest.json")


def _write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _run(command: list[str], cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(command, cwd=cwd, check=False, capture_output=True, text=True)


def _ensure_pip(python_exe: str, cwd: Path) -> subprocess.CompletedProcess[str]:
    pip_version = _run([python_exe, "-m", "pip", "--version"], cwd)
    if pip_version.returncode == 0:
        return pip_version
    return _run([python_exe, "-m", "ensurepip", "--upgrade"], cwd)


def _parse_direct_requirements(requirements_path: Path) -> list[str]:
    requirements: list[str] = []
    for raw_line in requirements_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        requirement = (
            line.split("==", 1)[0]
            .split(">=", 1)[0]
            .split("<=", 1)[0]
            .split("~=", 1)[0]
            .strip()
        )
        if requirement:
            requirements.append(requirement)
    return requirements


def _normalize_name(name: str) -> str:
    return name.strip().lower().replace("-", "_")


def _artifact_matches_requirement(filename: str, requirement: str) -> bool:
    return filename.lower().startswith(f"{_normalize_name(requirement)}-")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build the Zephyr-base runtime wheelhouse first slice.")
    parser.add_argument("--wheelhouse-root", type=Path, default=DEFAULT_WHEELHOUSE_ROOT)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)

    root = Path(__file__).resolve().parents[1]
    requirements_path = root / "runtime/python-runtime/base-runtime-requirements.txt"
    wheelhouse_root = (
        args.wheelhouse_root
        if args.wheelhouse_root.is_absolute()
        else (root / args.wheelhouse_root).resolve()
    )
    manifest_path = (root / DEFAULT_MANIFEST_PATH).resolve()

    if wheelhouse_root.exists():
        shutil.rmtree(wheelhouse_root)
    wheelhouse_root.mkdir(parents=True, exist_ok=True)

    direct_requirements = _parse_direct_requirements(requirements_path)
    ensure_pip = _ensure_pip(sys.executable, root)
    download_completed = _run(
        [
            sys.executable,
            "-m",
            "pip",
            "download",
            "--disable-pip-version-check",
            "--dest",
            str(wheelhouse_root),
            "-r",
            str(requirements_path),
        ],
        root,
    )

    artifacts = sorted(path.name for path in wheelhouse_root.iterdir() if path.is_file())
    wheel_files = [name for name in artifacts if name.endswith(".whl")]
    source_dist_only = [name for name in artifacts if name.endswith((".tar.gz", ".zip"))]
    installable_artifacts = [name for name in artifacts if name.endswith(".whl") or name.endswith((".tar.gz", ".zip"))]
    missing_requirements = [
        requirement
        for requirement in direct_requirements
        if not any(_artifact_matches_requirement(filename, requirement) for filename in installable_artifacts)
    ]

    report = {
        "schema_version": 1,
        "report_id": "zephyr.base.s14.wheelhouse_manifest.v1",
        "requirements_file": "runtime/python-runtime/base-runtime-requirements.txt",
        "wheelhouse_path": str(wheelhouse_root),
        "python_tag": f"cp{sys.version_info.major}{sys.version_info.minor}",
        "platform": platform.platform(),
        "wheels_count": len(wheel_files),
        "wheel_files": wheel_files,
        "missing_requirements": missing_requirements,
        "source_dist_only": source_dist_only,
        "incompatible_platform": [],
        "download_pass": ensure_pip.returncode == 0 and download_completed.returncode == 0 and not missing_requirements,
        "offline_install_proven": False,
        "wheelhouse_bundled": False,
        "committed_to_repo": False,
        "ensure_pip_stdout": ensure_pip.stdout.strip(),
        "ensure_pip_stderr": ensure_pip.stderr.strip(),
        "download_stdout": download_completed.stdout.strip(),
        "download_stderr": download_completed.stderr.strip(),
    }
    _write_json(manifest_path, report)
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["download_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
