from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path


DEFAULT_PACK_ROOT = Path(".tmp/clean_machine_proof_pack")
DEFAULT_LAYOUT_ROOT = Path(".tmp/base_install_layout/ZephyrBase")
ZIP_NAME = "ZephyrBase-clean-machine-proof.zip"
PROOF_TEMPLATE = {
    "schema_version": 1,
    "report_id": "zephyr.base.s13.clean_machine_runtime_proof.v1",
    "proof_level": "L1",
    "machine": {
        "os": "",
        "python": "",
        "node_available": False,
        "cargo_available": False,
        "git_available": False,
    },
    "runtime": {
        "managed_python": "",
        "managed_runtime_created": False,
        "uses_current_shell_python_for_execution": False,
        "embedded_python_runtime": False,
        "wheelhouse_bundled": False,
        "installer_runtime_complete": False,
    },
    "text_flow": {
        "pass": False,
        "run_result_exists": False,
        "marker_found": False,
        "billing_semantics": False,
        "bundled_runtime_used": False,
        "fixture_runner_used": False,
        "zephyr_dev_working_tree_required": False,
        "requires_network": False,
        "requires_p45_substrate": False,
    },
    "file_flow": {
        "pass": False,
        "run_result_exists": False,
        "marker_found": False,
        "billing_semantics": False,
        "bundled_runtime_used": False,
        "fixture_runner_used": False,
        "zephyr_dev_working_tree_required": False,
        "requires_network": False,
        "requires_p45_substrate": False,
    },
    "scope": {
        "installer_built": False,
        "release_created": False,
        "clean_machine_runtime_proven": False,
        "clean_machine_installer_proven": False,
    },
}


def _write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _git_head(root: Path) -> str:
    completed = subprocess.run(
        ["git", "-c", f"safe.directory={root}", "-C", str(root), "rev-parse", "HEAD"],
        check=False,
        capture_output=True,
        text=True,
    )
    return completed.stdout.strip() if completed.returncode == 0 else "unknown"


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
            ".runtime",
            "gen",
        ),
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build the Zephyr Base clean-machine proof pack.")
    parser.add_argument("--pack-root", type=Path, default=DEFAULT_PACK_ROOT)
    parser.add_argument("--layout-root", type=Path, default=DEFAULT_LAYOUT_ROOT)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)

    root = Path(__file__).resolve().parents[1]
    ui_dist = root / "ui/dist"
    if not ui_dist.exists():
        raise FileNotFoundError("ui/dist is missing; run npm --prefix ui run build first")

    subprocess.run(
        [sys.executable, str(root / "scripts/build_base_install_layout.py"), "--layout-root", str(args.layout_root), "--json"],
        cwd=root,
        check=True,
    )

    layout_root = args.layout_root if args.layout_root.is_absolute() else (root / args.layout_root).resolve()
    pack_root = args.pack_root if args.pack_root.is_absolute() else (root / args.pack_root).resolve()
    proof_layout_root = pack_root / "ZephyrBase"
    zip_path = pack_root / ZIP_NAME
    if pack_root.exists():
        shutil.rmtree(pack_root)
    pack_root.mkdir(parents=True, exist_ok=True)

    _copytree(layout_root, proof_layout_root)
    (proof_layout_root / "checks").mkdir(parents=True, exist_ok=True)
    (proof_layout_root / "proof").mkdir(parents=True, exist_ok=True)

    shutil.copy2(root / "scripts/run_clean_machine_runtime_proof.py", proof_layout_root / "checks/run_clean_machine_runtime_proof.py")
    shutil.copy2(root / "scripts/validate_clean_machine_runtime_proof.py", proof_layout_root / "checks/validate_clean_machine_runtime_proof.py")
    (proof_layout_root / "CLEAN_MACHINE_README.md").write_text(
        "Run `python checks/run_clean_machine_runtime_proof.py --json` and then `python checks/validate_clean_machine_runtime_proof.py --json` from this directory.\n",
        encoding="utf-8",
    )
    _write_json(proof_layout_root / "proof/clean_machine_runtime_proof.template.json", PROOF_TEMPLATE)

    shutil.make_archive(str(zip_path.with_suffix("")), "zip", root_dir=pack_root, base_dir="ZephyrBase")

    lineage_path = proof_layout_root / "manifests/public_export_lineage.json"
    source_sha = "unknown"
    if lineage_path.exists():
        lineage = json.loads(lineage_path.read_text(encoding="utf-8"))
        source_sha = lineage.get("zephyr_dev_source_sha") or lineage.get("zephyr_dev_adapter_commit_sha") or "unknown"
    manifest = {
        "schema_version": 1,
        "report_id": "zephyr.base.s13.clean_machine_proof_pack_manifest.v1",
        "base_repo_sha": _git_head(root),
        "source_sha": source_sha,
        "pack_root": str(proof_layout_root),
        "zip_path": str(zip_path),
        "installer_built": False,
        "release_created": False,
        "embedded_python_runtime": False,
        "wheelhouse_bundled": False,
        "clean_machine_runtime_proven": False,
        "proof_level": "L1",
        "requires_python_on_clean_machine": True,
        "requires_network_for_bootstrap": True,
        "requires_git": False,
        "requires_node": False,
        "requires_rust": False,
        "requires_zephyr_dev": False,
        "requires_zephyr_base_repo": False,
    }
    _write_json(pack_root / "clean_machine_proof_pack_manifest.json", manifest)
    if args.json:
        print(json.dumps(manifest, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
