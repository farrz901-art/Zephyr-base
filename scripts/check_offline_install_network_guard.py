from __future__ import annotations

import argparse
import json
from pathlib import Path


def _write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _load_json(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Check the offline wheelhouse install path for network-guard compliance.")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)

    root = Path(__file__).resolve().parents[1]
    checker_path = root / "scripts/check_wheelhouse_runtime_install.py"
    checker_text = checker_path.read_text(encoding="utf-8")
    report_path = root / ".tmp/wheelhouse_runtime_install_check.json"
    report = _load_json(report_path) if report_path.exists() else {}
    summary = report.get("summary", {}) if isinstance(report.get("summary"), dict) else {}

    uses_no_index = "--no-index" in checker_text
    uses_find_links = "--find-links" in checker_text
    network_url_used = "https://" in checker_text or "http://" in checker_text
    direct_network_install = "pip install -r" in checker_text and "--no-index" not in checker_text
    report_requires_network_for_dependency_install = summary.get(
        "requires_network_for_dependency_install",
        False,
    )
    report_requires_network_at_runtime = summary.get("requires_network_at_runtime", False)

    passed = (
        uses_no_index
        and uses_find_links
        and not network_url_used
        and not direct_network_install
        and report_requires_network_for_dependency_install is False
        and report_requires_network_at_runtime is False
    )
    output = {
        "schema_version": 1,
        "report_id": "zephyr.base.s14.offline_install_network_guard.v1",
        "summary": {
            "pass": passed,
            "uses_no_index": uses_no_index,
            "uses_find_links": uses_find_links,
            "requires_network_for_dependency_install": report_requires_network_for_dependency_install,
            "requires_network_at_runtime": report_requires_network_at_runtime,
        },
        "checker_path": str(checker_path),
        "network_url_used": network_url_used,
        "direct_network_install": direct_network_install,
    }
    _write_json(root / ".tmp/offline_install_network_guard.json", output)
    if args.json:
        print(json.dumps(output, ensure_ascii=False, indent=2))
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
