import type { BaseContentEvidenceV1, BaseRunResultV1, LineageSnapshotV1 } from "../contracts/baseRunResult";
import { sampleErrorEvidence, sampleErrorResult } from "../fixtures/sampleErrorResult";
import {
  sampleLineageSnapshot,
  sampleRuntimeMode,
  sampleSuccessEvidence,
  sampleSuccessResult,
} from "../fixtures/sampleRunResult";
import type { OutputFolderPlan } from "./baseBridgeClient";

export const mockArtifactClient = {
  runtimeMode: sampleRuntimeMode,
  async loadSampleSuccess(): Promise<{ result: BaseRunResultV1; evidence: BaseContentEvidenceV1 }> {
    return { result: sampleSuccessResult, evidence: sampleSuccessEvidence };
  },
  async loadSampleError(): Promise<{ result: BaseRunResultV1; evidence: BaseContentEvidenceV1 }> {
    return { result: sampleErrorResult, evidence: sampleErrorEvidence };
  },
  async readLineageSnapshot(): Promise<LineageSnapshotV1> {
    return sampleLineageSnapshot;
  },
  async openOutputFolderPlan(outputDir: string): Promise<OutputFolderPlan> {
    return {
      action: "open_output_folder_plan",
      output_dir: outputDir,
      implemented: false,
      reason: "S7 shows the output folder plan in the UI shell; native open behavior lands later.",
      requires_network: false,
      requires_p45_substrate: false,
      commercial_logic_allowed: false,
    };
  },
};
