import type { BaseUsageFactV1 } from "../contracts/baseRunResult";
import { useLanguage } from "../i18n/useLanguage";

interface UsageFactCardProps {
  usageFact: BaseUsageFactV1;
}

export function UsageFactCard({ usageFact }: UsageFactCardProps) {
  const { messages: m } = useLanguage();

  return (
    <section className="panel-card accent-card nested-card">
      <h3>{m.advanced.usageTitle}</h3>
      <dl className="definition-grid compact-grid">
        <div>
          <dt>{m.advanced.usageKind}</dt>
          <dd>{usageFact.fact_kind}</dd>
        </div>
        <div>
          <dt>{m.advanced.usageBilling}</dt>
          <dd>{String(usageFact.billing_semantics)}</dd>
        </div>
        <div>
          <dt>{m.advanced.usageInputBytes}</dt>
          <dd>{usageFact.input_bytes ?? 0}</dd>
        </div>
        <div>
          <dt>{m.advanced.usageOutputFiles}</dt>
          <dd>{usageFact.output_files_count}</dd>
        </div>
      </dl>
      <p className="panel-copy">{m.advanced.rawUsageNote}</p>
    </section>
  );
}
