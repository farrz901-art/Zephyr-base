from __future__ import annotations

import argparse
import json
from pathlib import Path

REQUIRED_CAMEL_TERMS = (
    "inputPath",
    "outputDir",
    "inlineText",
    "runResult",
)
REQUIRED_COMMANDS = (
    "run_local_text",
    "run_local_file",
    "write_interaction_proof",
)


def _write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _extract_block(text: str, marker: str) -> str:
    start = text.find(marker)
    if start == -1:
        return ""
    end = text.find("};", start)
    if end == -1:
        return text[start:]
    return text[start : end + 2]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Check UI -> Tauri invoke payload casing.")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)

    root = Path(__file__).resolve().parents[1]
    bridge_client_text = (root / "ui/src/services/baseBridgeClient.ts").read_text(
        encoding="utf-8",
        errors="ignore",
    )
    commands_text = (root / "src-tauri/src/commands.rs").read_text(
        encoding="utf-8",
        errors="ignore",
    )

    camel_hits = [term for term in REQUIRED_CAMEL_TERMS if term in bridge_client_text]
    command_hits = [term for term in REQUIRED_COMMANDS if term in commands_text]

    run_local_file_block = _extract_block(
        bridge_client_text,
        "const payload: RunLocalFilePayload = {",
    )
    run_local_text_block = _extract_block(
        bridge_client_text,
        "const payload: RunLocalTextPayload = {",
    )
    read_run_result_block = _extract_block(
        bridge_client_text,
        "const payload: ReadRunResultPayload = {",
    )
    output_folder_plan_block = _extract_block(
        bridge_client_text,
        "const payload: OutputFolderPlanPayload = {",
    )
    interaction_proof_block = _extract_block(
        bridge_client_text,
        "const payload: InteractionProofWritePayload = {",
    )

    forbidden_hits = []
    for label, block in {
        "runLocalFile": run_local_file_block,
        "runLocalText": run_local_text_block,
        "readRunResult": read_run_result_block,
        "openOutputFolderPlan": output_folder_plan_block,
        "writeInteractionProof": interaction_proof_block,
    }.items():
        for token in ("input_path", "output_dir", "inline_text", "run_result"):
            if f"{token}:" in block:
                forbidden_hits.append(f"{label}:{token}")

    payload_blocks = {
        "runLocalFile": "inputPath" in run_local_file_block and "outputDir" in run_local_file_block,
        "runLocalText": "inlineText" in run_local_text_block and "outputDir" in run_local_text_block,
        "readRunResult": "outputDir" in read_run_result_block,
        "openOutputFolderPlan": "outputDir" in output_folder_plan_block,
        "writeInteractionProof": "outputDir" in interaction_proof_block and "runResult" in interaction_proof_block,
    }

    report = {
        "schema_version": 1,
        "report_id": "zephyr.base.s10p.tauri_invoke_payload_shape_check.v1",
        "summary": {
            "pass": len(camel_hits) == len(REQUIRED_CAMEL_TERMS)
            and not forbidden_hits
            and len(command_hits) == len(REQUIRED_COMMANDS)
            and all(payload_blocks.values()),
            "camel_case_hits": len(camel_hits),
            "forbidden_snake_case_hits": len(forbidden_hits),
            "required_command_hits": len(command_hits),
        },
        "camel_hits": camel_hits,
        "forbidden_hits": forbidden_hits,
        "command_hits": command_hits,
        "payload_blocks": payload_blocks,
    }
    out_path = root / ".tmp" / "tauri_invoke_payload_shape_check.json"
    _write_json(out_path, report)
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["summary"]["pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
