import type { RuntimeModeSummary } from "../contracts/baseRunResult";

interface RuntimePreflightCardProps {
  runtimeMode: RuntimeModeSummary;
}

export function RuntimePreflightCard({ runtimeMode }: RuntimePreflightCardProps) {
  return (
    <section className="panel-card accent-card">
      <p className="eyebrow">Runtime truth</p>
      <h2>Preflight before local processing</h2>
      <dl className="definition-grid compact-grid">
        <div>
          <dt>Local-only</dt>
          <dd>True</dd>
        </div>
        <div>
          <dt>Bundled adapter</dt>
          <dd>{String(runtimeMode.uses_bundled_adapter)}</dd>
        </div>
        <div>
          <dt>Current Python env</dt>
          <dd>{String(runtimeMode.uses_current_python_environment)}</dd>
        </div>
        <div>
          <dt>Installer complete</dt>
          <dd>{String(runtimeMode.installer_runtime_complete)}</dd>
        </div>
        <div>
          <dt>Tauri invoke ready</dt>
          <dd>{String(runtimeMode.tauri_invoke_ready)}</dd>
        </div>
        <div>
          <dt>Window click e2e</dt>
          <dd>{String(runtimeMode.tauri_invoke_e2e_verified)}</dd>
        </div>
      </dl>
    </section>
  );
}
