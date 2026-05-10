from __future__ import annotations

import argparse
import json
from pathlib import Path

REQUIRED_FILES = [
    Path("docs/UI_ARTIFACT_CONSUMPTION.md"),
    Path("docs/UI_TAURI_INVOKE_INTEGRATION.md"),
    Path("docs/BASE_LOCAL_APP_FLOW.md"),
    Path("docs/TAURI_WINDOW_INTERACTION_PROOF.md"),
    Path("docs/MANUAL_TAURI_WINDOW_PROOF.md"),
    Path("docs/PACKAGED_RUNTIME_BASELINE.md"),
    Path("docs/TAURI_GENERATED_ARTIFACTS.md"),
    Path("docs/BASE_INSTALL_LAYOUT_POLICY.md"),
    Path("docs/CLEAN_MACHINE_RUNTIME_PROOF_PLAN.md"),
    Path("docs/BASE_USER_EXPERIENCE_POLICY.md"),
    Path("docs/BASE_BILINGUAL_UI_BRIEF.md"),
    Path("docs/MANUAL_BASE_UX_SMOKE.md"),
    Path("ui/package.json"),
    Path("ui/tsconfig.json"),
    Path("ui/vite.config.ts"),
    Path("ui/index.html"),
    Path("ui/src/main.tsx"),
    Path("ui/src/App.tsx"),
    Path("ui/src/i18n/messages.ts"),
    Path("ui/src/i18n/useLanguage.tsx"),
    Path("ui/src/contracts/baseRunResult.ts"),
    Path("ui/src/services/baseBridgeClient.ts"),
    Path("ui/src/services/mockArtifactClient.ts"),
    Path("ui/src/fixtures/sampleRunResult.ts"),
    Path("ui/src/fixtures/sampleErrorResult.ts"),
    Path("ui/src/components/common/LanguageToggle.tsx"),
    Path("ui/src/components/layout/AppShell.tsx"),
    Path("ui/src/components/input/InputCard.tsx"),
    Path("ui/src/components/run/RunCard.tsx"),
    Path("ui/src/components/results/UserResultCard.tsx"),
    Path("ui/src/components/diagnostics/AdvancedDiagnostics.tsx"),
    Path("scripts/check_ui_result_lifecycle.py"),
    Path("scripts/check_ui_build.py"),
    Path("scripts/check_tauri_app_path.py"),
    Path("scripts/check_local_result_lifecycle_ux.py"),
    Path("scripts/check_tauri_window_interaction_proof.py"),
    Path("scripts/check_tauri_invoke_payload_shape.py"),
    Path("scripts/check_python_runtime_dependencies.py"),
    Path("scripts/check_runtime_packaging_baseline.py"),
    Path("scripts/check_managed_runtime_flow.py"),
    Path("scripts/bootstrap_base_runtime.py"),
    Path("scripts/check_generated_artifact_hygiene.py"),
    Path("scripts/build_base_install_layout.py"),
    Path("scripts/audit_base_install_layout.py"),
    Path("scripts/check_base_install_layout_runtime_smoke.py"),
    Path("scripts/check_install_layout_baseline.py"),
    Path("scripts/check_base_ux_shell.py"),
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
COMMAND_NAMES = (
    "run_local_file",
    "run_local_text",
    "read_run_result",
    "open_output_folder_plan",
    "read_lineage_snapshot",
)


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
    app_text = _read_text(root / "ui/src/App.tsx").lower()
    bridge_client_text = _read_text(root / "ui/src/services/baseBridgeClient.ts")
    commands_rs_text = _read_text(root / "src-tauri/src/commands.rs")
    main_rs_text = _read_text(root / "src-tauri/src/main.rs")
    sample_success_text = _read_text(root / "ui/src/fixtures/sampleRunResult.ts").lower()
    sample_error_text = _read_text(root / "ui/src/fixtures/sampleErrorResult.ts").lower()
    advanced_text = _read_text(root / "ui/src/components/diagnostics/AdvancedDiagnostics.tsx").lower()
    messages_text = _read_text(root / "ui/src/i18n/messages.ts").lower()

    format_hits = [fmt for fmt in SUPPORTED_FORMATS if fmt in ui_text]
    command_hits = [name for name in COMMAND_NAMES if name in bridge_client_text]
    rust_command_hits = [name for name in COMMAND_NAMES if name in commands_rs_text]
    cli_command_hits = [name.replace("_", "-") for name in COMMAND_NAMES if name.replace("_", "-") in main_rs_text]
    direct_python_hits = [term for term in ("run_public_core_adapter.py", "subprocess", "python.exe") if term in ui_text]
    zephyr_dev_root_hits = [term for term in ("zephyr_dev_root", "zephyr-dev-root") if term in ui_text]
    invoke_mode_declared = "invoke_ready_not_window_e2e" in bridge_client_text
    ui_real_run_controls_present = "run" in messages_text and "read latest result" in messages_text
    proof_panel_present = "interactionproofpanel" in ui_text and "proofexport" in messages_text
    unsupported_notice_present = "pdf" in messages_text and "docx" in messages_text
    camel_case_payloads_present = all(
        token in bridge_client_text
        for token in ("inputPath", "outputDir", "inlineText", "runResult")
    )
    managed_runtime_status_present = all(
        token in messages_text
        for token in (
            "managedruntimeavailable",
            "managedruntimeselected",
            "selectedpython",
            "installlayoutsupported",
            "installerbuilt",
            "releasecreated",
            "cleanmachineproven",
        )
    ) and "runtimepreflightcard" in ui_text and "lineagestatuscard" in ui_text
    bilingual_markers_present = all(token in messages_text for token in ('en: {', 'zh: {', 'english', '中文'))
    advanced_collapsed = "<details" in advanced_text and " open" not in advanced_text

    report = {
        "schema_version": 1,
        "report_id": "zephyr.base.s16.ui_shell_check.v1",
        "summary": {
            "pass": not missing
            and not forbidden_hits
            and not network_hits
            and not direct_python_hits
            and not zephyr_dev_root_hits
            and ui_real_run_controls_present
            and proof_panel_present
            and unsupported_notice_present
            and camel_case_payloads_present
            and managed_runtime_status_present
            and bilingual_markers_present
            and advanced_collapsed
            and len(command_hits) == len(COMMAND_NAMES)
            and len(rust_command_hits) == len(COMMAND_NAMES)
            and len(cli_command_hits) == len(COMMAND_NAMES)
            and invoke_mode_declared,
            "required_files_exist": len(missing) == 0,
            "commercial_terms_blocked": len(forbidden_hits),
            "network_calls_blocked": len(network_hits),
            "supported_formats_limited_to_base_first_slice": len(format_hits) == len(SUPPORTED_FORMATS),
            "billing_semantics_false_present": "billing_semantics: false" in sample_success_text and "billing_semantics: false" in sample_error_text,
            "ui_command_names_match_rust": len(command_hits) == len(COMMAND_NAMES) and len(rust_command_hits) == len(COMMAND_NAMES) and len(cli_command_hits) == len(COMMAND_NAMES),
            "ui_does_not_call_python_directly": len(direct_python_hits) == 0,
            "ui_does_not_use_zephyr_dev_root": len(zephyr_dev_root_hits) == 0,
            "invoke_ready_not_window_e2e_declared": invoke_mode_declared,
            "ui_real_run_controls_present": ui_real_run_controls_present,
            "interaction_proof_panel_exists": proof_panel_present,
            "camel_case_tauri_payloads_present": camel_case_payloads_present,
            "managed_runtime_status_present": managed_runtime_status_present,
            "bilingual_markers_present": bilingual_markers_present,
            "advanced_collapsed_by_default": advanced_collapsed,
            "unsupported_notice_present": unsupported_notice_present,
        },
        "missing_files": missing,
        "forbidden_hits": forbidden_hits,
        "network_hits": network_hits,
        "supported_formats_detected": format_hits,
        "direct_python_hits": direct_python_hits,
        "zephyr_dev_root_hits": zephyr_dev_root_hits,
        "ui_command_hits": command_hits,
        "rust_command_hits": rust_command_hits,
        "cli_command_hits": cli_command_hits,
    }
    out_path = root / ".tmp" / "ui_shell_check.json"
    _write_json(out_path, report)
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["summary"]["pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
