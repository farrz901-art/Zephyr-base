import type { LineageSnapshotV1, RuntimeModeSummary } from "../contracts/baseRunResult";

interface LineageStatusCardProps {
  lineage: LineageSnapshotV1;
  runtimeMode: RuntimeModeSummary;
}

export function LineageStatusCard({ lineage, runtimeMode }: LineageStatusCardProps) {
  const publicLineage = lineage.public_export_lineage as {
    zephyr_dev_source_sha?: string;
    p5_1_final_sha?: string;
  };
  return (
    <section className="panel-card wide-card">
      <h2>Lineage and runtime status</h2>
      <dl className="definition-grid compact-grid">
        <div>
          <dt>Zephyr-dev source SHA</dt>
          <dd>{publicLineage.zephyr_dev_source_sha ?? "unknown"}</dd>
        </div>
        <div>
          <dt>P5.1 baseline</dt>
          <dd>{publicLineage.p5_1_final_sha ?? "unknown"}</dd>
        </div>
        <div>
          <dt>Uses current Python environment</dt>
          <dd>{String(lineage.uses_current_python_environment)}</dd>
        </div>
        <div>
          <dt>Installer runtime complete</dt>
          <dd>{String(lineage.installer_runtime_complete)}</dd>
        </div>
        <div>
          <dt>Invoke mode</dt>
          <dd>{runtimeMode.mode}</dd>
        </div>
        <div>
          <dt>Tauri invoke E2E</dt>
          <dd>{String(runtimeMode.tauri_invoke_e2e_verified)}</dd>
        </div>
      </dl>
    </section>
  );
}
