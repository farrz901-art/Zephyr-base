import type {
  BaseContentEvidenceV1,
  BaseRunResultV1,
  LineageSnapshotV1,
  RuntimeModeSummary,
} from "../../contracts/baseRunResult";
import { useLanguage } from "../../i18n/useLanguage";
import { ErrorDiagnosisPanel } from "../ErrorDiagnosisPanel";
import { InteractionProofPanel } from "../InteractionProofPanel";
import { LineageStatusCard } from "../LineageStatusCard";
import { ReceiptCard } from "../ReceiptCard";
import { RuntimePreflightCard } from "../RuntimePreflightCard";
import { UsageFactCard } from "../UsageFactCard";

interface AdvancedDiagnosticsProps {
  result: BaseRunResultV1;
  evidence: BaseContentEvidenceV1;
  lineage: LineageSnapshotV1;
  runtimeMode: RuntimeModeSummary;
  proofStatus: "not_exported" | "exported" | "failed";
  proofPath: string | null;
  proofNote: string;
  proofEnabled: boolean;
  onExportProof: () => void;
  onLoadSampleSuccess: () => void;
  onLoadSampleError: () => void;
}

export function AdvancedDiagnostics({
  result,
  evidence,
  lineage,
  runtimeMode,
  proofStatus,
  proofPath,
  proofNote,
  proofEnabled,
  onExportProof,
  onLoadSampleSuccess,
  onLoadSampleError,
}: AdvancedDiagnosticsProps) {
  const { messages: m } = useLanguage();

  return (
    <details className="panel-card advanced-diagnostics">
      <summary>
        <span>{m.advanced.summary}</span>
      </summary>
      <div className="advanced-body">
        <p className="panel-copy">{m.advanced.subtitle}</p>
        <section className="panel-card nested-card">
          <p className="eyebrow">{m.advanced.devTools}</p>
          <div className="toolbar-row">
            <button className="ghost-button" type="button" onClick={onLoadSampleSuccess}>
              {m.advanced.sampleSuccess}
            </button>
            <button className="ghost-button" type="button" onClick={onLoadSampleError}>
              {m.advanced.sampleError}
            </button>
          </div>
        </section>
        <div className="result-grid">
          <ReceiptCard receipt={result.receipt} />
          <UsageFactCard usageFact={result.usage_fact} />
          <ErrorDiagnosisPanel error={result.error} />
          <InteractionProofPanel
            enabled={proofEnabled}
            note={proofNote}
            proofPath={proofPath}
            proofStatus={proofStatus}
            onExport={onExportProof}
          />
          <RuntimePreflightCard lineage={lineage} runtimeMode={runtimeMode} />
          <LineageStatusCard lineage={lineage} runtimeMode={runtimeMode} />
        </div>
        <section className="panel-card nested-card">
          <p className="eyebrow">{m.advanced.rawJsonTitle}</p>
          <div className="result-grid">
            <div>
              <h3>{m.advanced.resultJson}</h3>
              <pre className="preview-surface json-surface">{JSON.stringify(result, null, 2)}</pre>
            </div>
            <div>
              <h3>{m.advanced.usageJson}</h3>
              <pre className="preview-surface json-surface">
                {JSON.stringify(result.usage_fact, null, 2)}
              </pre>
            </div>
            <div>
              <h3>{m.advanced.receiptJson}</h3>
              <pre className="preview-surface json-surface">
                {JSON.stringify(result.receipt, null, 2)}
              </pre>
            </div>
            <div>
              <h3>{m.result.evidenceTitle}</h3>
              <pre className="preview-surface json-surface">
                {JSON.stringify(evidence, null, 2)}
              </pre>
            </div>
          </div>
        </section>
      </div>
    </details>
  );
}
