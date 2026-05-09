from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from pathlib import Path


def _load_module(root: Path):
    module_path = root / "scripts/validate_clean_machine_runtime_proof.py"
    spec = importlib.util.spec_from_file_location("validate_clean_machine_runtime_proof", module_path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _clean_proof_payload() -> dict[str, object]:
    return {
        "schema_version": 1,
        "report_id": "zephyr.base.s13.clean_machine_runtime_proof.v1",
        "proof_level": "L1",
        "runtime": {
            "managed_python": "D:/ZephyrBaseProof/ZephyrBase/.runtime/base_runtime_venv/Scripts/python.exe",
            "managed_runtime_created": True,
            "uses_current_shell_python_for_execution": False,
            "embedded_python_runtime": False,
            "wheelhouse_bundled": False,
            "installer_runtime_complete": False,
        },
        "text_flow": {
            "pass": True,
            "run_result_exists": True,
            "marker_found": True,
            "billing_semantics": False,
            "bundled_runtime_used": True,
            "fixture_runner_used": False,
            "zephyr_dev_working_tree_required": False,
            "requires_network": False,
            "requires_p45_substrate": False,
        },
        "file_flow": {
            "pass": True,
            "run_result_exists": True,
            "marker_found": True,
            "billing_semantics": False,
            "bundled_runtime_used": True,
            "fixture_runner_used": False,
            "zephyr_dev_working_tree_required": False,
            "requires_network": False,
            "requires_p45_substrate": False,
        },
        "scope": {
            "installer_built": False,
            "release_created": False,
            "clean_machine_runtime_proven": True,
            "clean_machine_installer_proven": False,
        },
    }


def _clean_run_result(marker: str) -> dict[str, object]:
    return {
        "schema_version": 1,
        "request_id": f"proof-{marker}",
        "status": "success",
        "normalized_text_preview": marker,
        "usage_fact": {
            "billing_semantics": False,
        },
        "bundled_runtime_used": True,
        "fixture_runner_used": False,
        "zephyr_dev_working_tree_required": False,
        "requires_network": False,
        "requires_p45_substrate": False,
    }


def _create_proof_root(root: Path, proof_root: Path) -> None:
    _write_json(proof_root / "clean_machine_runtime_proof.json", _clean_proof_payload())
    _write_json(
        proof_root / "clean_machine_text/run_result.json",
        _clean_run_result("ZEPHYR_BASE_S13_CLEAN_MACHINE_TEXT_MARKER"),
    )
    _write_json(
        proof_root / "clean_machine_file/run_result.json",
        _clean_run_result("ZEPHYR_BASE_S13_CLEAN_MACHINE_FILE_MARKER"),
    )


def test_external_clean_proof_dir_validation_passes(tmp_path: Path) -> None:
    root = Path(__file__).resolve().parents[1]
    proof_root = tmp_path / "ZephyrBase" / "proof"
    _create_proof_root(root, proof_root)
    completed = subprocess.run(
        [
            sys.executable,
            str(root / "scripts/validate_clean_machine_runtime_proof.py"),
            "--proof-root",
            str(proof_root),
            "--json",
        ],
        cwd=root,
        check=False,
        capture_output=True,
        text=True,
    )
    assert completed.returncode == 0
    report = json.loads((root / ".tmp/clean_machine_runtime_proof_validation.json").read_text(encoding="utf-8"))
    assert report["summary"]["pass"] is True
    assert report["dev_path_found"] is False


def test_imported_clean_proof_under_repo_tmp_still_passes_when_content_is_clean(tmp_path: Path) -> None:
    root = Path(__file__).resolve().parents[1]
    proof_root = root / ".tmp/imported_clean_machine_proof/proof"
    if proof_root.parent.exists():
        import shutil
        shutil.rmtree(proof_root.parent)
    _create_proof_root(root, proof_root)
    completed = subprocess.run(
        [
            sys.executable,
            str(root / "scripts/validate_clean_machine_runtime_proof.py"),
            "--proof-root",
            str(proof_root),
            "--json",
        ],
        cwd=root,
        check=False,
        capture_output=True,
        text=True,
    )
    assert completed.returncode == 0
    report = json.loads((root / ".tmp/clean_machine_runtime_proof_validation.json").read_text(encoding="utf-8"))
    assert report["summary"]["pass"] is True
    assert report["dev_path_found"] is False


def test_validation_fails_when_proof_content_contains_dev_path(tmp_path: Path) -> None:
    root = Path(__file__).resolve().parents[1]
    proof_root = tmp_path / "ZephyrBase" / "proof"
    _create_proof_root(root, proof_root)
    polluted = _clean_run_result("ZEPHYR_BASE_S13_CLEAN_MACHINE_TEXT_MARKER")
    polluted["bundle_root"] = "E:/Github_Projects/Zephyr-base/runtime/public-core-bundle"
    _write_json(proof_root / "clean_machine_text/run_result.json", polluted)
    completed = subprocess.run(
        [
            sys.executable,
            str(root / "scripts/validate_clean_machine_runtime_proof.py"),
            "--proof-root",
            str(proof_root),
            "--json",
        ],
        cwd=root,
        check=False,
        capture_output=True,
        text=True,
    )
    assert completed.returncode != 0
    report = json.loads((root / ".tmp/clean_machine_runtime_proof_validation.json").read_text(encoding="utf-8"))
    assert report["summary"]["pass"] is False
    assert report["dev_path_found"] is True
