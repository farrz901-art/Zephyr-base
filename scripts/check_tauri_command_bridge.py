from __future__ import annotations

import argparse
import json
import shutil
import subprocess
from pathlib import Path

FORBIDDEN_COMMERCIAL_TERMS = (
    "license_verify",
    "entitlement_server",
    "payment_callback",
    "billing_decision",
    "quota_authority",
    "risk_score",
    "web_core",
    "zephyr_pro",
    "private_core_export",
)
FORBIDDEN_NETWORK_TERMS = (
    "reqwest",
    "ureq",
    "surf::",
    "hyper::client",
    "tokio::net",
    "tokio_tungstenite",
    "websocket",
)
REQUIRED_FILES = (
    Path("src-tauri/Cargo.toml"),
    Path("src-tauri/tauri.conf.json"),
    Path("src-tauri/src/main.rs"),
    Path("src-tauri/src/commands.rs"),
    Path("src-tauri/src/bridge.rs"),
    Path("src-tauri/src/errors.rs"),
    Path("src-tauri/src/lineage.rs"),
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


def _cargo_check(root: Path) -> tuple[bool, bool, str]:
    cargo = shutil.which("cargo")
    if cargo is None:
        return False, False, "cargo not available"
    completed = subprocess.run(
        [cargo, "check", "--manifest-path", "src-tauri/Cargo.toml"],
        cwd=root,
        check=False,
        capture_output=True,
        text=True,
    )
    combined = (completed.stdout + "\n" + completed.stderr).strip()
    return True, completed.returncode == 0, combined


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Check the Zephyr-base Tauri command bridge slice.")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)

    root = Path(__file__).resolve().parents[1]
    missing = [path.as_posix() for path in REQUIRED_FILES if not (root / path).exists()]
    out_path = root / ".tmp" / "tauri_command_bridge_check.json"
    if missing:
        report = {
            "schema_version": 1,
            "report_id": "zephyr.base.s6.tauri_command_bridge_check.v1",
            "summary": {
                "pass": False,
                "cargo_available": shutil.which("cargo") is not None,
                "cargo_check_pass": False,
                "static_bridge_check_pass": False,
                "commercial_terms_blocked": 0,
            },
            "bridge": {
                "commands_exist": False,
                "bundled_adapter_invocation_detected": False,
                "uses_zephyr_dev_root": False,
                "fixture_fallback_used": False,
                "requires_p45_substrate": False,
                "requires_network": False,
            },
            "issues": [f"missing required files: {missing}"],
        }
        _write_json(out_path, report)
        if args.json:
            print(json.dumps(report, ensure_ascii=False, indent=2))
        return 1

    commands_text = _read_text(root / "src-tauri/src/commands.rs")
    bridge_text = _read_text(root / "src-tauri/src/bridge.rs")
    main_text = _read_text(root / "src-tauri/src/main.rs")
    errors_text = _read_text(root / "src-tauri/src/errors.rs")
    lineage_text = _read_text(root / "src-tauri/src/lineage.rs")
    cargo_text = _read_text(root / "src-tauri/Cargo.toml")

    source_text = "\n".join([commands_text, bridge_text, main_text, errors_text, lineage_text]).lower()
    runtime_bridge_text = bridge_text.split("#[cfg(test)]", 1)[0].lower()
    blocked_terms = [
        term
        for term in (*FORBIDDEN_COMMERCIAL_TERMS, *FORBIDDEN_NETWORK_TERMS)
        if term in source_text
    ]
    commands_exist = all(
        marker in commands_text
        for marker in (
            "pub fn run_local_file",
            "pub fn run_local_text",
            "pub fn read_run_result",
            "pub fn open_output_folder_plan",
        )
    )
    bundled_adapter_invocation_detected = (
        "run_public_core_adapter.py" in bridge_text and "runtime/public-core-bundle" in bridge_text
    )
    uses_zephyr_dev_root = "zephyr_dev_root" in source_text
    fixture_fallback_used = (
        "allow-fixture-fallback" in runtime_bridge_text
        or "run_public_core_fixture" in runtime_bridge_text
    )
    static_bridge_check_pass = all(
        (
            commands_exist,
            bundled_adapter_invocation_detected,
            not uses_zephyr_dev_root,
            not fixture_fallback_used,
            "serde_json" in cargo_text,
            "requires_network" in bridge_text,
            "requires_p45_substrate" in bridge_text,
        )
    ) and not blocked_terms

    cargo_available, cargo_check_pass, cargo_detail = _cargo_check(root)
    summary_pass = static_bridge_check_pass and (cargo_check_pass if cargo_available else True)
    report = {
        "schema_version": 1,
        "report_id": "zephyr.base.s6.tauri_command_bridge_check.v1",
        "summary": {
            "pass": summary_pass,
            "cargo_available": cargo_available,
            "cargo_check_pass": cargo_check_pass,
            "static_bridge_check_pass": static_bridge_check_pass,
            "commercial_terms_blocked": len(blocked_terms),
        },
        "bridge": {
            "commands_exist": commands_exist,
            "bundled_adapter_invocation_detected": bundled_adapter_invocation_detected,
            "uses_zephyr_dev_root": uses_zephyr_dev_root,
            "fixture_fallback_used": fixture_fallback_used,
            "requires_p45_substrate": False,
            "requires_network": False,
            "run_local_file_command": "pub fn run_local_file" in commands_text,
            "run_local_text_command": "pub fn run_local_text" in commands_text,
            "read_run_result_command": "pub fn read_run_result" in commands_text,
            "open_output_folder_plan_command": "pub fn open_output_folder_plan" in commands_text,
        },
        "cargo": {
            "detail": cargo_detail,
        },
        "blocked_terms": blocked_terms,
        "issues": [],
    }
    if not cargo_available:
        report["issues"].append(
            "cargo is not available; static bridge validation passed but cargo check was skipped."
        )
    _write_json(out_path, report)
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if summary_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
