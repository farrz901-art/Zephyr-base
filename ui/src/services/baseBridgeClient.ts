import type { BaseRunResultV1, LineageSnapshotV1 } from "../contracts/baseRunResult";

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
  mode: "invoke_ready_not_e2e_verified";
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
    `Tauri invoke is prepared for ${command}, but end-to-end verification is not complete in S7.`,
  );
}

export const baseBridgeClient: BaseBridgeClient = {
  mode: "invoke_ready_not_e2e_verified",
  tauriInvokeReady: invoke !== null,
  tauriInvokeE2eVerified: false,
  async runLocalFile(inputPath, outputDir) {
    if (invoke === null) {
      return notVerified("run_local_file");
    }
    return invoke<BaseRunResultV1>("run_local_file", { inputPath, outputDir });
  },
  async runLocalText(inlineText, outputDir) {
    if (invoke === null) {
      return notVerified("run_local_text");
    }
    return invoke<BaseRunResultV1>("run_local_text", { inlineText, outputDir });
  },
  async readRunResult(outputDir) {
    if (invoke === null) {
      return notVerified("read_run_result");
    }
    return invoke<BaseRunResultV1>("read_run_result", { outputDir });
  },
  async readLineageSnapshot() {
    if (invoke === null) {
      return notVerified("read_lineage_snapshot");
    }
    return invoke<LineageSnapshotV1>("read_lineage_snapshot");
  },
  async openOutputFolderPlan(outputDir) {
    if (invoke === null) {
      return notVerified("open_output_folder_plan");
    }
    return invoke<OutputFolderPlan>("open_output_folder_plan", { outputDir });
  },
};
