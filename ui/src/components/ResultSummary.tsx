import type { BaseRunResultV1 } from "../contracts/baseRunResult";

interface ResultSummaryProps {
  result: BaseRunResultV1;
}

export function ResultSummary({ result }: ResultSummaryProps) {
  return (
    <section className="panel-card">
      <h2>Result summary</h2>
      <dl className="definition-grid compact-grid">
        <div>
          <dt>Status</dt>
          <dd>{result.status}</dd>
        </div>
        <div>
          <dt>Request ID</dt>
          <dd>{result.request_id}</dd>
        </div>
        <div>
          <dt>Evidence kind</dt>
          <dd>{result.content_evidence_summary.evidence_kind}</dd>
        </div>
        <div>
          <dt>Output files</dt>
          <dd>{result.output_files.length}</dd>
        </div>
      </dl>
    </section>
  );
}
