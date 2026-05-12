from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path


DEFAULT_PACKAGE_ROOT = Path(".tmp/windows_installer_package")
PACKAGE_NAME = "ZephyrBase-windows-unsigned.zip"


def _write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _run(command: list[str], cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(command, cwd=cwd, check=False, capture_output=True, text=True)


def _copytree(src: Path, dst: Path) -> None:
    shutil.copytree(
        src,
        dst,
        dirs_exist_ok=True,
        ignore=shutil.ignore_patterns(
            ".git",
            ".idea",
            "node_modules",
            "target",
            "__pycache__",
            "*.pyc",
            "gen",
            ".runtime",
        ),
    )


def _git_head(root: Path) -> str:
    completed = _run(["git", "-c", f"safe.directory={root}", "-C", str(root), "rev-parse", "HEAD"], root)
    return completed.stdout.strip() if completed.returncode == 0 else "unknown"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build the S15 unsigned Windows installer package first slice.")
    parser.add_argument("--package-root", type=Path, default=DEFAULT_PACKAGE_ROOT)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)

    root = Path(__file__).resolve().parents[1]
    package_root = args.package_root if args.package_root.is_absolute() else (root / args.package_root).resolve()
    install_root = package_root / "ZephyrBase"
    zip_path = package_root / PACKAGE_NAME

    tauri_baseline = _run([sys.executable, str(root / "scripts/build_tauri_app_baseline.py"), "--json"], root)
    if tauri_baseline.returncode != 0:
        raise RuntimeError(tauri_baseline.stderr.strip() or "build_tauri_app_baseline.py failed")
    install_layout = _run([sys.executable, str(root / "scripts/build_base_install_layout.py"), "--json"], root)
    if install_layout.returncode != 0:
        raise RuntimeError(install_layout.stderr.strip() or "build_base_install_layout.py failed")
    wheelhouse = _run([sys.executable, str(root / "scripts/build_base_runtime_wheelhouse.py"), "--json"], root)
    if wheelhouse.returncode != 0:
        raise RuntimeError(wheelhouse.stderr.strip() or "build_base_runtime_wheelhouse.py failed")

    tauri_report = json.loads((root / ".tmp/tauri_app_build_baseline.json").read_text(encoding="utf-8"))
    release_binary = Path(str(tauri_report.get("release_binary_path", ""))) if tauri_report.get("release_binary_path") else None
    if release_binary is None or not release_binary.exists():
        raise FileNotFoundError("Tauri release binary is missing; cannot build S15 package")

    layout_root = root / ".tmp/base_install_layout/ZephyrBase"
    wheelhouse_root = root / ".tmp/base_runtime_wheelhouse"
    if package_root.exists():
        shutil.rmtree(package_root)
    package_root.mkdir(parents=True, exist_ok=True)

    _copytree(layout_root, install_root)
    _copytree(wheelhouse_root, install_root / "runtime/wheelhouse")
    (install_root / "app").mkdir(parents=True, exist_ok=True)
    (install_root / "checks").mkdir(parents=True, exist_ok=True)
    (install_root / "manifests").mkdir(parents=True, exist_ok=True)
    shutil.copy2(release_binary, install_root / "app" / release_binary.name)
    (install_root / "app" / "launch_zephyr_base.cmd").write_text(
        "@echo off\r\nstart \"Zephyr Base\" \"%~dp0\\"
        + release_binary.name
        + "\"\r\n",
        encoding="utf-8",
    )
    shutil.copy2(root / "scripts/run_windows_package_install_proof.py", install_root / "checks/run_windows_package_install_proof.py")
    shutil.copy2(root / "scripts/validate_windows_package_install_proof.py", install_root / "checks/validate_windows_package_install_proof.py")
    shutil.copy2(root / "scripts/run_offline_runtime_proof.py", install_root / "checks/run_offline_runtime_proof.py")
    shutil.copy2(root / "scripts/validate_offline_runtime_proof.py", install_root / "checks/validate_offline_runtime_proof.py")
    shutil.copy2(root / "scripts/marker_detection.py", install_root / "checks/marker_detection.py")
    shutil.copy2(root / "docs/WINDOWS_INSTALLER_PACKAGING_POLICY.md", install_root / "docs/WINDOWS_INSTALLER_PACKAGING_POLICY.md")
    shutil.copy2(root / "packaging/windows/README.md", install_root / "docs/WINDOWS_PACKAGING_README.md")

    lineage_path = install_root / "manifests/public_export_lineage.json"
    lineage = json.loads(lineage_path.read_text(encoding="utf-8"))
    source_sha = lineage.get("zephyr_dev_source_sha") or lineage.get("zephyr_dev_adapter_commit_sha") or "unknown"
    manifest = {
        "schema_version": 1,
        "report_id": "zephyr.base.s15.windows_installer_manifest.v1",
        "base_repo_sha": _git_head(root),
        "source_sha": source_sha,
        "package_kind": "portable_zip",
        "package_path": str(zip_path),
        "install_root": str(install_root),
        "ui_dist_present": (install_root / "app/ui/dist/index.html").exists(),
        "tauri_app_present": (install_root / "app" / release_binary.name).exists(),
        "public_core_bundle_present": (install_root / "runtime/public-core-bundle").exists(),
        "runtime_manifest_present": (install_root / "runtime/python-runtime/runtime_manifest.json").exists(),
        "wheelhouse_in_package": (install_root / "runtime/wheelhouse").exists(),
        "wheelhouse_committed_to_repo": False,
        "embedded_python_runtime": False,
        "installer_built": True,
        "signed_installer": False,
        "release_created": False,
        "install_smoke_pass": False,
        "installer_runtime_complete": "partial",
        "commercial_logic_allowed": False,
    }
    _write_json(package_root / "installer_manifest.json", manifest)
    _write_json(install_root / "manifests/installer_manifest.json", manifest)
    shutil.make_archive(str(zip_path.with_suffix("")), "zip", root_dir=package_root, base_dir="ZephyrBase")
    report = {
        "schema_version": 1,
        "report_id": "zephyr.base.s15.windows_installer_package_report.v1",
        "summary": {
            "pass": True,
            "package_kind": "portable_zip",
            "package_built": True,
            "tauri_app_present": manifest["tauri_app_present"],
            "wheelhouse_in_package": manifest["wheelhouse_in_package"],
        },
        "package_root": str(install_root),
        "package_path": str(zip_path),
        "release_binary": str(install_root / "app" / release_binary.name),
        "manifest": manifest,
    }
    _write_json(root / ".tmp/windows_installer_package_report.json", report)
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
