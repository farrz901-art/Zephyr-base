from __future__ import annotations

import argparse
import json
from pathlib import Path


def _write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _read_json(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def _resolve_proof_root(candidate: Path) -> Path:
    resolved = candidate.resolve()
    if (resolved / "windows_install_proof.json").exists():
        return resolved
    if (resolved / "proof/windows_install_proof.json").exists():
        return resolved / "proof"
    raise FileNotFoundError(f"Could not locate windows install proof under {candidate}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate the packaged Windows install smoke proof.")
    parser.add_argument("--proof-root", type=Path, default=Path("proof"))
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)

    root = Path(__file__).resolve().parents[1]
    proof_root = _resolve_proof_root(args.proof_root if args.proof_root.is_absolute() else (root / args.proof_root))
    proof = _read_json(proof_root / "windows_install_proof.json")
    text_flow = proof.get("text_flow", {}) if isinstance(proof.get("text_flow"), dict) else {}
    file_flow = proof.get("file_flow", {}) if isinstance(proof.get("file_flow"), dict) else {}
    offline_install = proof.get("offline_install", {}) if isinstance(proof.get("offline_install"), dict) else {}
    scope = proof.get("scope", {}) if isinstance(proof.get("scope"), dict) else {}
    runtime = proof.get("runtime", {}) if isinstance(proof.get("runtime"), dict) else {}

    passed = all(
        (
            text_flow.get("pass") is True,
            file_flow.get("pass") is True,
            text_flow.get("marker_found") is True,
            file_flow.get("marker_found") is True,
            text_flow.get("billing_semantics") is False,
            file_flow.get("billing_semantics") is False,
            text_flow.get("bundled_runtime_used") is True,
            file_flow.get("bundled_runtime_used") is True,
            text_flow.get("fixture_runner_used") is False,
            file_flow.get("fixture_runner_used") is False,
            text_flow.get("zephyr_dev_working_tree_required") is False,
            file_flow.get("zephyr_dev_working_tree_required") is False,
            text_flow.get("requires_network") is False,
            file_flow.get("requires_network") is False,
            text_flow.get("requires_p45_substrate") is False,
            file_flow.get("requires_p45_substrate") is False,
            offline_install.get("uses_no_index") is True,
            offline_install.get("uses_find_links") is True,
            offline_install.get("requires_network_for_dependency_install") is False,
            offline_install.get("requires_network_at_runtime") is False,
            scope.get("installer_built") is True,
            scope.get("release_created") is False,
            scope.get("signed_installer") is False,
            scope.get("embedded_python_runtime") is False,
            scope.get("wheelhouse_bundled") is True,
            scope.get("install_smoke_pass") is True,
            runtime.get("embedded_python_runtime") is False,
            runtime.get("wheelhouse_bundled") is True,
        )
    )

    report = {
        "schema_version": 1,
        "report_id": "zephyr.base.s15.windows_install_proof_validation.v1",
        "summary": {
            "pass": passed,
            "proof_exists": True,
            "text_flow_pass": text_flow.get("pass") is True,
            "file_flow_pass": file_flow.get("pass") is True,
        },
        "proof_root": str(proof_root),
        "proof": proof,
    }
    _write_json(proof_root / "windows_install_proof_validation.json", report)
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
