from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path
from typing import TypedDict, cast

from uns_stream._internal.utils import sha256_file
from uns_stream.partition.auto import partition as partition_auto
from zephyr_core import PartitionStrategy

SUPPORTED_INPUT_EXTENSIONS = frozenset({".txt", ".md"})
OUTPUT_FILES = [
    "normalized_text.txt",
    "content_evidence.json",
    "receipt.json",
    "usage_fact.json",
    "run_result.json",
]


class BaseErrorDict(TypedDict):
    schema_version: int
    error_code: str
    category: str
    user_message: str
    technical_detail_safe: str
    secret_safe: bool


class RequestDict(TypedDict, total=False):
    schema_version: int
    request_id: str
    input_kind: str
    input_path: str
    inline_text: str
    output_dir: str
    requested_outputs: list[str]


@dataclass(frozen=True, slots=True)
class PreparedInput:
    input_path: Path
    input_kind: str
    request_id: str
    bridge_mode: str | None
    input_bytes: int


def _read_text(path: Path) -> str:
    raw = path.read_bytes()
    if raw.startswith(b"\xff\xfe") or raw.startswith(b"\xfe\xff"):
        return raw.decode("utf-16")
    if raw.startswith(b"\xef\xbb\xbf"):
        return raw.decode("utf-8-sig")
    return raw.decode("utf-8")


def _load_json_object(path: Path) -> dict[str, object]:
    loaded_obj: object = json.loads(_read_text(path))
    if not isinstance(loaded_obj, dict):
        raise ValueError(f"Expected JSON object at {path}")
    return cast(dict[str, object], loaded_obj)


def _resolve_from_root(root: Path, path_value: str) -> Path:
    path = Path(path_value)
    return path if path.is_absolute() else (root / path).resolve()


def _write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _build_error(*, code: str, category: str, message: str, detail: str) -> BaseErrorDict:
    return {
        "schema_version": 1,
        "error_code": code,
        "category": category,
        "user_message": message,
        "technical_detail_safe": detail,
        "secret_safe": True,
    }


def _normalize_text_preview(text: str) -> str:
    normalized = text.replace("\r\n", "\n").replace("\r", "\n").strip()
    return normalized[:160]


def _write_failure_outputs(
    *,
    out_dir: Path,
    request_id: str,
    error: BaseErrorDict,
    input_bytes: int,
    bridge_mode: str | None,
) -> dict[str, object]:
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "normalized_text.txt").write_text("", encoding="utf-8")
    content_evidence: dict[str, object] = {
        "schema_version": 1,
        "evidence_kind": "artifact_reference_only_v1",
        "normalized_text_status": "missing",
        "elements_count": 0,
        "production_runtime": False,
        "adapter_runtime": "zephyr_bundle_public_core_local_runner_v1",
        "fixture_runner_used": False,
        "bundled_runtime_used": True,
        "zephyr_dev_public_core_invoked": False,
        "zephyr_dev_working_tree_required": False,
        "installer_runtime_complete": False,
        "requires_network": False,
        "requires_p45_substrate": False,
    }
    receipt: dict[str, object] = {
        "schema_version": 1,
        "run_id": f"failed-{request_id}",
        "request_id": request_id,
        "status": "failed",
        "delivery_outcome": "failed",
        "output_root": str(out_dir),
        "artifacts": OUTPUT_FILES,
        "created_by": "Zephyr bundled public core runner",
        "production_runtime": False,
        "adapter_runtime": "zephyr_bundle_public_core_local_runner_v1",
        "fixture_runner_used": False,
        "bundled_runtime_used": True,
        "zephyr_dev_public_core_invoked": False,
        "zephyr_dev_working_tree_required": False,
        "installer_runtime_complete": False,
        "requires_network": False,
        "requires_p45_substrate": False,
    }
    usage_fact: dict[str, object] = {
        "schema_version": 1,
        "fact_kind": "technical_usage_fact",
        "billing_semantics": False,
        "input_bytes": input_bytes,
        "output_files_count": len(OUTPUT_FILES),
        "adapter_runtime": "zephyr_bundle_public_core_local_runner_v1",
        "production_runtime": False,
        "fixture_runner_used": False,
        "bundled_runtime_used": True,
        "zephyr_dev_public_core_invoked": False,
        "zephyr_dev_working_tree_required": False,
        "installer_runtime_complete": False,
        "requires_network": False,
        "requires_p45_substrate": False,
    }
    run_result: dict[str, object] = {
        "schema_version": 1,
        "request_id": request_id,
        "status": "failed",
        "normalized_text_preview": "",
        "content_evidence_summary": {
            "elements_count": 0,
            "has_normalized_text": False,
            "evidence_kind": "artifact_reference_only_v1",
        },
        "receipt": receipt,
        "usage_fact": usage_fact,
        "output_files": OUTPUT_FILES,
        "error": error,
        "adapter_runtime": "zephyr_bundle_public_core_local_runner_v1",
        "production_runtime": False,
        "fixture_runner_used": False,
        "bundled_runtime_used": True,
        "zephyr_dev_public_core_invoked": False,
        "zephyr_dev_working_tree_required": False,
        "installer_runtime_complete": False,
        "requires_network": False,
        "requires_p45_substrate": False,
    }
    if bridge_mode is not None:
        content_evidence["local_text_bridge_mode"] = bridge_mode
        receipt["local_text_bridge_mode"] = bridge_mode
        usage_fact["local_text_bridge_mode"] = bridge_mode
        run_result["local_text_bridge_mode"] = bridge_mode
    _write_json(out_dir / "content_evidence.json", content_evidence)
    _write_json(out_dir / "receipt.json", receipt)
    _write_json(out_dir / "usage_fact.json", usage_fact)
    _write_json(out_dir / "run_result.json", run_result)
    return run_result


