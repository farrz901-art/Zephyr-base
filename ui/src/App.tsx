import { useEffect, useMemo, useState } from "react";

import { AdvancedDiagnostics } from "./components/diagnostics/AdvancedDiagnostics";
import { InputCard } from "./components/input/InputCard";
import { AppShell } from "./components/layout/AppShell";
import { UserResultCard } from "./components/results/UserResultCard";
import { RunCard } from "./components/run/RunCard";
import type {
  BaseContentEvidenceV1,
  BaseRunResultV1,
  InteractionProofV1,
  LineageSnapshotV1,
  RunLifecycleState,
  RuntimeModeSummary,
} from "./contracts/baseRunResult";
import {
  sampleErrorEvidence,
  sampleErrorResult,
} from "./fixtures/sampleErrorResult";
import {
  sampleLineageSnapshot,
  sampleRuntimeMode,
  sampleSuccessEvidence,
  sampleSuccessResult,
} from "./fixtures/sampleRunResult";
import { LanguageProvider, useLanguage } from "./i18n/useLanguage";
import {
  baseBridgeClient,
  buildEvidenceFromRunResult,
  createRunLifecycle,
  type OutputFolderPlan,
} from "./services/baseBridgeClient";
import { mockArtifactClient } from "./services/mockArtifactClient";

const SUPPORTED_FORMATS = [".txt", ".text", ".log", ".md", ".markdown"] as const;
const FILE_OUTPUT_DIR = ".tmp/ui_shell_file";
const TEXT_OUTPUT_DIR = ".tmp/ui_shell_text";
const PROOF_OUTPUT_DIR = ".tmp/s10_tauri_window_interaction";
const DEFAULT_MARKER = "ZEPHYR_BASE_S16_UX_TEXT_MARKER";

type DisplayMode =
  | "real_tauri_local_text"
  | "real_tauri_local_file"
  | "sample_success"
  | "sample_error";

type StatusContext =
  | "ready"
  | "sample_success"
  | "sample_error"
  | "real_success"
  | "real_failed"
  | "read_failed";

function wait(ms: number) {
  return new Promise((resolve) => window.setTimeout(resolve, ms));
}

