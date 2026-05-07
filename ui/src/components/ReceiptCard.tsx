import type { BaseReceiptViewV1 } from "../contracts/baseRunResult";

interface ReceiptCardProps {
  receipt: BaseReceiptViewV1;
}

export function ReceiptCard({ receipt }: ReceiptCardProps) {
  return (
    <section className="panel-card">
      <h2>Receipt</h2>
      <dl className="definition-grid compact-grid">
        <div>
          <dt>Run ID</dt>
          <dd>{receipt.run_id}</dd>
        </div>
        <div>
          <dt>Outcome</dt>
          <dd>{receipt.delivery_outcome}</dd>
        </div>
        <div>
          <dt>Output root</dt>
          <dd>{receipt.output_root}</dd>
        </div>
        <div>
          <dt>Created by</dt>
          <dd>{receipt.created_by}</dd>
        </div>
      </dl>
    </section>
  );
}
