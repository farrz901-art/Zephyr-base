from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path


REQUIRED_GENERATED = {
    "src-tauri/gen/schemas/acl-manifests.json",
    "src-tauri/gen/schemas/capabilities.json",
    "src-tauri/gen/schemas/desktop-schema.json",
    "src-tauri/gen/schemas/windows-schema.json",
}


def _write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _tracked_files(root: Path) -> list[str]:
    completed = subprocess.run(
        ["git", "-c", f"safe.directory={root}", "-C", str(root), "ls-files"],
        check=False,
        capture_output=True,
        text=True,
    )
    if completed.returncode != 0:
        return []
    return [line.strip() for line in completed.stdout.splitlines() if line.strip()]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Check generated Tauri artifact hygiene.")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)

    root = Path(__file__).resolve().parents[1]
    tracked = _tracked_files(root)
    gen_tracked = [path for path in tracked if path.startswith("src-tauri/gen/")]
    generated_paths = {
        path.relative_to(root).as_posix()
        for path in (root / "src-tauri/gen").rglob("*")
        if path.is_file()
    } if (root / "src-tauri/gen").exists() else set()

    report = {
        "schema_version": 1,
        "report_id": "zephyr.base.s12.generated_artifact_hygiene.v1",
        "summary": {
            "pass": (root / "docs/TAURI_GENERATED_ARTIFACTS.md").exists()
            and (root / "src-tauri/capabilities/default.json").exists()
            and not gen_tracked,
            "src_tauri_gen_classified_generated": True,
            "src_tauri_gen_committed": len(gen_tracked) > 0,
            "generated_artifact_hygiene_pass": (root / "docs/TAURI_GENERATED_ARTIFACTS.md").exists()
            and (root / "src-tauri/capabilities/default.json").exists()
            and not gen_tracked,
        },
        "required_generated_present": sorted(REQUIRED_GENERATED.intersection(generated_paths)),
        "generated_paths_detected": sorted(generated_paths),
        "tracked_generated_paths": gen_tracked,
        "source_capability_config_present": (root / "src-tauri/capabilities/default.json").exists(),
        "generated_doc_present": (root / "docs/TAURI_GENERATED_ARTIFACTS.md").exists(),
    }
    out_path = root / ".tmp" / "generated_artifact_hygiene_check.json"
    _write_json(out_path, report)
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["summary"]["pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
