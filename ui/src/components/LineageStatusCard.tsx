import type { LineageSnapshotV1, RuntimeModeSummary } from "../contracts/baseRunResult";
import { useLanguage } from "../i18n/useLanguage";

interface LineageStatusCardProps {
  lineage: LineageSnapshotV1;
  runtimeMode: RuntimeModeSummary;
}

export function LineageStatusCard({ lineage, runtimeMode }: LineageStatusCardProps) {
  const { messages: m } = useLanguage();
  const publicLineage = lineage.public_export_lineage as {
    zephyr_dev_source_sha?: string;
    p5_1_final_sha?: string;
  };

  return (
    <section className="panel-card wide-card nested-card">
      <h3>{m.advanced.lineageTitle}</h3>
      <dl className="definition-grid compact-grid">
        <div>
          <dt>{m.advanced.lineageSourceSha}</dt>
          <dd>{publicLineage.zephyr_dev_source_sha ?? "unknown"}</dd>
        </div>
        <div>
          <dt>{m.advanced.lineageBaseline}</dt>
          <dd>{publicLineage.p5_1_final_sha ?? "unknown"}</dd>
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
          <dt>{m.runtime.mode}</dt>
          <dd>{runtimeMode.mode}</dd>
        </div>
      </dl>
    </section>
  );
}
