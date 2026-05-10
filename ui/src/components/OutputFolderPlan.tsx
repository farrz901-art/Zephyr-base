import { useLanguage } from "../i18n/useLanguage";
import type { OutputFolderPlan as OutputFolderPlanModel } from "../services/baseBridgeClient";

interface OutputFolderPlanProps {
  plan: OutputFolderPlanModel;
}

export function OutputFolderPlan({ plan }: OutputFolderPlanProps) {
  const { messages: m } = useLanguage();

  return (
    <section className="panel-card nested-card">
      <h3>{m.result.outputTitle}</h3>
      <dl className="definition-grid compact-grid">
        <div>
          <dt>{m.result.outputDir}</dt>
          <dd>{plan.output_dir}</dd>
        </div>
        <div>
          <dt>{m.result.status}</dt>
          <dd>{String(plan.implemented)}</dd>
        </div>
        <div className="full-span">
          <dt>{m.result.outputReason}</dt>
          <dd>{plan.reason}</dd>
        </div>
      </dl>
    </section>
  );
}