def _prepare_input(*, root: Path, request: RequestDict, temp_root: Path) -> PreparedInput:
    request_id = str(request.get("request_id", "unknown-request"))
    input_kind = str(request.get("input_kind", "unknown"))
    if input_kind == "local_file":
        input_path_value = str(request.get("input_path", ""))
        input_path = _resolve_from_root(root, input_path_value)
        if not input_path.exists():
            raise FileNotFoundError(str(input_path))
        ext = input_path.suffix.lower()
        if ext not in SUPPORTED_INPUT_EXTENSIONS:
            raise ValueError(f"unsupported_extension:{ext}")
        return PreparedInput(
            input_path=input_path,
            input_kind=input_kind,
            request_id=request_id,
            bridge_mode=None,
            input_bytes=input_path.stat().st_size,
        )
    if input_kind == "local_text":
        inline_text = str(request.get("inline_text", ""))
        temp_root.mkdir(parents=True, exist_ok=True)
        temp_path = temp_root / f"{request_id}.txt"
        temp_path.write_text(inline_text, encoding="utf-8")
        return PreparedInput(
            input_path=temp_path,
            input_kind=input_kind,
            request_id=request_id,
            bridge_mode="temp_file_to_public_core",
            input_bytes=len(inline_text.encode("utf-8")),
        )
    raise ValueError(f"unsupported_input_kind:{input_kind}")


