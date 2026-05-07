from __future__ import annotations

import argparse
import json
from pathlib import Path

REQUIRED_FILES = [
    Path("docs/UI_ARTIFACT_CONSUMPTION.md"),
    Path("ui/package.json"),
    Path("ui/index.html"),
    Path("ui/src/main.tsx"),
    Path("ui/src/App.tsx"),
    Path("ui/src/contracts/baseRunResult.ts"),
    Path("ui/src/services/baseBridgeClient.ts"),
    Path("ui/src/services/mockArtifactClient.ts"),
    Path("ui/src/fixtures/sampleRunResult.ts"),
    Path("ui/src/fixtures/sampleErrorResult.ts"),
    Path("ui/src/components/Welcome.tsx"),
    Path("ui/src/components/FileDropZone.tsx"),
    Path("ui/src/components/TextInputPanel.tsx"),
    Path("ui/src/components/ProgressPanel.tsx"),
    Path("ui/src/components/ResultSummary.tsx"),
    Path("ui/src/components/NormalizedTextPreview.tsx"),
    Path("ui/src/components/EvidenceCard.tsx"),
    Path("ui/src/components/ReceiptCard.tsx"),
    Path("ui/src/components/UsageFactCard.tsx"),
    Path("ui/src/components/ErrorDiagnosisPanel.tsx"),
    Path("ui/src/components/LineageStatusCard.tsx"),
    Path("ui/src/components/OutputFolderPlan.tsx"),
    Path("ui/src/styles/tokens.css"),
]
FORBIDDEN_COMMERCIAL_TERMS = (
    "license_verify",
    "entitlement",
    "payment",
    "paid_user",
    "billing_decision",
    "quota_authority",
    "risk_score",
    "web_core",
    "zephyr_pro",
    "private_core",
)
FORBIDDEN_NETWORK_TERMS = ("fetch(", "axios", "xmlhttprequest", "websocket")
SUPPORTED_FORMATS = (".txt", ".text", ".log", ".md", ".markdown")
UNSUPPORTED_CLAIMS = (".pdf", ".docx", ".png", ".jpg", ".jpeg", ".csv", ".xlsx")


def _read_text(path: Path) -> str:
    raw = path.read_bytes()
    if raw.startswith(b"\xff\xfe") or raw.startswith(b"\xfe\xff"):
        return raw.decode("utf-16")
    if raw.startswith(b"\xef\xbb\xbf"):
        return raw.decode("utf-8-sig")
    return raw.decode("utf-8")


def _write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Check the Zephyr-base UI shell slice.")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)

    root = Path(__file__).resolve().parents[1]
    missing = [path.as_posix() for path in REQUIRED_FILES if not (root / path).exists()]
    ui_files = [path for path in (root / "ui/src").rglob("*") if path.is_file()]
    ui_text = "\n".join(_read_text(path).lower() for path in ui_files)
    forbidden_hits = [term for term in FORBIDDEN_COMMERCIAL_TERMS if term in ui_text]
    network_hits = [term for term in FORBIDDEN_NETWORK_TERMS if term in ui_text]
    sample_success_text = _read_text(root / "ui/src/fixtures/sampleRunResult.ts").lower()
    sample_error_text = _read_text(root / "ui/src/fixtures/sampleErrorResult.ts").lower()
    app_text = _read_text(root / "ui/src/App.tsx")
    format_hits = [fmt for fmt in SUPPORTED_FORMATS if fmt in app_text]
    unsupported_hits = [term for term in UNSUPPORTED_CLAIMS if term in ui_text]

    report = {
        "schema_version": 1,
        "report_id": "zephyr.base.s7.ui_shell_check.v1",
        "summary": {
            "pass": not missing and not forbidden_hits and not network_hits and not unsupported_hits,
            "required_files_exist": len(missing) == 0,
            "commercial_terms_blocked": len(forbidden_hits),
            "network_calls_blocked": len(network_hits),
            "supported_formats_limited_to_base_first_slice": len(format_hits) == len(SUPPORTED_FORMATS) and not unsupported_hits,
            "billing_semantics_false_present": "billing_semantics: false" in sample_success_text and "billing_semantics: false" in sample_error_text,
        },
        "missing_files": missing,
        "forbidden_hits": forbidden_hits,
        "network_hits": network_hits,
        "unsupported_hits": unsupported_hits,
        "supported_formats_detected": format_hits,
    }
    out_path = root / ".tmp" / "ui_shell_check.json"
    _write_json(out_path, report)
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["summary"]["pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
