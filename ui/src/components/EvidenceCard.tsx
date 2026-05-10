import type { BaseContentEvidenceV1 } from "../contracts/baseRunResult";
import { useLanguage } from "../i18n/useLanguage";

interface EvidenceCardProps {
  evidence: BaseContentEvidenceV1;
}

export function EvidenceCard({ evidence }: EvidenceCardProps) {
  const { messages: m } = useLanguage();

  return (
    <section className="panel-card nested-card">
      <h3>{m.result.evidenceTitle}</h3>
      <dl className="definition-grid compact-grid">
        <div>
          <dt>{m.result.evidenceKind}</dt>
          <dd>{evidence.evidence_kind}</dd>
        </div>
        <div>
          <dt>{m.result.evidenceCount}</dt>
          <dd>{evidence.elements_count ?? 0}</dd>
        </div>
        <div>
          <dt>{m.result.tokenFound}</dt>
          <dd>{String(evidence.token_marker_found ?? false)}</dd>
        </div>
        <div>
          <dt>{m.result.sourceKind}</dt>
          <dd>{evidence.source_kind ?? "local_artifact"}</dd>
        </div>
      </dl>
    </section>
  );
}
