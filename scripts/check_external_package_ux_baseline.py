from __future__ import annotations

import argparse
import json
from pathlib import Path


REQUIRED_FILES = [
    Path("docs/BASE_EXTERNAL_UX_SMOKE_POLICY.md"),
    Path("docs/MANUAL_EXTERNAL_PACKAGE_UX_PROOF.md"),
    Path("scripts/build_external_package_ux_proof_pack.py"),
    Path("scripts/validate_external_package_ux_proof.py"),
    Path("scripts/import_external_package_ux_proof.py"),
    Path("scripts/run_external_package_runtime_smoke.py"),
    Path("ui/src/i18n/messages.ts"),
    Path("ui/src/components/common/LanguageToggle.tsx"),
]
PACKAGE_PATH = Path(".tmp/windows_installer_package/ZephyrBase-windows-unsigned.zip")
SUPPORTED_FORMATS = (".txt", ".text", ".log", ".md", ".markdown")


def _write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Check the S17 external package UX baseline.")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)

    root = Path(__file__).resolve().parents[1]
    missing = [path.as_posix() for path in REQUIRED_FILES if not (root / path).exists()]
    messages_text = (root / "ui/src/i18n/messages.ts").read_text(encoding="utf-8", errors="ignore").lower()
    ui_text = "\n".join(
        path.read_text(encoding="utf-8", errors="ignore").lower()
        for path in (root / "ui/src").rglob("*")
        if path.is_file()
    )
    bilingual_ui = ("en:" in messages_text or "en =" in messages_text) and ("zh:" in messages_text or "zh =" in messages_text)
    no_unsupported_claim = not any(term in ui_text for term in ("pdf support", "docx support", "ocr support", "image support"))
    no_commercial_claim = not any(term in ui_text for term in ("billing plan", "payment plan", "license portal", "entitlement flow", "quota"))
    no_network_claim = not any(term in ui_text for term in ("cloud processing", "web api", "online sync"))
    supported_formats_truthful = all(fmt in ui_text for fmt in SUPPORTED_FORMATS)
    report = {
        "schema_version": 1,
        "report_id": "zephyr.base.s17.external_package_ux_baseline_check.v1",
        "summary": {
            "pass": not missing
            and (root / PACKAGE_PATH).exists()
            and bilingual_ui
            and no_unsupported_claim
            and no_commercial_claim
            and no_network_claim
            and supported_formats_truthful,
            "bilingual_ui": bilingual_ui,
            "package_exists": (root / PACKAGE_PATH).exists(),
            "no_unsupported_claim": no_unsupported_claim,
            "no_commercial_claim": no_commercial_claim,
            "no_network_claim": no_network_claim,
        },
        "missing_files": missing,
    }
    _write_json(root / ".tmp/external_package_ux_baseline_check.json", report)
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["summary"]["pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
