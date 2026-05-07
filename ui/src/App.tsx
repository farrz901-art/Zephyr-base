import { useEffect, useState } from "react";

import type { BaseContentEvidenceV1, BaseRunResultV1, LineageSnapshotV1, RuntimeModeSummary } from "./contracts/baseRunResult";
import { sampleErrorEvidence, sampleErrorResult } from "./fixtures/sampleErrorResult";
import {
  sampleLineageSnapshot,
  sampleRuntimeMode,
  sampleSuccessEvidence,
  sampleSuccessResult,
} from "./fixtures/sampleRunResult";
import { baseBridgeClient } from "./services/baseBridgeClient";
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
import { OutputFolderPlan } from "./components/OutputFolderPlan";

const SUPPORTED_FORMATS = [".txt", ".text", ".log", ".md", ".markdown"];

export default function App() {
  const [sampleMode, setSampleMode] = useState<"success" | "error">("success");
  const [status, setStatus] = useState("Idle");
  const [statusDetail, setStatusDetail] = useState(
    "UI shell is showing sample artifacts while Tauri invoke remains invoke-ready and window e2e is not yet verified.",
  );
  const [inputPath, setInputPath] = useState("E:/docs/example.md");
  const [inlineText, setInlineText] = useState("ZEPHYR_BASE_REAL_ADAPTER_MARKER_M3_S4_TEXT");
  const [result, setResult] = useState<BaseRunResultV1>(sampleSuccessResult);
  const [evidence, setEvidence] = useState<BaseContentEvidenceV1>(sampleSuccessEvidence);
  const [lineage, setLineage] = useState<LineageSnapshotV1>(sampleLineageSnapshot);
  const [runtimeMode, setRuntimeMode] = useState<RuntimeModeSummary>(sampleRuntimeMode);
  const [outputPlan, setOutputPlan] = useState({
    action: "open_output_folder_plan",
    output_dir: sampleSuccessResult.receipt.output_root,
    implemented: false,
    reason: "Output folder plan is displayed in the shell; native open behavior lands later.",
    requires_network: false,
    requires_p45_substrate: false,
    commercial_logic_allowed: false,
  });

  useEffect(() => {
    const loadLineage = async () => {
      const lineageSnapshot = await mockArtifactClient.readLineageSnapshot();
      setLineage(lineageSnapshot);
      setRuntimeMode(mockArtifactClient.runtimeMode);
    };
    void loadLineage();
  }, []);

  const loadSample = async (mode: "success" | "error") => {
    setSampleMode(mode);
    setStatus("Mock artifact mode");
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

  const handleInvokeReadyClick = async (mode: "file" | "text") => {
    setStatus("Invoke-ready only");
    try {
      if (mode === "file") {
        await baseBridgeClient.runLocalFile(inputPath, ".tmp/ui_shell_file");
      } else {
        await baseBridgeClient.runLocalText(inlineText, ".tmp/ui_shell_text");
      }
      setStatusDetail("Tauri invoke returned a result in the current desktop runtime.");
    } catch (error) {
      const message = error instanceof Error ? error.message : String(error);
      setStatusDetail(message);
      setResult(sampleErrorResult);
      setEvidence(sampleErrorEvidence);
    }
  };

  return (
    <main className="app-shell">
      <header className="top-band">
        <p className="eyebrow">Base public artifact shell</p>
        <div className="top-band-meta">
          <span>Local runtime first slice</span>
          <span>Installer runtime not complete</span>
          <span>Free desktop product</span>
        </div>
      </header>
      <Welcome />
      <section className="action-grid">
        <FileDropZone inputPath={inputPath} onInputPathChange={setInputPath} supportedFormats={SUPPORTED_FORMATS} />
        <TextInputPanel inlineText={inlineText} onInlineTextChange={setInlineText} />
      </section>
      <section className="toolbar-card">
        <div className="toolbar-row">
          <button className="primary-button" type="button" onClick={() => void loadSample("success")}>
            Load sample success result
          </button>
          <button className="secondary-button" type="button" onClick={() => void loadSample("error")}>
            Load sample error result
          </button>
        </div>
        <div className="toolbar-row">
          <button className="ghost-button" type="button" onClick={() => void handleInvokeReadyClick("file")}>
            Invoke-ready local file action
          </button>
          <button className="ghost-button" type="button" onClick={() => void handleInvokeReadyClick("text")}>
            Invoke-ready local text action
          </button>
        </div>
        <p className="toolbar-note">
          Tauri invoke is prepared for bundled adapter calls, but S8 still does not claim full desktop window e2e verification.
        </p>
      </section>
      <ProgressPanel status={status} detail={statusDetail} runtimeMode={runtimeMode} />
      <section className="result-grid">
        <ResultSummary result={result} />
        <UsageFactCard usageFact={result.usage_fact} />
        <ReceiptCard receipt={result.receipt} />
        <EvidenceCard evidence={evidence} />
        <ErrorDiagnosisPanel error={result.error} />
        <OutputFolderPlan plan={outputPlan} />
      </section>
      <NormalizedTextPreview preview={result.normalized_text_preview} />
      <LineageStatusCard lineage={lineage} runtimeMode={runtimeMode} />
      <footer className="footer-note">
        Sample mode selected: <strong>{sampleMode}</strong>. Supported formats remain limited to {SUPPORTED_FORMATS.join(", ")}.
      </footer>
    </main>
  );
}

