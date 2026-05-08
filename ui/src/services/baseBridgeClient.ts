import { invoke } from "@tauri-apps/api/core";

import type {
  BaseContentEvidenceV1,
  BaseRunResultV1,
  InteractionProofV1,
  InteractionProofWritePayload,
  InteractionProofWriteResult,
  LineageSnapshotV1,
  OutputFolderPlanPayload,
  ReadRunResultPayload,
  ResultDisplayModel,
  RunLocalFilePayload,
  RunLocalTextPayload,
  RuntimeModeSummary,
} from "../contracts/baseRunResult";

export interface OutputFolderPlan {
  action: "open_output_folder_plan";
  output_dir: string;
  implemented: boolean;
  reason: string;
  requires_network: boolean;
  requires_p45_substrate: boolean;
  commercial_logic_allowed: boolean;
}

export const TAURI_COMMANDS = {
  run_local_file: "run_local_file",
  run_local_text: "run_local_text",
  read_run_result: "read_run_result",
  open_output_folder_plan: "open_output_folder_plan",
  read_lineage_snapshot: "read_lineage_snapshot",
  write_interaction_proof: "write_interaction_proof",
} as const;

export const runtimeMode: RuntimeModeSummary = {
  mode: "invoke_ready_not_window_e2e",
  tauri_invoke_ready: true,
  tauri_invoke_e2e_verified: false,
  uses_bundled_adapter: true,
  uses_current_python_environment: true,
  embedded_python_runtime: false,
  wheelhouse_bundled: false,
  installer_runtime_complete: false,
};

type TauriCommandName = (typeof TAURI_COMMANDS)[keyof typeof TAURI_COMMANDS];

function hasTauriInvoke(): boolean {
  if (typeof window === "undefined") {
    return false;
  }
  const globalWindow = window as Window & { __TAURI_INTERNALS__?: unknown };
  return globalWindow.__TAURI_INTERNALS__ !== undefined;
}

async function invokeJson<TPayload, TResult>(
  command: TauriCommandName,
  payload?: TPayload,
): Promise<TResult> {
  if (!hasTauriInvoke()) {
    throw new Error(
      "Tauri invoke is not available in this browser-only shell. Launch the desktop app path for real local runs.",
    );
  }
  return invoke<TResult>(command, payload as Record<string, unknown> | undefined);
}

export function buildEvidenceFromRunResult(result: BaseRunResultV1): BaseContentEvidenceV1 {
  return {
    schema_version: 1,
    evidence_kind:
      result.content_evidence_kind ?? result.content_evidence_summary.evidence_kind,
    normalized_text_preview: result.normalized_text_preview,
    source_kind: "local_artifact",
    elements_count: result.content_evidence_summary.elements_count,
    token_marker_found: result.normalized_text_preview.includes("ZEPHYR_BASE"),
    bundled_runtime_used: result.bundled_runtime_used,
    zephyr_dev_working_tree_required: result.zephyr_dev_working_tree_required,
    installer_runtime_complete: result.installer_runtime_complete,
    requires_network: result.requires_network,
    requires_p45_substrate: result.requires_p45_substrate,
  };
}

export function classifyRunResult(result: BaseRunResultV1): "success" | "failed" {
  return result.status === "success" ? "success" : "failed";
}

export function extractDisplayModel(result: BaseRunResultV1): ResultDisplayModel {
  return {
    request_id: result.request_id,
    status: result.status,
    normalized_text_preview: result.normalized_text_preview,
    evidence_kind: result.content_evidence_summary.evidence_kind,
    output_root: result.receipt.output_root,
    billing_semantics: result.usage_fact.billing_semantics,
    has_error: result.error !== null,
    error_message: result.error?.user_message ?? null,
  };
}

export function createRunLifecycle(result: BaseRunResultV1) {
  return {
    classification: classifyRunResult(result),
    displayModel: extractDisplayModel(result),
    evidence: buildEvidenceFromRunResult(result),
  };
}

export const baseBridgeClient = {
  runtimeMode,
  hasTauriInvoke,
  async runLocalFile(inputPath: string, outputDir: string): Promise<BaseRunResultV1> {
    const payload: RunLocalFilePayload = {
      input_path: inputPath,
      output_dir: outputDir,
    };
    return invokeJson<RunLocalFilePayload, BaseRunResultV1>(
      TAURI_COMMANDS.run_local_file,
      payload,
    );
  },
  async runLocalText(inlineText: string, outputDir: string): Promise<BaseRunResultV1> {
    const payload: RunLocalTextPayload = {
      inline_text: inlineText,
      output_dir: outputDir,
    };
    return invokeJson<RunLocalTextPayload, BaseRunResultV1>(
      TAURI_COMMANDS.run_local_text,
      payload,
    );
  },
  async readRunResult(outputDir: string): Promise<BaseRunResultV1> {
    const payload: ReadRunResultPayload = { output_dir: outputDir };
    return invokeJson<ReadRunResultPayload, BaseRunResultV1>(
      TAURI_COMMANDS.read_run_result,
      payload,
    );
  },
  async readLineageSnapshot(): Promise<LineageSnapshotV1> {
    return invokeJson<undefined, LineageSnapshotV1>(TAURI_COMMANDS.read_lineage_snapshot);
  },
  async openOutputFolderPlan(outputDir: string): Promise<OutputFolderPlan> {
    const payload: OutputFolderPlanPayload = { output_dir: outputDir };
    return invokeJson<OutputFolderPlanPayload, OutputFolderPlan>(
      TAURI_COMMANDS.open_output_folder_plan,
      payload,
    );
  },
  async writeInteractionProof(
    outputDir: string,
    proof: InteractionProofV1,
    runResult: BaseRunResultV1,
  ): Promise<InteractionProofWriteResult> {
    const payload: InteractionProofWritePayload = {
      output_dir: outputDir,
      proof,
      run_result: runResult,
    };
    return invokeJson<InteractionProofWritePayload, InteractionProofWriteResult>(
      TAURI_COMMANDS.write_interaction_proof,
      payload,
    );
  },
};
