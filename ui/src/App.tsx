import { useEffect, useState } from "react";

import type {
  BaseContentEvidenceV1,
  BaseRunResultV1,
  LineageSnapshotV1,
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

const SUPPORTED_FORMATS = [".txt", ".text", ".log", ".md", ".markdown"];
const FILE_OUTPUT_DIR = ".tmp/ui_shell_file";
const TEXT_OUTPUT_DIR = ".tmp/ui_shell_text";

export default function App() {
  const [sampleMode, setSampleMode] = useState<"success" | "error">("success");
  const [status, setStatus] = useState("Idle");
  const [statusDetail, setStatusDetail] = useState(
    "Visible shell is launch-ready for real Tauri invoke, while full window click e2e remains a later proof step.",
  );
  const [inputPath, setInputPath] = useState("tests/fixtures/real_adapter_sample_input.txt");
  const [inlineText, setInlineText] = useState("ZEPHYR_BASE_S9_TAURI_APP_PATH_MARKER");
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

  const applyResult = async (nextResult: BaseRunResultV1, outputDir: string) => {
    const lifecycle = createRunLifecycle(nextResult);
    setResult(nextResult);
    setEvidence(lifecycle.evidence);
    setLastOutputDir(outputDir);
    setOutputPlan(await baseBridgeClient.openOutputFolderPlan(outputDir).catch(async () => {
      return mockArtifactClient.openOutputFolderPlan(outputDir);
    }));
    try {
      const lineageSnapshot = await baseBridgeClient.readLineageSnapshot();
      setLineage(lineageSnapshot);
      setRuntimeMode(baseBridgeClient.runtimeMode);
    } catch {
      setRuntimeMode(sampleRuntimeMode);
    }
    setStatus(lifecycle.classification === "success" ? "Run completed" : "Run failed");
    setStatusDetail(
      lifecycle.classification === "success"
        ? "UI consumed a real base_run_result_v1 artifact from the local bundled adapter path."
        : lifecycle.displayModel.error_message ?? "Run failed with a secret-safe error result.",
    );
  };

  const loadSample = async (mode: "success" | "error") => {
    setSampleMode(mode);
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

  const handleRunText = async () => {
    setStatus("Running local text");
    setStatusDetail("Invoking the bundled adapter through the Rust/Tauri command bridge.");
    try {
      const nextResult = await baseBridgeClient.runLocalText(inlineText, TEXT_OUTPUT_DIR);
      await applyResult(nextResult, TEXT_OUTPUT_DIR);
    } catch (error) {
      const message = error instanceof Error ? error.message : String(error);
      const failed = {
        ...sampleErrorResult,
        request_id: "ui-real-run-text-failed",
        error: {
          ...sampleErrorResult.error!,
          technical_detail_safe: message,
          user_message: "Tauri invoke was not available or the local runtime failed safely.",
        },
      };
      setResult(failed);
      setEvidence(buildEvidenceFromRunResult(failed));
      setStatus("Run failed");
      setStatusDetail(message);
    }
  };

  const handleRunFile = async () => {
    setStatus("Running local file");
    setStatusDetail("Invoking the bundled adapter through the Rust/Tauri command bridge.");
    try {
      const nextResult = await baseBridgeClient.runLocalFile(inputPath, FILE_OUTPUT_DIR);
      await applyResult(nextResult, FILE_OUTPUT_DIR);
    } catch (error) {
      const message = error instanceof Error ? error.message : String(error);
      const failed = {
        ...sampleErrorResult,
        request_id: "ui-real-run-file-failed",
        error: {
          ...sampleErrorResult.error!,
          technical_detail_safe: message,
          user_message: "Tauri invoke was not available or the local runtime failed safely.",
        },
      };
      setResult(failed);
      setEvidence(buildEvidenceFromRunResult(failed));
      setStatus("Run failed");
      setStatusDetail(message);
    }
  };

  const handleReadLatest = async () => {
    setStatus("Reading latest result");
    try {
      const nextResult = await baseBridgeClient.readRunResult(lastOutputDir);
      await applyResult(nextResult, lastOutputDir);
    } catch (error) {
      const message = error instanceof Error ? error.message : String(error);
      setStatus("Read failed");
      setStatusDetail(message);
    }
  };

  return (
    <main className="app-shell">
      <header className="top-band">
        <p className="eyebrow">Base visible app shell</p>
        <div className="top-band-meta">
          <span>Local-only</span>
          <span>Tauri invoke dev mode</span>
          <span>Installer runtime complete=false</span>
        </div>
      </header>
      <Welcome />
      <section className="action-grid">
        <FileDropZone inputPath={inputPath} onInputPathChange={setInputPath} supportedFormats={SUPPORTED_FORMATS} />
        <TextInputPanel inlineText={inlineText} onInlineTextChange={setInlineText} />
      </section>
      <section className="toolbar-card">
        <div className="toolbar-row">
          <button className="primary-button" type="button" onClick={() => void handleRunText()}>
            Run local text
          </button>
          <button className="primary-button" type="button" onClick={() => void handleRunFile()}>
            Run local file path
          </button>
          <button className="secondary-button" type="button" onClick={() => void handleReadLatest()}>
            Read latest result
          </button>
        </div>
        <div className="toolbar-row">
          <button className="ghost-button" type="button" onClick={() => void loadSample("success")}>
            Load sample success result
          </button>
          <button className="ghost-button" type="button" onClick={() => void loadSample("error")}>
            Load sample error result
          </button>
        </div>
        <p className="toolbar-note">
          Supported formats remain limited to {SUPPORTED_FORMATS.join(", ")}. This shell does not claim pdf, docx, image, web, or cloud support.
        </p>
      </section>
      <ProgressPanel status={status} detail={statusDetail} runtimeMode={runtimeMode} />
      <section className="result-grid">
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
        Sample mode retained for regression, but real local run controls are the visible path in S9. Last output dir: <strong>{lastOutputDir}</strong>.
      </footer>
    </main>
  );
}
