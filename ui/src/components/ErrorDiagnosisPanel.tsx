import type { BaseErrorV1 } from "../contracts/baseRunResult";

interface ErrorDiagnosisPanelProps {
  error: BaseErrorV1 | null;
}

export function ErrorDiagnosisPanel({ error }: ErrorDiagnosisPanelProps) {
  return (
    <section className="panel-card error-card">
      <h2>Error diagnosis</h2>
      {error ? (
        <dl className="definition-grid compact-grid">
          <div>
            <dt>Error code</dt>
            <dd>{error.error_code}</dd>
          </div>
          <div>
            <dt>Category</dt>
            <dd>{error.category}</dd>
          </div>
          <div>
            <dt>User message</dt>
            <dd>{error.user_message}</dd>
          </div>
          <div>
            <dt>Secret safe</dt>
            <dd>{String(error.secret_safe)}</dd>
          </div>
          <div className="full-span">
            <dt>Technical detail</dt>
            <dd>{error.technical_detail_safe}</dd>
          </div>
        </dl>
      ) : (
        <p className="panel-copy">No active error. Sample success mode keeps this panel available for later Tauri runs.</p>
      )}
    </section>
  );
}
