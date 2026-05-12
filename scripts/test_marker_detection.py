from __future__ import annotations

import json
from pathlib import Path

from marker_detection import build_long_marker_text, detect_marker_in_output


def _write_run_result(path: Path, preview: str, *, status: str = "success") -> dict[str, object]:
    run_result = {
        "schema_version": 1,
        "request_id": "test-request",
        "status": status,
        "normalized_text_preview": preview,
        "usage_fact": {"billing_semantics": False},
    }
    path.write_text(json.dumps(run_result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return run_result


def test_long_file_marker_found_from_full_text(tmp_path: Path) -> None:
    output_dir = tmp_path / "file_flow"
    output_dir.mkdir()
    marker = "ZEPHYR_BASE_S17_EXTERNAL_UX_FILE_MARKER"
    run_result = _write_run_result(output_dir / "run_result.json", "Head preview only")
    (output_dir / "normalized_text.txt").write_text(build_long_marker_text(marker, "Long file proof sample"), encoding="utf-8")
    report = detect_marker_in_output(output_dir=output_dir, run_result=run_result, marker=marker)
    assert report["normalized_text_exists"] is True
    assert report["preview_marker_found"] is False
    assert report["full_text_marker_found"] is True
    assert report["marker_found"] is True
    assert report["marker_detection_failed"] is False


def test_long_text_marker_found_from_full_text_when_preview_misses(tmp_path: Path) -> None:
    output_dir = tmp_path / "text_flow"
    output_dir.mkdir()
    marker = "ZEPHYR_BASE_S17_EXTERNAL_UX_TEXT_MARKER"
    run_result = _write_run_result(output_dir / "run_result.json", "Preview without marker")
    (output_dir / "normalized_text.txt").write_text(build_long_marker_text(marker, "Long text proof sample"), encoding="utf-8")
    report = detect_marker_in_output(output_dir=output_dir, run_result=run_result, marker=marker)
    assert report["preview_marker_found"] is False
    assert report["full_text_marker_found"] is True
    assert report["marker_found"] is True


def test_preview_fallback_used_when_normalized_text_missing(tmp_path: Path) -> None:
    output_dir = tmp_path / "preview_only"
    output_dir.mkdir()
    marker = "ZEPHYR_BASE_PREVIEW_ONLY_MARKER"
    run_result = _write_run_result(output_dir / "run_result.json", f"preview {marker}")
    report = detect_marker_in_output(output_dir=output_dir, run_result=run_result, marker=marker)
    assert report["normalized_text_exists"] is False
    assert report["preview_marker_found"] is True
    assert report["full_text_marker_found"] is False
    assert report["marker_found"] is True


def test_no_marker_auto_injection(tmp_path: Path) -> None:
    output_dir = tmp_path / "no_marker"
    output_dir.mkdir()
    marker = "ZEPHYR_BASE_NOT_PRESENT_MARKER"
    run_result = _write_run_result(output_dir / "run_result.json", "Preview without marker")
    (output_dir / "normalized_text.txt").write_text(build_long_marker_text("SOME_OTHER_MARKER", "Other sample"), encoding="utf-8")
    report = detect_marker_in_output(output_dir=output_dir, run_result=run_result, marker=marker)
    assert report["processing_success"] is True
    assert report["marker_found"] is False
    assert report["marker_detection_failed"] is True
