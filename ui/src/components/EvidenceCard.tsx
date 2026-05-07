import type { BaseContentEvidenceV1 } from "../contracts/baseRunResult";

interface EvidenceCardProps {
  evidence: BaseContentEvidenceV1;
}

export function EvidenceCard({ evidence }: EvidenceCardProps) {
  return (
    <section className="panel-card">
      <h2>Content evidence</h2>
      <dl className="definition-grid compact-grid">
        <div>
          <dt>Evidence kind</dt>
          <dd>{evidence.evidence_kind}</dd>
        </div>
        <div>
          <dt>Elements</dt>
          <dd>{evidence.elements_count ?? 0}</dd>
        </div>
        <div>
          <dt>Token marker found</dt>
          <dd>{String(evidence.token_marker_found ?? false)}</dd>
        </div>
        <div>
          <dt>Source kind</dt>
          <dd>{evidence.source_kind ?? "local artifact"}</dd>
        </div>
      </dl>
    </section>
  );
}
