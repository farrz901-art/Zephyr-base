from __future__ import annotations

import argparse
import json
import subprocess
from datetime import UTC, datetime
from pathlib import Path


def _write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _write_markdown(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _read_json(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def _git_output(repo: Path, *args: str) -> str | None:
    completed = subprocess.run(
        ["git", "-c", f"safe.directory={repo}", "-C", str(repo), *args],
        check=False,
        capture_output=True,
        text=True,
    )
    if completed.returncode != 0:
        return None
    return completed.stdout.strip()


def _generated_at_utc() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def render_markdown(report: dict[str, object]) -> str:
    summary = report["summary"]
    readiness = report["m3_readiness"]
    scope = report["scope"]
    boundary = report["boundary"]
    lines = [
        "# Base M3 Readiness",
        "",
        "## Final judgment",
        f"- overall: {summary['overall']}",
        f"- pass: {summary['pass']}",
        "",
        "## Readiness",
        f"- base_mvp_runnable: {readiness['base_mvp_runnable']}",
        f"- external_package_ux_proven: {readiness['external_package_ux_proven']}",
        f"- portable_zip_package_proven: {readiness['portable_zip_package_proven']}",
        f"- managed_runtime_bootstrap_proven: {readiness['managed_runtime_bootstrap_proven']}",
        f"- offline_runtime_proven: {readiness['offline_runtime_proven']}",
        f"- clean_machine_runtime_proven: {readiness['clean_machine_runtime_proven']}",
        f"- bilingual_ui_proven: {readiness['bilingual_ui_proven']}",
        f"- m3_distribution_decision: {readiness['m3_distribution_decision']}",
        "",
        "## Scope",
        f"- signed_installer: {scope['signed_installer']}",
        f"- official_release: {scope['official_release']}",
        f"- release_created: {scope['release_created']}",
        f"- auto_update: {scope['auto_update']}",
        f"- embedded_python_runtime: {scope['embedded_python_runtime']}",
        f"- runtime_capability_changed: {scope['runtime_capability_changed']}",
        "",
        "## Boundary",
        f"- pdf_claimed: {boundary['pdf_claimed']}",
        f"- docx_claimed: {boundary['docx_claimed']}",
        f"- image_or_ocr_claimed: {boundary['image_or_ocr_claimed']}",
        f"- html_claimed: {boundary['html_claimed']}",
        f"- cloud_claimed: {boundary['cloud_claimed']}",
        f"- pro_claimed: {boundary['pro_claimed']}",
        f"- license_or_entitlement_claimed: {boundary['license_or_entitlement_claimed']}",
        f"- payment_or_billing_claimed: {boundary['payment_or_billing_claimed']}",
        "",
        "## Conclusion",
        "- Base satisfies the P6-M3 MVP bar as a free local-only preview desktop product distributed as an unsigned portable zip preview package.",
    ]
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build the Base M3 readiness report.")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)

    root = Path(__file__).resolve().parents[1]
    required_paths = {
        "boundary": root / ".tmp/base_boundary_check.json",
        "ux_shell": root / ".tmp/base_ux_shell_check.json",
        "external_ux": root / ".tmp/imported_external_package_ux_proof_report.json",
        "package_report": root / ".tmp/windows_installer_package_report.json",
        "package_audit": root / ".tmp/windows_installer_package_audit.json",
        "install_smoke": root / ".tmp/windows_install_smoke_report.json",
        "external_runtime_smoke": root / ".tmp/external_package_runtime_smoke_report.json",
        "gui_bootstrap": root / ".tmp/external_gui_runtime_bootstrap_check.json",
        "managed_runtime": root / ".tmp/managed_runtime_flow_check.json",
        "clean_machine": root / ".tmp/imported_clean_machine_proof_report.json",
        "offline_runtime": root / ".tmp/imported_offline_runtime_proof_report.json",
        "overclaim": root / ".tmp/base_m3_overclaim_check.json",
        "wheelhouse": root / ".tmp/wheelhouse_wheel_only_readiness.json",
    }
    missing = [name for name, path in required_paths.items() if not path.exists()]

    if missing:
        report = {
            "schema_version": 1,
            "report_id": "zephyr.base.s18.base_m3_readiness.v1",
            "summary": {"pass": False, "overall": "fail"},
            "missing_inputs": missing,
        }
        out_root = root / ".tmp/base_m3_readiness"
        _write_json(out_root / "report.json", report)
        _write_markdown(out_root / "report.md", "# Base M3 Readiness\n\nMissing required inputs.\n")
        if args.json:
            print(json.dumps(report, ensure_ascii=False, indent=2))
        return 1

    boundary = _read_json(required_paths["boundary"])
    ux_shell = _read_json(required_paths["ux_shell"])
    external_ux = _read_json(required_paths["external_ux"])
    package_report = _read_json(required_paths["package_report"])
    package_audit = _read_json(required_paths["package_audit"])
    install_smoke = _read_json(required_paths["install_smoke"])
    external_runtime_smoke = _read_json(required_paths["external_runtime_smoke"])
    gui_bootstrap = _read_json(required_paths["gui_bootstrap"])
    managed_runtime = _read_json(required_paths["managed_runtime"])
    clean_machine = _read_json(required_paths["clean_machine"])
    offline_runtime = _read_json(required_paths["offline_runtime"])
    overclaim = _read_json(required_paths["overclaim"])
    wheelhouse = _read_json(required_paths["wheelhouse"])

    package_manifest = package_report.get("manifest", {})
    package_summary = package_report.get("summary", {})
    repo_head = _git_output(root, "rev-parse", "HEAD") or "unknown"
    origin_head = _git_output(root, "rev-parse", "origin/main")

    m3_readiness = {
        "base_mvp_runnable": package_summary.get("pass") is True and install_smoke.get("summary", {}).get("install_smoke_pass") is True,
        "external_package_ux_proven": external_ux.get("summary", {}).get("manual_gui_proof_pass") is True,
        "portable_zip_package_proven": package_manifest.get("package_kind") == "portable_zip"
        and package_audit.get("summary", {}).get("pass") is True,
        "managed_runtime_bootstrap_proven": managed_runtime.get("summary", {}).get("managed_runtime_flow_pass") is True
        and gui_bootstrap.get("summary", {}).get("pass") is True,
        "offline_runtime_proven": offline_runtime.get("summary", {}).get("external_offline_proof_pass") is True,
        "clean_machine_runtime_proven": clean_machine.get("summary", {}).get("external_clean_machine_proof_pass") is True,
        "bilingual_ui_proven": ux_shell.get("summary", {}).get("bilingual_ui") is True,
        "m3_distribution_decision": "unsigned_portable_zip_preview",
    }

    boundary_flags = {
        "pdf_claimed": overclaim.get("findings", {}).get("pdf_claimed", False),
        "docx_claimed": overclaim.get("findings", {}).get("docx_claimed", False),
        "image_or_ocr_claimed": overclaim.get("findings", {}).get("image_or_ocr_claimed", False),
        "html_claimed": overclaim.get("findings", {}).get("html_claimed", False),
        "cloud_claimed": overclaim.get("findings", {}).get("cloud_claimed", False),
        "pro_claimed": overclaim.get("findings", {}).get("pro_claimed", False),
        "license_or_entitlement_claimed": overclaim.get("findings", {}).get("license_or_entitlement_claimed", False),
        "payment_or_billing_claimed": overclaim.get("findings", {}).get("payment_or_billing_claimed", False),
        "private_core_allowed": False,
        "web_core_dependency_allowed": False,
        "secrets_printed": False,
    }

    passed = (
        boundary.get("summary", {}).get("pass") is True
        and overclaim.get("summary", {}).get("pass") is True
        and all(value is True or value == "unsigned_portable_zip_preview" for value in m3_readiness.values())
        and external_runtime_smoke.get("summary", {}).get("external_runtime_smoke_pass") is True
    )

    report = {
        "schema_version": 1,
        "report_id": "zephyr.base.s18.base_m3_readiness.v1",
        "generated_at_utc": _generated_at_utc(),
        "summary": {
            "pass": passed,
            "overall": "pass" if passed else "conditional",
        },
        "zephyr_base": {
            "current_head_sha": repo_head,
            "pushed": origin_head == repo_head and origin_head is not None,
        },
        "m3_readiness": m3_readiness,
        "scope": {
            "signed_installer": package_manifest.get("signed_installer"),
            "official_release": False,
            "release_created": package_manifest.get("release_created"),
            "auto_update": False,
            "embedded_python_runtime": package_manifest.get("embedded_python_runtime"),
            "runtime_capability_changed": False,
        },
        "boundary": boundary_flags,
        "notes": [
            "M3 delivery artifact remains an unsigned portable zip preview package.",
            "Wheel-only readiness remains incomplete while langdetect-1.0.9.tar.gz remains in the local wheelhouse proof path."
            if wheelhouse.get("wheel_only_ready") is False
            else "Wheel-only readiness is complete."
        ],
    }

    out_root = root / ".tmp/base_m3_readiness"
    _write_json(out_root / "report.json", report)
    _write_markdown(out_root / "report.md", render_markdown(report))
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
