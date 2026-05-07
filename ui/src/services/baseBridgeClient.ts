import type {
  BaseRunResultV1,
  LineageSnapshotV1,
  OutputFolderPlanPayload,
  ReadRunResultPayload,
  ResultDisplayModel,
  RunLocalFilePayload,
  RunLocalTextPayload,
} from "../contracts/baseRunResult";

export const TAURI_COMMANDS = {
  run_local_file: "run_local_file",
  run_local_text: "run_local_text",
  read_run_result: "read_run_result",
  open_output_folder_plan: "open_output_folder_plan",
  read_lineage_snapshot: "read_lineage_snapshot",
} as const;

export interface OutputFolderPlan {
  action: string;
  output_dir: string;
  implemented: boolean;
  reason: string;
  requires_network: boolean;
  requires_p45_substrate: boolean;
  commercial_logic_allowed: boolean;
}

export interface BaseBridgeClient {
  mode: "invoke_ready_not_window_e2e";
  tauriInvokeReady: boolean;
  tauriInvokeE2eVerified: boolean;
  runLocalFile(inputPath: string, outputDir: string): Promise<BaseRunResultV1>;
  runLocalText(inlineText: string, outputDir: string): Promise<BaseRunResultV1>;
  readRunResult(outputDir: string): Promise<BaseRunResultV1>;
  readLineageSnapshot(): Promise<LineageSnapshotV1>;
  openOutputFolderPlan(outputDir: string): Promise<OutputFolderPlan>;
}

type InvokeFn = <T>(command: string, payload?: Record<string, unknown>) => Promise<T>;

function resolveInvoke(): InvokeFn | null {
  const candidate = (globalThis as { __TAURI__?: { core?: { invoke?: InvokeFn } } }).__TAURI__;
  return candidate?.core?.invoke ?? null;
}

const invoke = resolveInvoke();

function notVerified(command: string): never {
  throw new Error(
    `Tauri invoke is prepared for ${command}, but window e2e verification is not complete in S8.`,
  );
}

function invokeCommand<TPayload extends Record<string, unknown>, TResult>(
  command: string,
  payload?: TPayload,
): Promise<TResult> {
  if (invoke === null) {
    return notVerified(command);
  }
  return invoke<TResult>(command, payload);
}

export function classifyRunResult(result: BaseRunResultV1): "success" | "failed" {
  return result.status === "success" ? "success" : "failed";
}

export function extractDisplayModel(result: BaseRunResultV1): ResultDisplayModel {
  return {
    request_id: result.request_id,
    status: result.status,
    normalized_text_preview: result.normalized_text_preview,
    evidence_kind: result.content_evidence_kind ?? result.content_evidence_summary.evidence_kind,
    output_root: result.receipt.output_root,
    billing_semantics: result.usage_fact.billing_semantics,
    has_error: result.error !== null,
    error_message: result.error?.user_message ?? null,
  };
}

export function createRunLifecycle(client: BaseBridgeClient = baseBridgeClient) {
  return {
    async runLocalFile(inputPath: string, outputDir: string): Promise<BaseRunResultV1> {
      return client.runLocalFile(inputPath, outputDir);
    },
    async runLocalText(inlineText: string, outputDir: string): Promise<BaseRunResultV1> {
      return client.runLocalText(inlineText, outputDir);
    },
    async readRunResult(outputDir: string): Promise<BaseRunResultV1> {
      return client.readRunResult(outputDir);
    },
    classifyRunResult,
    extractDisplayModel,
  };
}

export const baseBridgeClient: BaseBridgeClient = {
  mode: "invoke_ready_not_window_e2e",
  tauriInvokeReady: invoke !== null,
  tauriInvokeE2eVerified: false,
  async runLocalFile(inputPath, outputDir) {
    const payload: RunLocalFilePayload = { input_path: inputPath, output_dir: outputDir };
    return invokeCommand<RunLocalFilePayload, BaseRunResultV1>(TAURI_COMMANDS.run_local_file, payload);
  },
  async runLocalText(inlineText, outputDir) {
    const payload: RunLocalTextPayload = { inline_text: inlineText, output_dir: outputDir };
    return invokeCommand<RunLocalTextPayload, BaseRunResultV1>(TAURI_COMMANDS.run_local_text, payload);
  },
  async readRunResult(outputDir) {
    const payload: ReadRunResultPayload = { output_dir: outputDir };
    return invokeCommand<ReadRunResultPayload, BaseRunResultV1>(TAURI_COMMANDS.read_run_result, payload);
  },
  async readLineageSnapshot() {
    return invokeCommand<Record<string, never>, LineageSnapshotV1>(TAURI_COMMANDS.read_lineage_snapshot);
  },
  async openOutputFolderPlan(outputDir) {
    const payload: OutputFolderPlanPayload = { output_dir: outputDir };
    return invokeCommand<OutputFolderPlanPayload, OutputFolderPlan>(TAURI_COMMANDS.open_output_folder_plan, payload);
  },
};
