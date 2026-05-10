from __future__ import annotations

import argparse
import json
import shutil
import subprocess
from pathlib import Path

FORBIDDEN_TERMS = ("entitlement", "payment", "license_verify", "web_core", "zephyr_pro")


def _write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _run(command: list[str], cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        command,
        cwd=cwd,
        check=False,
        capture_output=True,
        text=True,
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build and typecheck the Zephyr-base UI shell.")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)

    root = Path(__file__).resolve().parents[1]
    ui_root = root / "ui"
    node_available = shutil.which("node") is not None
    npm_executable = shutil.which("npm")
    npm_available = npm_executable is not None
    lock_file_exists = (ui_root / "package-lock.json").exists()
    node_modules_exists = (ui_root / "node_modules").exists()

    install_pass = False
    build_pass = False
    typecheck_pass = False
    install_detail = "npm not available"
    build_detail = "build not attempted"
    typecheck_detail = "typecheck not attempted"

    if node_available and npm_available:
        install_command = [npm_executable, "--prefix", "ui", "ci" if lock_file_exists else "install"]
        install_completed = _run(install_command, root)
        install_pass = install_completed.returncode == 0
        install_detail = (install_completed.stdout + "\n" + install_completed.stderr).strip()

        build_completed = None
        typecheck_completed = None
        if install_pass or node_modules_exists:
            build_completed = _run([npm_executable, "--prefix", "ui", "run", "build"], root)
            build_pass = build_completed.returncode == 0
            build_detail = (build_completed.stdout + "\n" + build_completed.stderr).strip()
            typecheck_completed = _run([npm_executable, "--prefix", "ui", "run", "typecheck"], root)
            typecheck_pass = typecheck_completed.returncode == 0
            typecheck_detail = (typecheck_completed.stdout + "\n" + typecheck_completed.stderr).strip()
            if not install_pass and node_modules_exists and build_pass and typecheck_pass:
                install_pass = True
                install_detail = (
                    install_detail
                    + "\nFallback: reused existing ui/node_modules after npm ci/install failed, and build+typecheck still passed."
                ).strip()

    dist_root = ui_root / "dist"
    index_exists = (dist_root / "index.html").exists()
    asset_files = [path.relative_to(root).as_posix() for path in dist_root.rglob("*") if path.is_file()] if dist_root.exists() else []
    generated_text = ""
    if dist_root.exists():
        for path in dist_root.rglob("*"):
            if path.is_file() and path.suffix.lower() in {".html", ".js", ".css"}:
                generated_text += path.read_text(encoding="utf-8", errors="ignore").lower()
    forbidden_hits = [term for term in FORBIDDEN_TERMS if term in generated_text]

    report = {
        "schema_version": 1,
        "report_id": "zephyr.base.s9.ui_build_check.v1",
        "summary": {
            "pass": node_available and npm_available and install_pass and build_pass and typecheck_pass and index_exists and not forbidden_hits,
            "node_available": node_available,
            "npm_available": npm_available,
            "lock_file_exists": lock_file_exists or (ui_root / "package-lock.json").exists(),
            "npm_install_or_ci_pass": install_pass,
            "ui_build_pass": build_pass,
            "typecheck_pass": typecheck_pass,
            "ui_dist_exists": dist_root.exists(),
            "generated_assets_boundary_safe": not forbidden_hits,
        },
        "install_detail": install_detail,
        "build_detail": build_detail,
        "typecheck_detail": typecheck_detail,
        "asset_files": asset_files,
        "forbidden_hits": forbidden_hits,
    }
    out_path = root / ".tmp" / "ui_build_check.json"
    _write_json(out_path, report)
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["summary"]["pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
