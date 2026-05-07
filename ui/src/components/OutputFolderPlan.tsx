import type { OutputFolderPlan as OutputFolderPlanModel } from "../services/baseBridgeClient";

interface OutputFolderPlanProps {
  plan: OutputFolderPlanModel;
}

export function OutputFolderPlan({ plan }: OutputFolderPlanProps) {
  return (
    <section className="panel-card">
      <h2>Output folder plan</h2>
      <dl className="definition-grid compact-grid">
        <div>
          <dt>Action</dt>
          <dd>{plan.action}</dd>
        </div>
        <div>
          <dt>Output dir</dt>
          <dd>{plan.output_dir}</dd>
        </div>
        <div>
          <dt>Implemented</dt>
          <dd>{String(plan.implemented)}</dd>
        </div>
        <div className="full-span">
          <dt>Reason</dt>
          <dd>{plan.reason}</dd>
        </div>
      </dl>
    </section>
  );
}
