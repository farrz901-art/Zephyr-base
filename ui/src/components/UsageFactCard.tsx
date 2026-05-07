import type { BaseUsageFactV1 } from "../contracts/baseRunResult";

interface UsageFactCardProps {
  usageFact: BaseUsageFactV1;
}

export function UsageFactCard({ usageFact }: UsageFactCardProps) {
  return (
    <section className="panel-card accent-card">
      <h2>Usage fact</h2>
      <dl className="definition-grid compact-grid">
        <div>
          <dt>Fact kind</dt>
          <dd>{usageFact.fact_kind}</dd>
        </div>
        <div>
          <dt>billing_semantics</dt>
          <dd>{String(usageFact.billing_semantics)}</dd>
        </div>
        <div>
          <dt>Input bytes</dt>
          <dd>{usageFact.input_bytes ?? 0}</dd>
        </div>
        <div>
          <dt>Output files</dt>
          <dd>{usageFact.output_files_count}</dd>
        </div>
      </dl>
      <p className="panel-copy">Base UI only displays technical usage facts. It is not a billing surface.</p>
    </section>
  );
}
