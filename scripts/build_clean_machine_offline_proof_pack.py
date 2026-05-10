from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path


DEFAULT_PACK_ROOT = Path(".tmp/clean_machine_offline_proof_pack")
DEFAULT_LAYOUT_ROOT = Path(".tmp/base_install_layout/ZephyrBase")
DEFAULT_WHEELHOUSE_ROOT = Path(".tmp/base_runtime_wheelhouse")
ZIP_NAME = "ZephyrBase-offline-runtime-proof.zip"


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


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build the local offline runtime proof pack.")
    parser.add_argument("--pack-root", type=Path, default=DEFAULT_PACK_ROOT)
    parser.add_argument("--layout-root", type=Path, default=DEFAULT_LAYOUT_ROOT)
    parser.add_argument("--wheelhouse-root", type=Path, default=DEFAULT_WHEELHOUSE_ROOT)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)

    root = Path(__file__).resolve().parents[1]
    ui_dist = root / "ui/dist"
    if not ui_dist.exists():
        raise FileNotFoundError("ui/dist is missing; run npm --prefix ui run build first")

    build_layout = _run(
        [sys.executable, str(root / "scripts/build_base_install_layout.py"), "--layout-root", str(args.layout_root), "--json"],
        root,
    )
    if build_layout.returncode != 0:
        raise RuntimeError(build_layout.stderr.strip() or "build_base_install_layout.py failed")

    build_wheelhouse = _run(
        [sys.executable, str(root / "scripts/build_base_runtime_wheelhouse.py"), "--json"],
        root,
    )
    if build_wheelhouse.returncode != 0:
        raise RuntimeError(build_wheelhouse.stderr.strip() or "build_base_runtime_wheelhouse.py failed")

    layout_root = args.layout_root if args.layout_root.is_absolute() else (root / args.layout_root).resolve()
    wheelhouse_root = args.wheelhouse_root if args.wheelhouse_root.is_absolute() else (root / args.wheelhouse_root).resolve()
    pack_root = args.pack_root if args.pack_root.is_absolute() else (root / args.pack_root).resolve()
    proof_layout_root = pack_root / "ZephyrBase"
    zip_path = pack_root / ZIP_NAME

    if pack_root.exists():
        shutil.rmtree(pack_root)
    pack_root.mkdir(parents=True, exist_ok=True)

    _copytree(layout_root, proof_layout_root)
    _copytree(wheelhouse_root, proof_layout_root / "runtime/wheelhouse")
    (proof_layout_root / "checks").mkdir(parents=True, exist_ok=True)
    (proof_layout_root / "proof").mkdir(parents=True, exist_ok=True)
    shutil.copy2(root / "scripts/run_offline_runtime_proof.py", proof_layout_root / "checks/run_offline_runtime_proof.py")
    shutil.copy2(root / "scripts/validate_offline_runtime_proof.py", proof_layout_root / "checks/validate_offline_runtime_proof.py")
    (proof_layout_root / "OFFLINE_RUNTIME_README.md").write_text(
        "Run `python checks/run_offline_runtime_proof.py --json` and then `python checks/validate_offline_runtime_proof.py --json` from this directory.\n",
        encoding="utf-8",
    )

    shutil.make_archive(str(zip_path.with_suffix("")), "zip", root_dir=pack_root, base_dir="ZephyrBase")
    manifest = {
        "schema_version": 1,
        "report_id": "zephyr.base.s14.offline_proof_pack_manifest.v1",
        "base_repo_sha": subprocess.run(
            ["git", "-c", f"safe.directory={root}", "-C", str(root), "rev-parse", "HEAD"],
            check=False,
            capture_output=True,
            text=True,
        ).stdout.strip() or "unknown",
        "pack_root": str(proof_layout_root),
        "zip_path": str(zip_path),
        "installer_built": False,
        "release_created": False,
        "embedded_python_runtime": False,
        "wheelhouse_bundled": True,
        "wheelhouse_committed": False,
        "offline_runtime_install_proven": False,
        "proof_level": "local_offline_pack",
        "requires_python_on_clean_machine": True,
        "requires_network_for_bootstrap": False,
        "requires_git": False,
        "requires_node": False,
        "requires_rust": False,
        "requires_zephyr_dev": False,
        "requires_zephyr_base_repo": False,
    }
    _write_json(pack_root / "offline_proof_pack_manifest.json", manifest)
    if args.json:
        print(json.dumps(manifest, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
