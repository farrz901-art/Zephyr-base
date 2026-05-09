import type { LineageSnapshotV1, RuntimeModeSummary } from "../contracts/baseRunResult";

interface RuntimePreflightCardProps {
  lineage: LineageSnapshotV1;
  runtimeMode: RuntimeModeSummary;
}

export function RuntimePreflightCard({ lineage, runtimeMode }: RuntimePreflightCardProps) {
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
          <dt>Managed runtime available</dt>
          <dd>{String(lineage.managed_runtime_available)}</dd>
        </div>
        <div>
          <dt>Managed runtime selected</dt>
          <dd>{String(lineage.managed_python_runtime_used)}</dd>
        </div>
        <div>
          <dt>Selected Python</dt>
          <dd>{lineage.selected_python_path}</dd>
        </div>
        <div>
          <dt>Current Python env</dt>
          <dd>{String(lineage.uses_current_python_environment)}</dd>
        </div>
        <div>
          <dt>Wheelhouse bundled</dt>
          <dd>{String(lineage.wheelhouse_bundled)}</dd>
        </div>
        <div>
          <dt>Install layout supported</dt>
          <dd>{String(lineage.install_layout_supported)}</dd>
        </div>
        <div>
          <dt>Installer built</dt>
          <dd>{String(lineage.installer_built)}</dd>
        </div>
        <div>
          <dt>Release created</dt>
          <dd>{String(lineage.release_created)}</dd>
        </div>
        <div>
          <dt>Clean machine runtime proven</dt>
          <dd>{String(lineage.clean_machine_runtime_proven)}</dd>
        </div>
        <div>
          <dt>Installer complete</dt>
          <dd>{String(lineage.installer_runtime_complete)}</dd>
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