def _build_success_outputs(
    *,
    prepared: PreparedInput,
    request: RequestDict,
    out_dir: Path,
) -> dict[str, object]:
    result = partition_auto(filename=str(prepared.input_path), strategy=PartitionStrategy.AUTO)
    normalized_text = result.normalized_text
    normalized_preview = _normalize_text_preview(normalized_text)
    content_evidence: dict[str, object] = {
        "schema_version": 1,
        "evidence_kind": "public_core_content_evidence_v1",
        "normalized_text_status": "available",
        "normalized_text_preview": normalized_preview,
        "normalized_text_len": len(normalized_text),
        "elements_count": len(result.elements),
        "source_kind": prepared.input_kind,
        "input_bytes": prepared.input_bytes,
        "production_runtime": True,
        "adapter_runtime": "zephyr_bundle_public_core_local_runner_v1",
        "fixture_runner_used": False,
        "bundled_runtime_used": True,
        "zephyr_dev_public_core_invoked": False,
        "zephyr_dev_working_tree_required": False,
        "installer_runtime_complete": False,
        "requires_network": False,
        "requires_p45_substrate": False,
    }
    receipt: dict[str, object] = {
        "schema_version": 1,
        "run_id": sha256_file(prepared.input_path),
        "request_id": prepared.request_id,
        "status": "success",
        "delivery_outcome": "success",
        "output_root": str(out_dir),
        "artifacts": OUTPUT_FILES,
        "created_by": "Zephyr bundled public core runner",
        "production_runtime": True,
        "adapter_runtime": "zephyr_bundle_public_core_local_runner_v1",
        "fixture_runner_used": False,
        "bundled_runtime_used": True,
        "zephyr_dev_public_core_invoked": False,
        "zephyr_dev_working_tree_required": False,
        "installer_runtime_complete": False,
        "requires_network": False,
        "requires_p45_substrate": False,
    }
    usage_fact: dict[str, object] = {
        "schema_version": 1,
        "fact_kind": "technical_usage_fact",
        "billing_semantics": False,
        "input_bytes": prepared.input_bytes,
        "output_files_count": len(OUTPUT_FILES),
        "adapter_runtime": "zephyr_bundle_public_core_local_runner_v1",
        "production_runtime": True,
        "fixture_runner_used": False,
        "bundled_runtime_used": True,
        "zephyr_dev_public_core_invoked": False,
        "zephyr_dev_working_tree_required": False,
        "installer_runtime_complete": False,
        "requires_network": False,
        "requires_p45_substrate": False,
    }
    run_result: dict[str, object] = {
        "schema_version": 1,
        "request_id": prepared.request_id,
        "status": "success",
        "normalized_text_preview": normalized_preview,
        "content_evidence_summary": {
            "elements_count": len(result.elements),
            "has_normalized_text": True,
            "evidence_kind": "public_core_content_evidence_v1",
        },
        "receipt": receipt,
        "usage_fact": usage_fact,
        "output_files": OUTPUT_FILES,
        "error": None,
        "adapter_runtime": "zephyr_bundle_public_core_local_runner_v1",
        "production_runtime": True,
        "fixture_runner_used": False,
        "bundled_runtime_used": True,
        "zephyr_dev_public_core_invoked": False,
        "zephyr_dev_working_tree_required": False,
        "installer_runtime_complete": False,
        "requires_network": False,
        "requires_p45_substrate": False,
        "requested_outputs": request.get("requested_outputs", []),
        "supported_input_extensions": sorted(SUPPORTED_INPUT_EXTENSIONS),
        "content_evidence_kind": "public_core_content_evidence_v1",
    }
    if prepared.bridge_mode is not None:
        content_evidence["local_text_bridge_mode"] = prepared.bridge_mode
        receipt["local_text_bridge_mode"] = prepared.bridge_mode
        usage_fact["local_text_bridge_mode"] = prepared.bridge_mode
        run_result["local_text_bridge_mode"] = prepared.bridge_mode

    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "normalized_text.txt").write_text(normalized_text, encoding="utf-8")
    _write_json(out_dir / "content_evidence.json", content_evidence)
    _write_json(out_dir / "receipt.json", receipt)
    _write_json(out_dir / "usage_fact.json", usage_fact)
    _write_json(out_dir / "run_result.json", run_result)
    return run_result


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run the bundled public core local runner.")
    parser.add_argument("--root", type=Path, default=Path("."))
    parser.add_argument("--request", type=Path, required=True)
    parser.add_argument("--out-dir", type=Path, required=True)
    parser.add_argument("--json", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_arg_parser()
    args = parser.parse_args(argv)
    root = args.root.resolve()
    request_path = args.request if args.request.is_absolute() else (root / args.request).resolve()
    out_dir = args.out_dir if args.out_dir.is_absolute() else (root / args.out_dir).resolve()
    request = cast(RequestDict, _load_json_object(request_path))
    temp_root = out_dir / "_temp_inputs"
    exit_code = 0
    try:
        prepared = _prepare_input(root=root, request=request, temp_root=temp_root)
        run_result = _build_success_outputs(prepared=prepared, request=request, out_dir=out_dir)
    except FileNotFoundError as exc:
        run_result = _write_failure_outputs(
            out_dir=out_dir,
            request_id=str(request.get("request_id", "unknown-request")),
            error=_build_error(
                code="base_input_missing",
                category="input",
                message="Input file was not found.",
                detail=str(exc),
            ),
            input_bytes=0,
            bridge_mode=None,
        )
        exit_code = 1
    except ValueError as exc:
        detail = str(exc)
        category = "input" if detail.startswith("unsupported_") else "processing"
        run_result = _write_failure_outputs(
            out_dir=out_dir,
            request_id=str(request.get("request_id", "unknown-request")),
            error=_build_error(
                code="base_request_invalid",
                category=category,
                message="Bundled public-core request could not be processed.",
                detail=detail,
            ),
            input_bytes=0,
            bridge_mode=None,
        )
        exit_code = 1
    except Exception as exc:
        run_result = _write_failure_outputs(
            out_dir=out_dir,
            request_id=str(request.get("request_id", "unknown-request")),
            error=_build_error(
                code="base_processing_failed",
                category="processing",
                message="Bundled public-core processing failed.",
                detail=f"{type(exc).__name__}: {exc}",
            ),
            input_bytes=0,
            bridge_mode=None,
        )
        exit_code = 1
    if args.json:
        print(json.dumps(run_result, ensure_ascii=False, indent=2))
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
