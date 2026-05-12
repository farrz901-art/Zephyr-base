from __future__ import annotations

from pathlib import Path


def _read_text(path: Path) -> str:
    raw = path.read_bytes()
    if raw.startswith(b"\xff\xfe") or raw.startswith(b"\xfe\xff"):
        return raw.decode("utf-16")
    if raw.startswith(b"\xef\xbb\xbf"):
        return raw.decode("utf-8-sig")
    return raw.decode("utf-8")


def detect_marker_in_output(
    *,
    output_dir: Path,
    run_result: dict[str, object],
    marker: str,
) -> dict[str, object]:
    normalized_text_path = output_dir / "normalized_text.txt"
    preview = str(run_result.get("normalized_text_preview", ""))
    preview_marker_found = bool(marker) and marker in preview
    full_text_marker_found = False
    if marker and normalized_text_path.exists():
        full_text_marker_found = marker in _read_text(normalized_text_path)
    processing_success = run_result.get("status") == "success"
    marker_found = full_text_marker_found or preview_marker_found
    return {
        "normalized_text_exists": normalized_text_path.exists(),
        "preview_marker_found": preview_marker_found,
        "full_text_marker_found": full_text_marker_found,
        "marker_found": marker_found,
        "processing_success": processing_success,
        "marker_detection_failed": processing_success and not marker_found,
    }


def build_long_marker_text(marker: str, label: str) -> str:
    lines = [
        f"{label} paragraph {index:02d}. This local plain-text regression sample stays offline, filesystem-backed, and free of network requirements."
        for index in range(1, 55)
    ]
    lines.extend(
        [
            "",
            "Marker:",
            marker,
            f"{label} complete.",
        ]
    )
    return "\n".join(lines) + "\n"
