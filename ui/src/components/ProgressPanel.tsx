import type { RuntimeModeSummary } from "../contracts/baseRunResult";
import { useLanguage } from "../i18n/useLanguage";

interface ProgressPanelProps {
  status: string;
  detail: string;
  runtimeMode: RuntimeModeSummary;
}

export function ProgressPanel({ status, detail, runtimeMode }: ProgressPanelProps) {
  const { messages: m } = useLanguage();

  return (
    <section className="panel-card status-card">
      <div>
        <p className="eyebrow">{m.status.runningSummary}</p>
        <h2>{status}</h2>
      </div>
      <p className="panel-copy">{detail}</p>
      <dl className="definition-grid compact-grid">
        <div>
          <dt>{m.runtime.mode}</dt>
          <dd>{runtimeMode.mode}</dd>
        </div>
        <div>
          <dt>{m.runtime.bundledAdapter}</dt>
          <dd>{String(runtimeMode.uses_bundled_adapter)}</dd>
        </div>
        <div>
          <dt>{m.runtime.invokeReady}</dt>
          <dd>{String(runtimeMode.tauri_invoke_ready)}</dd>
        </div>
        <div>
          <dt>{m.runtime.invokeE2E}</dt>
          <dd>{String(runtimeMode.tauri_invoke_e2e_verified)}</dd>
        </div>
      </dl>
    </section>
  );
}
