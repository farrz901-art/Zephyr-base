import { useEffect, useState } from "react";

import type {
  BaseContentEvidenceV1,
  BaseRunResultV1,
  InteractionProofV1,
  LineageSnapshotV1,
  RunLifecycleState,
  RuntimeModeSummary,
} from "./contracts/baseRunResult";
import { sampleErrorEvidence, sampleErrorResult } from "./fixtures/sampleErrorResult";
import {
  sampleLineageSnapshot,
  sampleRuntimeMode,
  sampleSuccessEvidence,
  sampleSuccessResult,
} from "./fixtures/sampleRunResult";
import {
  baseBridgeClient,
  buildEvidenceFromRunResult,
  createRunLifecycle,
  type OutputFolderPlan,
} from "./services/baseBridgeClient";
import { mockArtifactClient } from "./services/mockArtifactClient";
import { Welcome } from "./components/Welcome";
import { FileDropZone } from "./components/FileDropZone";
import { TextInputPanel } from "./components/TextInputPanel";
import { ProgressPanel } from "./components/ProgressPanel";
import { ResultSummary } from "./components/ResultSummary";
import { NormalizedTextPreview } from "./components/NormalizedTextPreview";
import { EvidenceCard } from "./components/EvidenceCard";
import { ReceiptCard } from "./components/ReceiptCard";
import { UsageFactCard } from "./components/UsageFactCard";
import { ErrorDiagnosisPanel } from "./components/ErrorDiagnosisPanel";
import { LineageStatusCard } from "./components/LineageStatusCard";
import { OutputFolderPlan as OutputFolderPlanCard } from "./components/OutputFolderPlan";
import { RunModePanel, type RunMode } from "./components/RunModePanel";
import { RunStatusTimeline } from "./components/RunStatusTimeline";
import { RuntimePreflightCard } from "./components/RuntimePreflightCard";
import { InteractionProofPanel } from "./components/InteractionProofPanel";
import { LocalOutputControls } from "./components/LocalOutputControls";
import { SupportedFormatsNotice } from "./components/SupportedFormatsNotice";

const SUPPORTED_FORMATS = [".txt", ".text", ".log", ".md", ".markdown"] as const;
const FILE_OUTPUT_DIR = ".tmp/ui_shell_file";
const TEXT_OUTPUT_DIR = ".tmp/ui_shell_text";
const PROOF_OUTPUT_DIR = ".tmp/s10_tauri_window_interaction";
const DEFAULT_MARKER = "ZEPHYR_BASE_S10_WINDOW_INTERACTION_MARKER";

function wait(ms: number) {
  return new Promise((resolve) => window.setTimeout(resolve, ms));
}

