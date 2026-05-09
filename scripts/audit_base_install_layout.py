from __future__ import annotations

import argparse
import json
from pathlib import Path


DEFAULT_LAYOUT_ROOT = Path(".tmp/base_install_layout/ZephyrBase")
FORBIDDEN_DIR_NAMES = {
    ".git",
    ".idea",
    "node_modules",
    "target",
    "base_runtime_wheelhouse",
}
ALLOWED_NEGATIVE = ("must not", "not ", "no ", "forbidden", "does not include", "cannot")
FORBIDDEN_TERMS = (
    "license_verify",
    "entitlement_server",
    "payment_callback",
    "billing_decision",
    "quota_authority",
    "risk_score",
    "web_core.internal",
    "private_core_export",
    "zephyr_pro",
)
TEXT_SUFFIXES = {".md", ".txt", ".json", ".py", ".toml", ".yml", ".yaml", ".html", ".js", ".css"}


def _write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _read_json(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Audit the Zephyr Base install layout first slice.")
    parser.add_argument("--layout-root", type=Path, default=DEFAULT_LAYOUT_ROOT)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)

    root = Path(__file__).resolve().parents[1]
    layout_root = args.layout_root if args.layout_root.is_absolute() else (root / args.layout_root).resolve()
    required = [
        layout_root / "app/ui/dist/index.html",
        layout_root / "app/tauri.conf.snapshot.json",
        layout_root / "app/capabilities/default.json",
        layout_root / "app/zephyr-base-app-placeholder.txt",
        layout_root / "public-core-bridge/run_public_core_adapter.py",
        layout_root / "runtime/public-core-bundle/run_bundle_public_core.py",
        layout_root / "runtime/python-runtime/runtime_manifest.json",
        layout_root / "checks/bootstrap_base_runtime.py",
        layout_root / "checks/check_python_runtime_dependencies.py",
        layout_root / "manifests/public_export_lineage.json",
        layout_root / "manifests/install_layout_manifest.json",
        layout_root / "docs/README.md",
        layout_root / "docs/NOTICE.md",
        layout_root / "docs/PRODUCT_BOUNDARY.md",
        layout_root / "docs/LICENSE",
    ]
    missing = [path.relative_to(layout_root).as_posix() for path in required if not path.exists()]

    forbidden_dirs: list[str] = []
    runtime_state_dirs: list[str] = []
    for path in layout_root.rglob("*"):
        rel = path.relative_to(layout_root).as_posix()
        if rel.startswith(".runtime/base_runtime_venv"):
            runtime_state_dirs.append(rel)
            continue
        if any(part in FORBIDDEN_DIR_NAMES for part in path.parts):
            forbidden_dirs.append(rel)
        if any(part.startswith("base_runtime_venv") for part in path.parts):
            forbidden_dirs.append(rel)

    leakage_hits: list[dict[str, object]] = []
    for path in layout_root.rglob("*"):
        if path.is_dir():
            continue
        if path.name == "LICENSE":
            continue
        if path.suffix.lower() not in TEXT_SUFFIXES:
            continue
        lowered = path.read_text(encoding="utf-8", errors="ignore").lower()
        rel = path.relative_to(layout_root).as_posix()
        for term in FORBIDDEN_TERMS:
            if term not in lowered:
                continue
            allowed_negative = rel == "docs/PRODUCT_BOUNDARY.md" and any(marker in lowered for marker in ALLOWED_NEGATIVE)
            if not allowed_negative:
                leakage_hits.append({"path": rel, "term": term})

    runtime_manifest = _read_json(layout_root / "runtime/python-runtime/runtime_manifest.json") if (layout_root / "runtime/python-runtime/runtime_manifest.json").exists() else {}
    report = {
        "schema_version": 1,
        "report_id": "zephyr.base.s12.install_layout_audit.v1",
        "summary": {
            "pass": not missing
            and not forbidden_dirs
            and not leakage_hits
            and runtime_manifest.get("installer_runtime_complete") is False
            and runtime_manifest.get("embedded_python_runtime") is False
            and runtime_manifest.get("managed_venv_supported") is True,
            "layout_root": str(layout_root),
            "ui_dist_exists": (layout_root / "app/ui/dist/index.html").exists(),
            "public_core_bundle_exists": (layout_root / "runtime/public-core-bundle/run_bundle_public_core.py").exists(),
            "bootstrap_script_exists": (layout_root / "checks/bootstrap_base_runtime.py").exists(),
            "forbidden_dirs_present": len(forbidden_dirs) > 0,
            "commercial_terms_blocked": len(leakage_hits),
        },
        "missing_files": missing,
        "forbidden_dirs": sorted(set(forbidden_dirs)),
        "runtime_state_dirs": sorted(set(runtime_state_dirs)),
        "leakage_hits": leakage_hits,
        "runtime_manifest_excerpt": runtime_manifest,
    }
    _write_json(root / ".tmp/base_install_layout_audit.json", report)
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["summary"]["pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
