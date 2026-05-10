import type { BaseRunResultV1 } from "../contracts/baseRunResult";
import { useLanguage } from "../i18n/useLanguage";

interface ResultSummaryProps {
  result: BaseRunResultV1;
}

export function ResultSummary({ result }: ResultSummaryProps) {
  const { messages: m } = useLanguage();

  return (
    <section className="panel-card nested-card">
      <h3>{m.result.summaryTitle}</h3>
      <dl className="definition-grid compact-grid">
        <div>
          <dt>{m.result.status}</dt>
          <dd>{result.status}</dd>
        </div>
        <div>
          <dt>{m.result.requestId}</dt>
          <dd>{result.request_id}</dd>
        </div>
        <div>
          <dt>{m.result.evidenceKind}</dt>
          <dd>{result.content_evidence_summary.evidence_kind}</dd>
        </div>
        <div>
          <dt>{m.result.outputFiles}</dt>
          <dd>{result.output_files.length}</dd>
        </div>
      </dl>
    </section>
  );
}
