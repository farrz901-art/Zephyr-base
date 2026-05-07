import type { RuntimeModeSummary } from "../contracts/baseRunResult";

interface ProgressPanelProps {
  status: string;
  detail: string;
  runtimeMode: RuntimeModeSummary;
}

export function ProgressPanel({ status, detail, runtimeMode }: ProgressPanelProps) {
  return (
    <section className="panel-card status-card">
      <div>
        <p className="eyebrow">Runtime status</p>
        <h2>{status}</h2>
      </div>
      <p className="panel-copy">{detail}</p>
      <dl className="definition-grid compact-grid">
        <div>
          <dt>Mode</dt>
          <dd>{runtimeMode.mode}</dd>
        </div>
        <div>
          <dt>Bundled adapter</dt>
          <dd>{String(runtimeMode.uses_bundled_adapter)}</dd>
        </div>
        <div>
          <dt>Tauri invoke ready</dt>
          <dd>{String(runtimeMode.tauriInvokeReady)}</dd>
        </div>
        <div>
          <dt>E2E verified</dt>
          <dd>{String(runtimeMode.tauriInvokeE2eVerified)}</dd>
        </div>
      </dl>
    </section>
  );
}