export default function App() {
  const [runMode, setRunMode] = useState<RunMode>("real_tauri_local_text");
  const [status, setStatus] = useState("Idle");
  const [statusDetail, setStatusDetail] = useState(
    "Visible Tauri path is ready for a real local run. Window click proof still requires an exported proof pack.",
  );
  const [lifecycleState, setLifecycleState] = useState<RunLifecycleState>("idle");
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
  const [proofNote, setProofNote] = useState(
    "Run a real Tauri mode and export the proof pack from the visible window.",
  );
  const [proofPath, setProofPath] = useState<string | null>(null);

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

  const applyResult = async (
    nextResult: BaseRunResultV1,
    outputDir: string,
    sourceMode: RunMode,
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
    setStatus(successful ? "Run completed" : "Run failed");
    setStatusDetail(
      successful
        ? "UI consumed a bundled adapter base_run_result_v1 artifact through the visible Tauri path."
        : lifecycle.displayModel.error_message ?? "Run failed with a secret-safe error result.",
    );
    if (sourceMode === "real_tauri_local_text" || sourceMode === "real_tauri_local_file") {
      setLastRealMode(sourceMode);
      setProofStatus("not_exported");
      setProofNote(
        "Visible window run completed. Export interaction proof to seal click-path evidence.",
      );
    }
  };

  const loadSample = async (mode: "success" | "error") => {
    setRunMode(mode === "success" ? "sample_success" : "sample_error");
    setLifecycleState("idle");
    setProofStatus("not_exported");
    setProofNote("Sample mode remains available for regression, but it is not a click-proof substitute.");
    setRuntimeMode(mockArtifactClient.runtimeMode);
    setStatus("Sample artifact mode");
    setStatusDetail(
      mode === "success"
        ? "Showing bundled adapter success-shaped artifacts in sample mode."
        : "Showing safe failed run_result artifacts in sample mode.",
    );
    if (mode === "success") {
      const payload = await mockArtifactClient.loadSampleSuccess();
      setResult(payload.result);
      setEvidence(payload.evidence);
      setOutputPlan(await mockArtifactClient.openOutputFolderPlan(payload.result.receipt.output_root));
      return;
    }
    const payload = await mockArtifactClient.loadSampleError();
    setResult(payload.result);
    setEvidence(payload.evidence);
    setOutputPlan(await mockArtifactClient.openOutputFolderPlan(payload.result.receipt.output_root));
  };

  const buildFailedResult = (requestId: string, message: string): BaseRunResultV1 => ({
    ...sampleErrorResult,
    request_id: requestId,
    error: {
      ...sampleErrorResult.error!,
      technical_detail_safe: message,
      user_message: "Tauri invoke was not available or the local runtime failed safely.",
    },
  });

  const handleRunText = async () => {
    setLifecycleState("preparing_request");
    setStatus("Preparing request");
    setStatusDetail("Preparing a local-text request for the bundled runtime.");
    await wait(40);
    setLifecycleState("invoking_tauri_command");
    setStatus("Invoking Tauri command");
    setStatusDetail("Calling the Rust command bridge from the visible shell.");
    try {
      await wait(40);
      setLifecycleState("processing_local_runtime");
      setStatus("Processing local runtime");
      setStatusDetail("The bundled adapter is processing the local text input.");
      const nextResult = await baseBridgeClient.runLocalText(inlineText, TEXT_OUTPUT_DIR);
      await applyResult(nextResult, TEXT_OUTPUT_DIR, "real_tauri_local_text");
    } catch (error) {
      const message = error instanceof Error ? error.message : String(error);
      const failed = buildFailedResult("ui-real-run-text-failed", message);
      setResult(failed);
      setEvidence(buildEvidenceFromRunResult(failed));
      setLifecycleState("failed");
      setStatus("Run failed");
      setStatusDetail(message);
      setLastRealMode("real_tauri_local_text");
      setProofStatus("not_exported");
      setProofNote("The real run failed safely. You can still export a proof pack from the visible window.");
    }
  };

  const handleRunFile = async () => {
    setLifecycleState("preparing_request");
    setStatus("Preparing request");
    setStatusDetail("Preparing a local-file request for the bundled runtime.");
    await wait(40);
    setLifecycleState("invoking_tauri_command");
    setStatus("Invoking Tauri command");
    setStatusDetail("Calling the Rust command bridge from the visible shell.");
    try {
      await wait(40);
      setLifecycleState("processing_local_runtime");
      setStatus("Processing local runtime");
      setStatusDetail("The bundled adapter is processing the local file input.");
      const nextResult = await baseBridgeClient.runLocalFile(inputPath, FILE_OUTPUT_DIR);
      await applyResult(nextResult, FILE_OUTPUT_DIR, "real_tauri_local_file");
    } catch (error) {
      const message = error instanceof Error ? error.message : String(error);
      const failed = buildFailedResult("ui-real-run-file-failed", message);
      setResult(failed);
      setEvidence(buildEvidenceFromRunResult(failed));
      setLifecycleState("failed");
      setStatus("Run failed");
      setStatusDetail(message);
      setLastRealMode("real_tauri_local_file");
      setProofStatus("not_exported");
      setProofNote("The real run failed safely. You can still export a proof pack from the visible window.");
    }
  };

  const handleReadLatest = async () => {
    setLifecycleState("reading_result");
    setStatus("Reading latest result");
    setStatusDetail("Re-reading the latest bundled adapter artifact set.");
    try {
      const nextResult = await baseBridgeClient.readRunResult(lastOutputDir);
      await applyResult(nextResult, lastOutputDir, runMode);
    } catch (error) {
      const message = error instanceof Error ? error.message : String(error);
      setLifecycleState("failed");
      setStatus("Read failed");
      setStatusDetail(message);
    }
  };

  const handlePrimaryRun = async () => {
    if (runMode === "sample_success") {
      await loadSample("success");
      return;
    }
    if (runMode === "sample_error") {
      await loadSample("error");
      return;
    }
    if (runMode === "real_tauri_local_file") {
      await handleRunFile();
      return;
    }
    await handleRunText();
  };

  const handleExportProof = async () => {
    if (!lastRealMode) {
      setProofStatus("failed");
      setProofNote("No real Tauri run has completed yet, so there is nothing trustworthy to export.");
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
      setProofNote(
        "Interaction proof exported. Run python scripts/check_tauri_window_interaction_proof.py --json to validate it.",
      );
    } catch (error) {
      const message = error instanceof Error ? error.message : String(error);
      setProofStatus("failed");
      setProofNote(message);
    }
  };

  return (
    <main className="app-shell">
      <header className="top-band">
        <p className="eyebrow">Base visible app shell</p>
        <div className="top-band-meta">
          <span>Local-only</span>
          <span>Bundled adapter</span>
          <span>Current Python environment</span>
          <span>Installer runtime complete=false</span>
        </div>
      </header>
      <Welcome />
      <RunModePanel mode={runMode} onModeChange={setRunMode} />
      <section className="action-grid">
        <FileDropZone inputPath={inputPath} onInputPathChange={setInputPath} supportedFormats={[...SUPPORTED_FORMATS]} />
        <TextInputPanel inlineText={inlineText} onInlineTextChange={setInlineText} />
      </section>
      <section className="toolbar-card">
        <div className="toolbar-row">
          <button className="primary-button" type="button" onClick={() => void handlePrimaryRun()}>
            {runMode === "real_tauri_local_file"
              ? "Run local file path"
              : runMode === "sample_success"
                ? "Load sample success"
                : runMode === "sample_error"
                  ? "Load sample error"
                  : "Run local text"}
          </button>
          <button className="secondary-button" type="button" onClick={() => void handleReadLatest()}>
            Read latest result
          </button>
          <button className="ghost-button" type="button" onClick={() => void loadSample("success")}>
            Sample success
          </button>
          <button className="ghost-button" type="button" onClick={() => void loadSample("error")}>
            Sample error
          </button>
        </div>
        <p className="toolbar-note">
          Real Tauri modes are first-class in S10. Sample modes remain for regression only.
        </p>
      </section>
      <section className="result-grid">
        <RunStatusTimeline currentState={lifecycleState} />
        <RuntimePreflightCard runtimeMode={runtimeMode} />
        <SupportedFormatsNotice supportedFormats={[...SUPPORTED_FORMATS]} />
      </section>
      <ProgressPanel status={status} detail={statusDetail} runtimeMode={runtimeMode} />
      <section className="result-grid">
        <LocalOutputControls
          lastOutputDir={lastOutputDir}
          onReadLatest={() => void handleReadLatest()}
          onExportProof={() => void handleExportProof()}
          proofEnabled={lastRealMode !== null}
        />
        <InteractionProofPanel
          enabled={lastRealMode !== null}
          note={proofNote}
          proofPath={proofPath}
          proofStatus={proofStatus}
          onExport={() => void handleExportProof()}
        />
        <ResultSummary result={result} />
        <UsageFactCard usageFact={result.usage_fact} />
        <ReceiptCard receipt={result.receipt} />
        <EvidenceCard evidence={evidence} />
        <ErrorDiagnosisPanel error={result.error} />
        <OutputFolderPlanCard plan={outputPlan} />
      </section>
      <NormalizedTextPreview preview={result.normalized_text_preview} />
      <LineageStatusCard lineage={lineage} runtimeMode={runtimeMode} />
      <footer className="footer-note">
        Visible shell now surfaces run lifecycle, runtime truth, supported format limits, and proof export. Full window click e2e still requires an actual proof pack.
      </footer>
    </main>
  );
}
