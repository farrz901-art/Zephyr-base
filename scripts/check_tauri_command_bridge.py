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
    detail = (completed.stdout + "\n" + completed.stderr).strip()
    return True, completed.returncode == 0, detail


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Check the Zephyr-base Tauri command bridge.")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)

    root = Path(__file__).resolve().parents[1]
    required_files = (
        root / "src-tauri/Cargo.toml",
        root / "src-tauri/tauri.conf.json",
        root / "src-tauri/src/main.rs",
        root / "src-tauri/src/commands.rs",
        root / "src-tauri/src/bridge.rs",
        root / "src-tauri/src/errors.rs",
        root / "src-tauri/src/lineage.rs",
    )
    missing = [path.relative_to(root).as_posix() for path in required_files if not path.exists()]

    commands_text = _read_text(root / "src-tauri/src/commands.rs") if not missing else ""
    bridge_text = _read_text(root / "src-tauri/src/bridge.rs") if not missing else ""
    main_text = _read_text(root / "src-tauri/src/main.rs") if not missing else ""
    cargo_text = _read_text(root / "src-tauri/Cargo.toml") if not missing else ""
    source_text = "\n".join((commands_text, bridge_text, main_text)).lower()

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
            "pub fn read_lineage_snapshot",
        )
    )
    bundled_adapter_invocation_detected = (
        "run_public_core_adapter.py" in bridge_text and "runtime/public-core-bundle" in bridge_text
    )
    uses_zephyr_dev_root = "zephyr_dev_root" in source_text
    runtime_bridge_text = bridge_text.split("#[cfg(test)]", 1)[0].lower()
    fixture_fallback_used = "allow-fixture-fallback" in runtime_bridge_text or "run_public_core_fixture" in runtime_bridge_text
    tauri_registration_pass = (
        "#[tauri::command]" in commands_text
        and "tauri::Builder::default()" in main_text
        and "tauri::generate_handler!" in main_text
    )
    static_bridge_check_pass = (
        not missing
        and not blocked_terms
        and commands_exist
        and bundled_adapter_invocation_detected
        and not uses_zephyr_dev_root
        and not fixture_fallback_used
        and "tauri =" in cargo_text
        and tauri_registration_pass
    )

    cargo_available, cargo_check_pass, cargo_detail = _cargo_check(root)
    pass_value = static_bridge_check_pass and (cargo_check_pass if cargo_available else True)
    report = {
        "schema_version": 1,
        "report_id": "zephyr.base.s6.tauri_command_bridge_check.v1",
        "summary": {
            "pass": pass_value,
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
            "tauri_command_registration_pass": tauri_registration_pass,
        },
        "cargo": {"detail": cargo_detail},
        "blocked_terms": blocked_terms,
        "missing": missing,
    }
    out_path = root / ".tmp" / "tauri_command_bridge_check.json"
    _write_json(out_path, report)
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if pass_value else 1


if __name__ == "__main__":
    raise SystemExit(main())
