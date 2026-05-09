from __future__ import annotations

import argparse
import json
from pathlib import Path

REQUIRED_FILES = [
    Path("ui/src/components/RunModePanel.tsx"),
    Path("ui/src/components/RunStatusTimeline.tsx"),
    Path("ui/src/components/RuntimePreflightCard.tsx"),
    Path("ui/src/components/InteractionProofPanel.tsx"),
    Path("ui/src/components/LocalOutputControls.tsx"),
    Path("ui/src/components/SupportedFormatsNotice.tsx"),
    Path("scripts/check_tauri_window_interaction_proof.py"),
    Path("scripts/check_tauri_invoke_payload_shape.py"),
    Path("scripts/check_python_runtime_dependencies.py"),
    Path("docs/MANUAL_TAURI_WINDOW_PROOF.md"),
]
REAL_MODE_LABELS = (
    "real tauri local text",
    "real tauri local file",
    "run local text",
    "run local file path",
)
LIFECYCLE_TERMS = (
    "preparing request",
    "invoking tauri command",
    "processing local runtime",
    "reading result",
)
FORBIDDEN_TERMS = (
    "license_verify",
    "entitlement",
    "payment",
    "billing_decision",
    "quota_authority",
    "risk_score",
    "web_core",
    "zephyr_pro",
)
NETWORK_TERMS = ("fetch(", "axios", "xmlhttprequest", "websocket")


def _write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Check the local result lifecycle UX shell.")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)

    root = Path(__file__).resolve().parents[1]
    missing = [path.as_posix() for path in REQUIRED_FILES if not (root / path).exists()]
    ui_text = "\n".join(
        path.read_text(encoding="utf-8", errors="ignore").lower()
        for path in (root / "ui/src").rglob("*")
        if path.is_file()
    )
    app_text = (root / "ui/src/App.tsx").read_text(encoding="utf-8", errors="ignore").lower()
    bridge_client_text = (root / "ui/src/services/baseBridgeClient.ts").read_text(
        encoding="utf-8",
        errors="ignore",
    )
    forbidden_hits = [term for term in FORBIDDEN_TERMS if term in ui_text]
    network_hits = [term for term in NETWORK_TERMS if term in ui_text]

    report = {
        "schema_version": 1,
        "report_id": "zephyr.base.s10.local_result_lifecycle_ux_check.v1",
        "summary": {
            "pass": not missing
            and not forbidden_hits
            and not network_hits
            and all(label in ui_text for label in REAL_MODE_LABELS)
            and all(term in ui_text for term in LIFECYCLE_TERMS)
            and "export interaction proof" in ui_text
            and "installer runtime complete=false" in app_text
            and all(token in bridge_client_text for token in ("inputPath", "outputDir", "inlineText", "runResult")),
            "real_run_mode_exists": all(label in ui_text for label in REAL_MODE_LABELS),
            "sample_mode_retained": "sample success" in ui_text and "sample error" in ui_text,
            "run_status_timeline_exists": "runstatustimeline" in ui_text,
            "runtime_preflight_card_exists": "runtimepreflightcard" in ui_text,
            "supported_formats_notice_exists": "supportedformatsnotice" in ui_text,
            "interaction_proof_panel_exists": "interactionproofpanel" in ui_text,
            "commercial_terms_blocked": len(forbidden_hits),
            "network_calls_blocked": len(network_hits),
        },
        "missing_files": missing,
        "forbidden_hits": forbidden_hits,
        "network_hits": network_hits,
    }
    out_path = root / ".tmp" / "local_result_lifecycle_ux_check.json"
    _write_json(out_path, report)
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["summary"]["pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
