import type { BaseErrorV1 } from "../contracts/baseRunResult";
import { useLanguage } from "../i18n/useLanguage";

interface ErrorDiagnosisPanelProps {
  error: BaseErrorV1 | null;
}

export function ErrorDiagnosisPanel({ error }: ErrorDiagnosisPanelProps) {
  const { messages: m } = useLanguage();

  return (
    <section className="panel-card error-card nested-card">
      <h3>{m.advanced.errorTitle}</h3>
      {error ? (
        <dl className="definition-grid compact-grid">
          <div>
            <dt>{m.advanced.errorCode}</dt>
            <dd>{error.error_code}</dd>
          </div>
          <div>
            <dt>{m.advanced.errorCategory}</dt>
            <dd>{error.category}</dd>
          </div>
          <div>
            <dt>{m.advanced.errorMessage}</dt>
            <dd>{error.user_message}</dd>
          </div>
          <div>
            <dt>{m.advanced.errorSecretSafe}</dt>
            <dd>{String(error.secret_safe)}</dd>
          </div>
          <div className="full-span">
            <dt>{m.advanced.errorTechnical}</dt>
            <dd>{error.technical_detail_safe}</dd>
          </div>
        </dl>
      ) : (
        <p className="panel-copy">{m.advanced.noError}</p>
      )}
    </section>
  );
}
