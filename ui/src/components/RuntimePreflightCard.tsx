import type { LineageSnapshotV1, RuntimeModeSummary } from "../contracts/baseRunResult";
import { useLanguage } from "../i18n/useLanguage";

interface RuntimePreflightCardProps {
  lineage: LineageSnapshotV1;
  runtimeMode: RuntimeModeSummary;
}

export function RuntimePreflightCard({ lineage, runtimeMode }: RuntimePreflightCardProps) {
  const { messages: m } = useLanguage();

  return (
    <section className="panel-card accent-card nested-card">
      <p className="eyebrow">{m.runtime.title}</p>
      <h3>{m.runtime.subtitle}</h3>
      <dl className="definition-grid compact-grid">
        <div>
          <dt>{m.runtime.localOnly}</dt>
          <dd>{m.common.trueLabel}</dd>
        </div>
        <div>
          <dt>{m.runtime.bundledAdapter}</dt>
          <dd>{String(runtimeMode.uses_bundled_adapter)}</dd>
        </div>
        <div>
          <dt>{m.runtime.managedRuntimeAvailable}</dt>
          <dd>{String(lineage.managed_runtime_available)}</dd>
        </div>
        <div>
          <dt>{m.runtime.managedRuntimeSelected}</dt>
          <dd>{String(lineage.managed_python_runtime_used)}</dd>
        </div>
        <div>
          <dt>{m.runtime.selectedPython}</dt>
          <dd>{lineage.selected_python_path}</dd>
        </div>
        <div>
          <dt>{m.runtime.currentPythonEnv}</dt>
          <dd>{String(lineage.uses_current_python_environment)}</dd>
        </div>
        <div>
          <dt>{m.runtime.wheelhouseBundled}</dt>
          <dd>{String(lineage.wheelhouse_bundled)}</dd>
        </div>
        <div>
          <dt>{m.runtime.installLayoutSupported}</dt>
          <dd>{String(lineage.install_layout_supported)}</dd>
        </div>
        <div>
          <dt>{m.runtime.installerBuilt}</dt>
          <dd>{String(lineage.installer_built)}</dd>
        </div>
        <div>
          <dt>{m.runtime.releaseCreated}</dt>
          <dd>{String(lineage.release_created)}</dd>
        </div>
        <div>
          <dt>{m.runtime.cleanMachineProven}</dt>
          <dd>{String(lineage.clean_machine_runtime_proven)}</dd>
        </div>
        <div>
          <dt>{m.runtime.installerComplete}</dt>
          <dd>{String(lineage.installer_runtime_complete)}</dd>
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
