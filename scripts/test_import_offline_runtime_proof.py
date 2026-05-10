from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from pathlib import Path


def _load_module():
    repo_root = Path(__file__).resolve().parents[1]
    module_path = repo_root / "scripts" / "import_offline_runtime_proof.py"
    spec = importlib.util.spec_from_file_location("import_offline_runtime_proof", module_path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def test_prefers_validation_report_under_imported_proof_root(tmp_path: Path) -> None:
    module = _load_module()
    imported_root = tmp_path / "imported" / "proof"
    imported_root.mkdir(parents=True, exist_ok=True)
    preferred_payload = {"summary": {"pass": True}, "source": "preferred"}
    _write_json(imported_root / "offline_runtime_proof_validation.json", preferred_payload)
    fallback_payload = {"summary": {"pass": False}, "source": "fallback"}
    _write_json(tmp_path / ".tmp" / "offline_runtime_proof_validation.json", fallback_payload)

    loaded = module._load_validation_report(
        imported_proof_root=imported_root,
        repo_root=tmp_path,
        validator_stdout="",
    )
    assert loaded["source"] == "preferred"


def test_falls_back_to_repo_tmp_validation_report(tmp_path: Path) -> None:
    module = _load_module()
    imported_root = tmp_path / "imported" / "proof"
    imported_root.mkdir(parents=True, exist_ok=True)
    fallback_payload = {"summary": {"pass": True}, "source": "fallback"}
    _write_json(tmp_path / ".tmp" / "offline_runtime_proof_validation.json", fallback_payload)

    loaded = module._load_validation_report(
        imported_proof_root=imported_root,
        repo_root=tmp_path,
        validator_stdout="",
    )
    assert loaded["source"] == "fallback"


def test_import_passes_when_validation_report_under_imported_proof_root_is_clean(tmp_path: Path) -> None:
    repo_root = Path(__file__).resolve().parents[1]
    proof_root = tmp_path / "external" / "ZephyrBase" / "proof"
    proof_root.mkdir(parents=True, exist_ok=True)
    proof_payload = {
        "schema_version": 1,
        "report_id": "zephyr.base.s14.offline_runtime_proof.v1",
        "text_flow": {
            "pass": True,
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
            "marker_found": True,
            "billing_semantics": False,
            "bundled_runtime_used": True,
            "fixture_runner_used": False,
            "zephyr_dev_working_tree_required": False,
            "requires_network": False,
            "requires_p45_substrate": False,
        },
        "offline_install": {
            "uses_no_index": True,
            "uses_find_links": True,
            "requires_network_for_dependency_install": False,
            "requires_network_at_runtime": False,
        },
        "scope": {
            "installer_built": False,
            "release_created": False,
            "embedded_python_runtime": False,
            "wheelhouse_bundled": True,
            "offline_runtime_install_proven": True,
        },
        "runtime": {
            "embedded_python_runtime": False,
            "wheelhouse_bundled": True,
        },
    }
    _write_json(proof_root / "offline_runtime_proof.json", proof_payload)

    completed = subprocess.run(
        [
            sys.executable,
            str(repo_root / "scripts/import_offline_runtime_proof.py"),
            "--proof-root",
            str(proof_root.parent),
            "--json",
        ],
        cwd=repo_root,
        check=False,
        capture_output=True,
        text=True,
    )
    assert completed.returncode == 0
    report = json.loads((repo_root / ".tmp/imported_offline_runtime_proof_report.json").read_text(encoding="utf-8"))
    assert report["summary"]["pass"] is True
    assert report["summary"]["external_offline_proof_pass"] is True
    assert report["validation_report"]["summary"]["pass"] is True


def test_import_fails_when_validation_report_summary_is_false(tmp_path: Path) -> None:
    repo_root = Path(__file__).resolve().parents[1]
    imported_root = repo_root / ".tmp" / "imported_offline_runtime_proof" / "proof"
    imported_root.mkdir(parents=True, exist_ok=True)
    _write_json(imported_root / "offline_runtime_proof_validation.json", {"summary": {"pass": False}})

    module = _load_module()
    loaded = module._load_validation_report(
        imported_proof_root=imported_root,
        repo_root=repo_root,
        validator_stdout="",
    )
    assert loaded["summary"]["pass"] is False
