from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
from datetime import UTC, datetime
from pathlib import Path


DEFAULT_LAYOUT_ROOT = Path(".tmp/base_install_layout/ZephyrBase")


def _write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _copytree(src: Path, dst: Path) -> None:
    shutil.copytree(
        src,
        dst,
        dirs_exist_ok=True,
        ignore=shutil.ignore_patterns(
            "__pycache__",
            ".git",
            ".idea",
            "node_modules",
            "target",
            "*.pyc",
        ),
    )


def _git_head(root: Path) -> str:
    completed = subprocess.run(
        ["git", "-c", f"safe.directory={root}", "-C", str(root), "rev-parse", "HEAD"],
        check=False,
        capture_output=True,
        text=True,
    )
    return completed.stdout.strip() if completed.returncode == 0 else "unknown"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build the Zephyr Base install layout first slice.")
    parser.add_argument("--layout-root", type=Path, default=DEFAULT_LAYOUT_ROOT)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)

    root = Path(__file__).resolve().parents[1]
    layout_root = args.layout_root if args.layout_root.is_absolute() else (root / args.layout_root).resolve()
    ui_dist = root / "ui/dist"
    if not ui_dist.exists():
        raise FileNotFoundError("ui/dist is missing; run npm --prefix ui run build first")

    if layout_root.exists():
        shutil.rmtree(layout_root)

    app_root = layout_root / "app"
    runtime_root = layout_root / "runtime"
    manifests_root = layout_root / "manifests"
    docs_root = layout_root / "docs"
    checks_root = layout_root / "checks"

    (app_root / "capabilities").mkdir(parents=True, exist_ok=True)
    manifests_root.mkdir(parents=True, exist_ok=True)
    docs_root.mkdir(parents=True, exist_ok=True)
    checks_root.mkdir(parents=True, exist_ok=True)

    _copytree(root / "ui/dist", app_root / "ui/dist")
    _copytree(root / "public-core-bridge", layout_root / "public-core-bridge")
    _copytree(root / "runtime/public-core-bundle", runtime_root / "public-core-bundle")
    _copytree(root / "runtime/python-runtime", runtime_root / "python-runtime")

    shutil.copy2(root / "manifests/public_export_lineage.json", manifests_root / "public_export_lineage.json")
    shutil.copy2(root / "src-tauri/tauri.conf.json", app_root / "tauri.conf.snapshot.json")
    shutil.copy2(root / "src-tauri/capabilities/default.json", app_root / "capabilities/default.json")
    shutil.copy2(root / "README.md", docs_root / "README.md")
    shutil.copy2(root / "NOTICE.md", docs_root / "NOTICE.md")
    shutil.copy2(root / "PRODUCT_BOUNDARY.md", docs_root / "PRODUCT_BOUNDARY.md")
    shutil.copy2(root / "LICENSE", docs_root / "LICENSE")
    shutil.copy2(root / "docs/PACKAGED_RUNTIME_BASELINE.md", docs_root / "PACKAGED_RUNTIME_BASELINE.md")
    shutil.copy2(root / "docs/BASE_LOCAL_APP_FLOW.md", docs_root / "BASE_LOCAL_APP_FLOW.md")
    shutil.copy2(root / "scripts/bootstrap_base_runtime.py", checks_root / "bootstrap_base_runtime.py")
    shutil.copy2(root / "scripts/check_python_runtime_dependencies.py", checks_root / "check_python_runtime_dependencies.py")
    shutil.copy2(root / "scripts/check_managed_runtime_flow.py", checks_root / "check_managed_runtime_flow.py")

    (app_root / "zephyr-base-app-placeholder.txt").write_text(
        "Visible app executable is not bundled in S12. This layout is an installer precursor with UI dist and runtime assets only.\n",
        encoding="utf-8",
    )

    lineage_path = manifests_root / "public_export_lineage.json"
    bundle_manifest_path = runtime_root / "public-core-bundle/manifest/public_core_bundle_manifest.json"
    runtime_manifest_path = runtime_root / "python-runtime/runtime_manifest.json"
    lineage = json.loads(lineage_path.read_text(encoding="utf-8"))
    source_sha = (
        lineage.get("zephyr_dev_source_sha")
        or lineage.get("zephyr_dev_adapter_commit_sha")
        or "unknown"
    )
    manifest = {
        "schema_version": 1,
        "report_id": "zephyr.base.s12.install_layout_manifest.v1",
        "generated_at_utc": datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "source_sha": source_sha,
        "base_repo_sha": _git_head(root),
        "public_manifest_hash": _sha256(lineage_path),
        "bundle_manifest_hash": _sha256(bundle_manifest_path),
        "runtime_manifest_hash": _sha256(runtime_manifest_path),
        "ui_dist_present": True,
        "public_core_bundle_present": True,
        "runtime_bootstrap_present": True,
        "managed_runtime_supported": True,
        "installer_built": False,
        "release_created": False,
        "embedded_python_runtime": False,
        "wheelhouse_bundled": False,
        "clean_machine_runtime_proven": False,
        "commercial_logic_allowed": False,
    }
    _write_json(manifests_root / "install_layout_manifest.json", manifest)

    report = {
        "schema_version": 1,
        "report_id": "zephyr.base.s12.build_install_layout.v1",
        "summary": {
            "pass": True,
            "layout_root": str(layout_root),
            "ui_dist_present": True,
            "public_core_bundle_present": True,
            "runtime_bootstrap_present": True,
        },
        "layout_root": str(layout_root),
        "manifest": manifest,
    }
    _write_json(root / ".tmp/base_install_layout_build.json", report)
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
