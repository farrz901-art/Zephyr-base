from __future__ import annotations

import argparse
import json
from pathlib import Path


DEFAULT_PACK_ROOT = Path(".tmp/clean_machine_proof_pack/ZephyrBase")
PACK_MANIFEST = Path(".tmp/clean_machine_proof_pack/clean_machine_proof_pack_manifest.json")
ZIP_PATH = Path(".tmp/clean_machine_proof_pack/ZephyrBase-clean-machine-proof.zip")
FORBIDDEN_PATH_MARKERS = (
    "E:\\Github_Projects\\Zephyr-base",
    "E:\\Github_Projects\\Zephyr",
    "/home/runner/work/Zephyr-base",
)
FORBIDDEN_DIRS = {".git", ".idea", "node_modules", "target", "gen"}
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
ALLOWED_NEGATIVE = ("must not", "not ", "no ", "forbidden", "does not include", "cannot")
TEXT_SUFFIXES = {".md", ".txt", ".json", ".py", ".toml", ".yml", ".yaml", ".html", ".js", ".css"}


def _write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Audit the clean-machine proof pack for relocation safety.")
    parser.add_argument("--pack-root", type=Path, default=DEFAULT_PACK_ROOT)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)

    root = Path(__file__).resolve().parents[1]
    pack_root = args.pack_root if args.pack_root.is_absolute() else (root / args.pack_root).resolve()
    manifest_path = root / PACK_MANIFEST
    zip_path = root / ZIP_PATH

    forbidden_paths: list[str] = []
    forbidden_terms: list[dict[str, str]] = []
    forbidden_dirs: list[str] = []
    for path in pack_root.rglob("*"):
        rel = path.relative_to(pack_root).as_posix()
        if any(part in FORBIDDEN_DIRS for part in path.parts) or "base_runtime_venv" in rel or "base_runtime_wheelhouse" in rel:
            forbidden_dirs.append(rel)
        if path.is_dir():
            continue
        text = path.read_text(encoding="utf-8", errors="ignore") if path.suffix.lower() in TEXT_SUFFIXES else ""
        for marker in FORBIDDEN_PATH_MARKERS:
            if marker in text:
                forbidden_paths.append(rel)
        lowered = text.lower()
        for term in FORBIDDEN_TERMS:
            if term in lowered:
                allowed_negative = rel == "docs/PRODUCT_BOUNDARY.md" and any(marker in lowered for marker in ALLOWED_NEGATIVE)
                if not allowed_negative:
                    forbidden_terms.append({"path": rel, "term": term})

    runner_path = pack_root / "checks/run_clean_machine_runtime_proof.py"
    validator_path = pack_root / "checks/validate_clean_machine_runtime_proof.py"
    layout_manifest_path = pack_root / "manifests/install_layout_manifest.json"
    layout_manifest = json.loads(layout_manifest_path.read_text(encoding="utf-8")) if layout_manifest_path.exists() else {}
    runner_text = runner_path.read_text(encoding="utf-8") if runner_path.exists() else ""
    validator_text = validator_path.read_text(encoding="utf-8") if validator_path.exists() else ""

    report = {
        "schema_version": 1,
        "report_id": "zephyr.base.s13.clean_machine_pack_relocation_audit.v1",
        "summary": {
            "pass": pack_root.exists()
            and manifest_path.exists()
            and zip_path.exists()
            and not forbidden_paths
            and not forbidden_terms
            and not forbidden_dirs
            and "Path(__file__).resolve().parents[1]" in runner_text
            and "Path(__file__).resolve().parents[1]" in validator_text
            and (pack_root / "proof/clean_machine_runtime_proof.template.json").exists()
            and layout_manifest.get("clean_machine_runtime_proven") is False,
            "zip_exists": zip_path.exists(),
            "proof_template_exists": (pack_root / "proof/clean_machine_runtime_proof.template.json").exists(),
            "layout_relative_runner": "Path(__file__).resolve().parents[1]" in runner_text,
            "layout_relative_validator": "Path(__file__).resolve().parents[1]" in validator_text,
        },
        "forbidden_path_hits": forbidden_paths,
        "forbidden_term_hits": forbidden_terms,
        "forbidden_dirs": sorted(set(forbidden_dirs)),
    }
    _write_json(root / ".tmp/clean_machine_pack_relocation_audit.json", report)
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["summary"]["pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
