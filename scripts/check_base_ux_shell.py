from __future__ import annotations

import argparse
import json
from pathlib import Path

REQUIRED_FILES = [
    Path("docs/BASE_USER_EXPERIENCE_POLICY.md"),
    Path("docs/BASE_BILINGUAL_UI_BRIEF.md"),
    Path("docs/MANUAL_BASE_UX_SMOKE.md"),
    Path("ui/src/i18n/messages.ts"),
    Path("ui/src/i18n/useLanguage.tsx"),
    Path("ui/src/components/common/LanguageToggle.tsx"),
    Path("ui/src/components/layout/AppShell.tsx"),
    Path("ui/src/components/input/InputCard.tsx"),
    Path("ui/src/components/run/RunCard.tsx"),
    Path("ui/src/components/results/UserResultCard.tsx"),
    Path("ui/src/components/diagnostics/AdvancedDiagnostics.tsx"),
]
REQUIRED_MESSAGE_MARKERS = (
    "title",
    "subtitle",
    "primary",
    "readLatest",
    "proofExport",
    "sampleSuccess",
    "sampleError",
)
SUPPORTED_FORMATS = (".txt", ".text", ".log", ".md", ".markdown")


def _write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Check the Base bilingual UX shell.")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)

    root = Path(__file__).resolve().parents[1]
    missing = [path.as_posix() for path in REQUIRED_FILES if not (root / path).exists()]
    messages_text = (root / "ui/src/i18n/messages.ts").read_text(encoding="utf-8", errors="ignore")
    app_text = (root / "ui/src/App.tsx").read_text(encoding="utf-8", errors="ignore").lower()
    advanced_text = (
        root / "ui/src/components/diagnostics/AdvancedDiagnostics.tsx"
    ).read_text(encoding="utf-8", errors="ignore").lower()
    ui_text = "\n".join(
        path.read_text(encoding="utf-8", errors="ignore").lower()
        for path in (root / "ui/src").rglob("*")
        if path.is_file()
    )

    english_supported = "en:" in messages_text or "en =" in messages_text
    chinese_supported = "zh:" in messages_text or "zh =" in messages_text
    language_toggle_present = "languagetoggle" in ui_text
    primary_run_button_present = "m.run.primary" in ui_text or "run primary" in messages_text.lower()
    advanced_diagnostics_collapsed_by_default = "<details" in advanced_text and " open" not in advanced_text
    sample_mode_demoted = "sample success" not in app_text and "samplesuccess" in advanced_text and "sampleerror" in advanced_text
    proof_export_demoted = "export interaction proof" not in app_text and "InteractionProofPanel" in (root / "ui/src/components/diagnostics/AdvancedDiagnostics.tsx").read_text(encoding="utf-8", errors="ignore")
    lineage_demoted = "lineagestatuscard" not in app_text and "lineagestatuscard" in advanced_text
    user_friendly_runtime_copy = all(
        marker in messages_text
        for marker in (
            "Free local processing. No billing record is created.",
            "Using the packaged local runtime.",
            "No developer workspace required.",
            "Runs without network access.",
        )
    )
    supported_formats_truthful = all(fmt in ui_text for fmt in SUPPORTED_FORMATS)
    unsupported_claims = any(term in ui_text for term in ("pdf support", "docx support", "ocr support", "image support"))
    commercial_claims = any(term in ui_text for term in ("billing plan", "payment plan", "entitlement flow", "license portal", "quota"))
    network_claims = any(term in ui_text for term in ("cloud processing", "web api", "online sync"))
    message_markers_present = all(marker in messages_text for marker in REQUIRED_MESSAGE_MARKERS)

    report = {
        "schema_version": 1,
        "report_id": "zephyr.base.s16.base_ux_shell_check.v1",
        "summary": {
            "pass": not missing
            and english_supported
            and chinese_supported
            and language_toggle_present
            and primary_run_button_present
            and advanced_diagnostics_collapsed_by_default
            and sample_mode_demoted
            and proof_export_demoted
            and lineage_demoted
            and user_friendly_runtime_copy
            and supported_formats_truthful
            and not unsupported_claims
            and not commercial_claims
            and not network_claims
            and message_markers_present,
            "bilingual_ui": english_supported and chinese_supported,
            "english_supported": english_supported,
            "chinese_supported": chinese_supported,
            "language_toggle_present": language_toggle_present,
            "primary_run_button_present": primary_run_button_present,
            "advanced_diagnostics_collapsed_by_default": advanced_diagnostics_collapsed_by_default,
            "sample_mode_demoted": sample_mode_demoted,
            "proof_export_demoted": proof_export_demoted,
            "lineage_demoted": lineage_demoted,
            "user_friendly_runtime_copy": user_friendly_runtime_copy,
            "supported_formats_truthful": supported_formats_truthful,
        },
        "missing_files": missing,
    }
    _write_json(root / ".tmp/base_ux_shell_check.json", report)
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["summary"]["pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