function BaseApp() {
  const { messages: m } = useLanguage();
  const [inputMode, setInputMode] = useState<"text" | "file">("text");
  const [displayMode, setDisplayMode] = useState<DisplayMode>("real_tauri_local_text");
  const [lifecycleState, setLifecycleState] = useState<RunLifecycleState>("idle");
  const [statusContext, setStatusContext] = useState<StatusContext>("ready");
  const [statusErrorDetail, setStatusErrorDetail] = useState<string | null>(null);
  const [inputPath, setInputPath] = useState("tests/fixtures/real_adapter_sample_input.txt");
  const [inlineText, setInlineText] = useState(DEFAULT_MARKER);
  const [result, setResult] = useState<BaseRunResultV1>(sampleSuccessResult);
  const [evidence, setEvidence] = useState<BaseContentEvidenceV1>(sampleSuccessEvidence);
  const [lineage, setLineage] = useState<LineageSnapshotV1>(sampleLineageSnapshot);
  const [runtimeMode, setRuntimeMode] = useState<RuntimeModeSummary>(sampleRuntimeMode);
  const [outputPlan, setOutputPlan] = useState<OutputFolderPlan>({
    action: "open_output_folder_plan",
    output_dir: sampleSuccessResult.receipt.output_root,
    implemented: false,
    reason: "Output folder plan is displayed in the shell; native open behavior lands later.",
    requires_network: false,
    requires_p45_substrate: false,
    commercial_logic_allowed: false,
  });
  const [lastOutputDir, setLastOutputDir] = useState(TEXT_OUTPUT_DIR);
  const [lastRealMode, setLastRealMode] = useState<"real_tauri_local_text" | "real_tauri_local_file" | null>(null);
  const [proofStatus, setProofStatus] = useState<"not_exported" | "exported" | "failed">("not_exported");
  const [proofPath, setProofPath] = useState<string | null>(null);
  const [proofErrorDetail, setProofErrorDetail] = useState<string | null>(null);

  useEffect(() => {
    const loadInitialState = async () => {
      if (baseBridgeClient.hasTauriInvoke()) {
        try {
          const lineageSnapshot = await baseBridgeClient.readLineageSnapshot();
          setLineage(lineageSnapshot);
          setRuntimeMode(baseBridgeClient.runtimeMode);
          return;
        } catch {
          // fall through to sample lineage state
        }
      }
      const lineageSnapshot = await mockArtifactClient.readLineageSnapshot();
      setLineage(lineageSnapshot);
      setRuntimeMode(mockArtifactClient.runtimeMode);
    };
    void loadInitialState();
  }, []);

  const isRunning = useMemo(
    () =>
      lifecycleState === "preparing_request" ||
      lifecycleState === "invoking_tauri_command" ||
      lifecycleState === "processing_local_runtime" ||
      lifecycleState === "reading_result",
    [lifecycleState],
  );

  const statusView = useMemo(() => {
    if (lifecycleState === "preparing_request") {
      return { status: m.status.preparing, detail: m.status.preparingDetail };
    }
    if (lifecycleState === "invoking_tauri_command") {
      return { status: m.status.running, detail: m.status.invokingDetail };
    }
    if (lifecycleState === "processing_local_runtime") {
      return { status: m.status.running, detail: m.status.processingDetail };
    }
    if (lifecycleState === "reading_result") {
      return { status: m.status.running, detail: m.status.readingDetail };
    }
    if (statusContext === "sample_success") {
      return { status: m.status.sampleSuccess, detail: m.status.sampleSuccessDetail };
    }
    if (statusContext === "sample_error") {
      return { status: m.status.sampleError, detail: m.status.sampleErrorDetail };
    }
    if (statusContext === "real_success") {
      return { status: m.status.completed, detail: m.status.completedDetail };
    }
    if (statusContext === "real_failed") {
      return {
        status: m.status.failed,
        detail: statusErrorDetail ?? m.status.failedMessage,
      };
    }
    if (statusContext === "read_failed") {
      return {
        status: m.status.failed,
        detail: statusErrorDetail ?? m.status.readFailedMessage,
      };
    }
    return { status: m.status.ready, detail: m.status.readyDetail };
  }, [lifecycleState, m, statusContext, statusErrorDetail]);

  const proofNote = useMemo(() => {
    if (proofStatus === "exported") {
      return m.advanced.proofDone;
    }
    if (proofStatus === "failed") {
      return proofErrorDetail ?? m.advanced.proofExportFailed;
    }
    if (!lastRealMode) {
      return m.advanced.proofUnavailable;
    }
    return m.advanced.proofReady;
  }, [lastRealMode, m, proofErrorDetail, proofStatus]);

  const applyResult = async (
    nextResult: BaseRunResultV1,
    outputDir: string,
    sourceMode: "real_tauri_local_text" | "real_tauri_local_file",
  ) => {
    setLifecycleState("reading_result");
    await wait(40);
    const lifecycle = createRunLifecycle(nextResult);
    setResult(nextResult);
    setEvidence(lifecycle.evidence);
    setLastOutputDir(outputDir);
    setOutputPlan(
      await baseBridgeClient.openOutputFolderPlan(outputDir).catch(async () => {
        return mockArtifactClient.openOutputFolderPlan(outputDir);
      }),
    );
    try {
      const lineageSnapshot = await baseBridgeClient.readLineageSnapshot();
      setLineage(lineageSnapshot);
      setRuntimeMode(baseBridgeClient.runtimeMode);
    } catch {
      setRuntimeMode(sampleRuntimeMode);
    }
    const successful = lifecycle.classification === "success";
    setLifecycleState(successful ? "success" : "failed");
    setStatusContext(successful ? "real_success" : "real_failed");
    setStatusErrorDetail(nextResult.error?.user_message ?? nextResult.error?.technical_detail_safe ?? null);
    setDisplayMode(sourceMode);
    setLastRealMode(sourceMode);
    setProofStatus("not_exported");
    setProofPath(null);
    setProofErrorDetail(null);
  };

  const loadSample = async (mode: "success" | "error") => {
    setLifecycleState("idle");
    setStatusErrorDetail(null);
    setProofStatus("not_exported");
    setProofPath(null);
    setProofErrorDetail(null);
    setRuntimeMode(mockArtifactClient.runtimeMode);
    if (mode === "success") {
      const payload = await mockArtifactClient.loadSampleSuccess();
      setResult(payload.result);
      setEvidence(payload.evidence);
      setOutputPlan(await mockArtifactClient.openOutputFolderPlan(payload.result.receipt.output_root));
      setDisplayMode("sample_success");
      setStatusContext("sample_success");
      return;
    }
    const payload = await mockArtifactClient.loadSampleError();
    setResult(payload.result);
    setEvidence(sampleErrorEvidence);
    setOutputPlan(await mockArtifactClient.openOutputFolderPlan(payload.result.receipt.output_root));
    setDisplayMode("sample_error");
    setStatusContext("sample_error");
  };

  const buildFailedResult = (requestId: string, message: string): BaseRunResultV1 => ({
    ...sampleErrorResult,
    request_id: requestId,
    error: {
      ...sampleErrorResult.error!,
      technical_detail_safe: message,
      user_message: message,
    },
  });

  const handleRunText = async () => {
    setStatusErrorDetail(null);
    setLifecycleState("preparing_request");
    await wait(40);
    setLifecycleState("invoking_tauri_command");
    try {
      await wait(40);
      setLifecycleState("processing_local_runtime");
      const nextResult = await baseBridgeClient.runLocalText(inlineText, TEXT_OUTPUT_DIR);
      await applyResult(nextResult, TEXT_OUTPUT_DIR, "real_tauri_local_text");
    } catch (error) {
      const message = error instanceof Error ? error.message : String(error);
      const failed = buildFailedResult("ui-real-run-text-failed", message);
      setResult(failed);
      setEvidence(buildEvidenceFromRunResult(failed));
      setLifecycleState("failed");
      setStatusContext("real_failed");
      setStatusErrorDetail(message);
      setDisplayMode("real_tauri_local_text");
      setLastRealMode("real_tauri_local_text");
      setProofStatus("not_exported");
      setProofPath(null);
      setProofErrorDetail(null);
    }
  };

  const handleRunFile = async () => {
    setStatusErrorDetail(null);
    setLifecycleState("preparing_request");
    await wait(40);
    setLifecycleState("invoking_tauri_command");
    try {
      await wait(40);
      setLifecycleState("processing_local_runtime");
      const nextResult = await baseBridgeClient.runLocalFile(inputPath, FILE_OUTPUT_DIR);
      await applyResult(nextResult, FILE_OUTPUT_DIR, "real_tauri_local_file");
    } catch (error) {
      const message = error instanceof Error ? error.message : String(error);
      const failed = buildFailedResult("ui-real-run-file-failed", message);
      setResult(failed);
      setEvidence(buildEvidenceFromRunResult(failed));
      setLifecycleState("failed");
      setStatusContext("real_failed");
      setStatusErrorDetail(message);
      setDisplayMode("real_tauri_local_file");
      setLastRealMode("real_tauri_local_file");
      setProofStatus("not_exported");
      setProofPath(null);
      setProofErrorDetail(null);
    }
  };

  const handleReadLatest = async () => {
    setStatusErrorDetail(null);
    setLifecycleState("reading_result");
    try {
      const nextResult = await baseBridgeClient.readRunResult(lastOutputDir);
      const sourceMode =
        displayMode === "real_tauri_local_file" ? "real_tauri_local_file" : "real_tauri_local_text";
      await applyResult(nextResult, lastOutputDir, sourceMode);
    } catch (error) {
      const message = error instanceof Error ? error.message : String(error);
      setLifecycleState("failed");
      setStatusContext("read_failed");
      setStatusErrorDetail(message);
    }
  };

  const handlePrimaryRun = async () => {
    if (inputMode === "file") {
      await handleRunFile();
      return;
    }
    await handleRunText();
  };

  const handleExportProof = async () => {
    if (!lastRealMode) {
      setProofStatus("failed");
      setProofErrorDetail(m.advanced.proofUnavailable);
      return;
    }
    const marker =
      result.normalized_text_preview.includes("ZEPHYR_BASE")
        ? result.normalized_text_preview
        : inlineText;
    const proof: InteractionProofV1 = {
      schema_version: 1,
      report_id: "zephyr.base.s10.window_interaction_proof.v1",
      proof_kind: "manual_window_click",
      marker,
      window_launched: baseBridgeClient.hasTauriInvoke(),
      user_clicked_run: true,
      ui_mode: lastRealMode,
      tauri_invoke_used: true,
      direct_python_call: false,
      network_call: false,
      run_result_path: `${PROOF_OUTPUT_DIR}/run_result.json`,
      normalized_preview_visible: true,
      evidence_visible: true,
      receipt_visible: true,
      usage_fact_visible: true,
      billing_semantics_displayed_false: result.usage_fact.billing_semantics === false,
      output_folder_plan_visible: true,
      error_panel_available: true,
      screenshot_path: null,
      notes: [
        "Visible window proof exported from the Base Tauri shell.",
        "This proof does not claim installer completeness or full release packaging.",
      ],
    };
    try {
      const exported = await baseBridgeClient.writeInteractionProof(
        PROOF_OUTPUT_DIR,
        proof,
        result,
      );
      setProofStatus("exported");
      setProofPath(exported.proof_path);
      setProofErrorDetail(null);
    } catch (error) {
      const message = error instanceof Error ? error.message : String(error);
      setProofStatus("failed");
      setProofErrorDetail(message);
    }
  };

  return (
    <AppShell>
      <InputCard
        inputMode={inputMode}
        inputPath={inputPath}
        inlineText={inlineText}
        onInputModeChange={setInputMode}
        onInputPathChange={setInputPath}
        onInlineTextChange={setInlineText}
        supportedFormats={[...SUPPORTED_FORMATS]}
      />
      <RunCard
        inputMode={inputMode}
        lifecycleState={lifecycleState}
        runtimeMode={runtimeMode}
        status={statusView.status}
        detail={statusView.detail}
        onRun={() => void handlePrimaryRun()}
        onReadLatest={() => void handleReadLatest()}
        isRunning={isRunning}
      />
      <UserResultCard
        result={result}
        evidence={evidence}
        outputPlan={outputPlan}
        lastOutputDir={lastOutputDir}
        onReadLatest={() => void handleReadLatest()}
      />
      <AdvancedDiagnostics
        result={result}
        evidence={evidence}
        lineage={lineage}
        runtimeMode={runtimeMode}
        proofStatus={proofStatus}
        proofPath={proofPath}
        proofNote={proofNote}
        proofEnabled={lastRealMode !== null}
        onExportProof={() => void handleExportProof()}
        onLoadSampleSuccess={() => void loadSample("success")}
        onLoadSampleError={() => void loadSample("error")}
      />
    </AppShell>
  );
}

export default function App() {
  return (
    <LanguageProvider>
      <BaseApp />
    </LanguageProvider>
  );
}
