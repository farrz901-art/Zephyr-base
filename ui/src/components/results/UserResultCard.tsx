import type { BaseContentEvidenceV1, BaseRunResultV1 } from "../../contracts/baseRunResult";
import { useLanguage } from "../../i18n/useLanguage";
import type { OutputFolderPlan as OutputFolderPlanModel } from "../../services/baseBridgeClient";
import { EvidenceCard } from "../EvidenceCard";
import { LocalOutputControls } from "../LocalOutputControls";
import { NormalizedTextPreview } from "../NormalizedTextPreview";
import { OutputFolderPlan } from "../OutputFolderPlan";
import { ResultSummary } from "../ResultSummary";

interface UserResultCardProps {
  result: BaseRunResultV1;
  evidence: BaseContentEvidenceV1;
  outputPlan: OutputFolderPlanModel;
  lastOutputDir: string;
  onReadLatest: () => void;
}

export function UserResultCard({
  result,
  evidence,
  outputPlan,
  lastOutputDir,
  onReadLatest,
}: UserResultCardProps) {
  const { messages: m } = useLanguage();
  const userFacts = [
    m.result.freeLocalFact,
    m.result.packagedRuntimeFact,
    m.result.noDevWorkspaceFact,
    m.result.noNetworkFact,
  ];

  return (
    <section className="panel-card wide-card">
      <div className="section-heading">
        <div>
          <p className="eyebrow">{m.result.title}</p>
          <h2>{m.result.subtitle}</h2>
        </div>
        <span className={`status-pill ${result.status === "success" ? "exported" : "failed"}`}>
          {result.status === "success" ? m.status.completed : m.status.failed}
        </span>
      </div>
      <p className="hero-copy">
        {result.status === "success" ? m.result.successBanner : m.result.failureBanner}
      </p>
      <div className="result-grid">
        <ResultSummary result={result} />
        <EvidenceCard evidence={evidence} />
        <OutputFolderPlan plan={outputPlan} />
        <LocalOutputControls
          lastOutputDir={lastOutputDir}
          onReadLatest={onReadLatest}
          onExportProof={() => undefined}
          proofEnabled={false}
          showProofAction={false}
        />
      </div>
      <ul className="fact-list">
        {userFacts.map((fact) => (
          <li key={fact}>{fact}</li>
        ))}
      </ul>
      <NormalizedTextPreview preview={result.normalized_text_preview} />
    </section>
  );
}
