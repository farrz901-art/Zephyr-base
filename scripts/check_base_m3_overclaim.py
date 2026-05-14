from __future__ import annotations

import argparse
import json
from pathlib import Path


SUPPORTED_FORMATS = (".txt", ".text", ".log", ".md", ".markdown")
REQUIRED_DOCS = (
    Path("docs/BASE_MVP_PRODUCT_TRUTH.md"),
    Path("docs/BASE_M3_READINESS_REPORT.md"),
    Path("docs/BASE_M3_DISTRIBUTION_DECISION.md"),
    Path("docs/BASE_M3_EVIDENCE_MATRIX.md"),
    Path("manifests/base_m3_evidence_matrix.json"),
)
REQUIRED_NEGATIVE_DOC_MARKERS = (
    "does not expose html",
    "unsigned portable zip preview package",
    "signed_installer=false",
    "official_release=false",
    "auto_update=false",
)
POSITIVE_PROHIBITED_PATTERNS = {
    "pdf_claimed": ("supports pdf", "pdf upload", "pdf processing"),
    "docx_claimed": ("supports docx", "docx upload", "docx processing"),
    "image_or_ocr_claimed": ("image upload", "ocr processing", "supports image"),
    "html_claimed": ("supports html", "html upload", "html processing"),
    "cloud_claimed": ("cloud processing", "online processing", "web api"),
    "pro_claimed": ("pro feature", "zephyr pro", "upgrade to pro"),
    "license_or_entitlement_claimed": ("license key", "entitlement flow", "account license"),
    "payment_or_billing_claimed": ("billing plan", "payment required", "subscription required", "quota plan"),
    "signed_installer_claimed": ("signed installer available", "official signed installer"),
    "official_release_claimed": ("official release now available", "production release download"),
    "auto_update_claimed": ("auto update available", "automatic updates"),
    "embedded_python_claimed": ("embedded python runtime",),
    "wheel_only_claimed": ("wheel-only proof complete", "only-binary proof complete"),
}


def _write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _read_json(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Check Base M3 overclaim boundaries.")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)

    root = Path(__file__).resolve().parents[1]
    missing = [path.as_posix() for path in REQUIRED_DOCS if not (root / path).exists()]

    documents_text = "\n".join(
        (root / path).read_text(encoding="utf-8", errors="ignore").lower()
        for path in REQUIRED_DOCS
        if (root / path).exists()
    )
    readme_path = root / "README.md"
    readme_text = readme_path.read_text(encoding="utf-8", errors="ignore").lower() if readme_path.exists() else ""
    ui_text = "\n".join(
        path.read_text(encoding="utf-8", errors="ignore").lower()
        for path in (root / "ui/src").rglob("*")
        if path.is_file()
    )
    positive_claim_corpus = readme_text + "\n" + ui_text

    findings = {
        key: any(pattern in positive_claim_corpus for pattern in patterns)
        for key, patterns in POSITIVE_PROHIBITED_PATTERNS.items()
    }

    package_report = _read_json(root / ".tmp/windows_installer_package_report.json")
    package_summary = package_report.get("summary", {})
    package_manifest = package_report.get("manifest", {})
    wheelhouse = _read_json(root / ".tmp/wheelhouse_wheel_only_readiness.json")

    supported_formats_truth = all(fmt in documents_text for fmt in SUPPORTED_FORMATS)
    negative_doc_markers_present = all(marker in documents_text for marker in REQUIRED_NEGATIVE_DOC_MARKERS)
    portable_zip = package_summary.get("package_kind") == "portable_zip" and package_manifest.get("package_kind") == "portable_zip"
    runtime_capability_changed = False
    private_core_allowed = False
    web_core_dependency_allowed = False
    secrets_printed = False
    no_network_runtime_claim = "network runtime required" not in positive_claim_corpus

    report = {
        "schema_version": 1,
        "report_id": "zephyr.base.s18.base_m3_overclaim_check.v1",
        "summary": {
            "pass": not missing
            and not any(findings.values())
            and supported_formats_truth
            and negative_doc_markers_present
            and portable_zip
            and runtime_capability_changed is False
            and private_core_allowed is False
            and web_core_dependency_allowed is False
            and secrets_printed is False
            and no_network_runtime_claim,
            "supported_formats_truthful": supported_formats_truth,
            "negative_doc_markers_present": negative_doc_markers_present,
            "package_kind": package_manifest.get("package_kind"),
            "wheel_only_ready": wheelhouse.get("wheel_only_ready"),
        },
        "missing_files": missing,
        "findings": findings,
        "scope": {
            "signed_installer": package_manifest.get("signed_installer"),
            "official_release": False,
            "release_created": package_manifest.get("release_created"),
            "auto_update": False,
            "embedded_python_runtime": package_manifest.get("embedded_python_runtime"),
            "runtime_capability_changed": runtime_capability_changed,
        },
        "boundary": {
            "private_core_allowed": private_core_allowed,
            "web_core_dependency_allowed": web_core_dependency_allowed,
            "secrets_printed": secrets_printed,
        },
    }

    out = root / ".tmp/base_m3_overclaim_check.json"
    _write_json(out, report)
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["summary"]["pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
