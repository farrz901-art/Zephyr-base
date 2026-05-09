from __future__ import annotations

import argparse
import json
from pathlib import Path


DEV_PATH_MARKERS = (
    "e:\\github_projects\\zephyr-base",
    "e:\\github_projects\\zephyr",
    "/home/runner/work/zephyr-base",
)


def _write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _read_json(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def _read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore")


def _resolve_proof_root(raw: Path | None) -> Path:
    if raw is None:
        return Path(__file__).resolve().parents[1] / "proof"
    candidate = raw.resolve()
    if (candidate / "clean_machine_runtime_proof.json").exists():
        return candidate
    if (candidate / "proof/clean_machine_runtime_proof.json").exists():
        return candidate / "proof"
    raise FileNotFoundError(f"Could not locate clean-machine proof root from {raw}")


def _output_path(explicit: bool, proof_root: Path) -> Path:
    if not explicit:
        return proof_root / "clean_machine_runtime_proof_validation.json"
    return Path.cwd().resolve() / ".tmp/clean_machine_runtime_proof_validation.json"


def _content_contains_dev_path(*contents: str) -> bool:
    lowered_contents = [
        content.lower().replace("/", "\\")
        for content in contents
    ]
    return any(marker in content for marker in DEV_PATH_MARKERS for content in lowered_contents)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate a Zephyr Base clean-machine runtime proof.")
    parser.add_argument("--proof-root", type=Path, default=None)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)

    proof_root = _resolve_proof_root(args.proof_root)
    proof_path = proof_root / "clean_machine_runtime_proof.json"
    text_run_result_path = proof_root / "clean_machine_text/run_result.json"
    file_run_result_path = proof_root / "clean_machine_file/run_result.json"
    proof_exists = proof_path.exists()
    proof = _read_json(proof_path) if proof_exists else {}
    text_run_result = _read_json(text_run_result_path) if text_run_result_path.exists() else {}
    file_run_result = _read_json(file_run_result_path) if file_run_result_path.exists() else {}
    usage_fact = text_run_result.get("usage_fact", {}) if isinstance(text_run_result, dict) else {}
    if not isinstance(usage_fact, dict):
        usage_fact = {}

    dev_path_found = _content_contains_dev_path(
        _read_text(proof_path) if proof_path.exists() else "",
        _read_text(text_run_result_path) if text_run_result_path.exists() else "",
        _read_text(file_run_result_path) if file_run_result_path.exists() else "",
    )
    text_flow = proof.get("text_flow", {}) if isinstance(proof.get("text_flow"), dict) else {}
    file_flow = proof.get("file_flow", {}) if isinstance(proof.get("file_flow"), dict) else {}
    scope = proof.get("scope", {}) if isinstance(proof.get("scope"), dict) else {}
    runtime = proof.get("runtime", {}) if isinstance(proof.get("runtime"), dict) else {}

    report = {
        "schema_version": 1,
        "report_id": "zephyr.base.s13.clean_machine_runtime_proof_validation.v1",
        "summary": {
            "pass": proof_exists
            and text_run_result_path.exists()
            and file_run_result_path.exists()
            and text_flow.get("pass") is True
            and file_flow.get("pass") is True
            and text_flow.get("marker_found") is True
            and file_flow.get("marker_found") is True
            and usage_fact.get("billing_semantics") is False
            and text_run_result.get("bundled_runtime_used") is True
            and text_run_result.get("fixture_runner_used") is False
            and text_run_result.get("zephyr_dev_working_tree_required") is False
            and text_run_result.get("requires_network") is False
            and text_run_result.get("requires_p45_substrate") is False
            and scope.get("installer_built") is False
            and scope.get("release_created") is False
            and runtime.get("embedded_python_runtime") is False
            and runtime.get("wheelhouse_bundled") is False
            and scope.get("clean_machine_runtime_proven") is True
            and not dev_path_found,
            "proof_exists": proof_exists,
            "run_result_exists": text_run_result_path.exists() and file_run_result_path.exists(),
            "marker_found": text_flow.get("marker_found") is True and file_flow.get("marker_found") is True,
        },
        "proof_root": str(proof_root),
        "proof_exists": proof_exists,
        "run_result_exists": text_run_result_path.exists() and file_run_result_path.exists(),
        "marker_found": text_flow.get("marker_found") is True and file_flow.get("marker_found") is True,
        "dev_path_found": dev_path_found,
        "billing_semantics": usage_fact.get("billing_semantics"),
        "bundled_runtime_used": text_run_result.get("bundled_runtime_used"),
        "fixture_runner_used": text_run_result.get("fixture_runner_used"),
        "zephyr_dev_working_tree_required": text_run_result.get("zephyr_dev_working_tree_required"),
        "requires_network": text_run_result.get("requires_network"),
        "requires_p45_substrate": text_run_result.get("requires_p45_substrate"),
    }
    output_path = _output_path(args.proof_root is not None, proof_root)
    _write_json(output_path, report)
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["summary"]["pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
