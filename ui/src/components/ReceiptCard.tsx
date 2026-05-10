import type { BaseReceiptViewV1 } from "../contracts/baseRunResult";
import { useLanguage } from "../i18n/useLanguage";

interface ReceiptCardProps {
  receipt: BaseReceiptViewV1;
}

export function ReceiptCard({ receipt }: ReceiptCardProps) {
  const { messages: m } = useLanguage();

  return (
    <section className="panel-card nested-card">
      <h3>{m.advanced.receiptTitle}</h3>
      <dl className="definition-grid compact-grid">
        <div>
          <dt>{m.result.requestId}</dt>
          <dd>{receipt.request_id}</dd>
        </div>
        <div>
          <dt>{m.advanced.receiptOutcome}</dt>
          <dd>{receipt.delivery_outcome}</dd>
        </div>
        <div>
          <dt>{m.advanced.receiptOutputRoot}</dt>
          <dd>{receipt.output_root}</dd>
        </div>
        <div>
          <dt>{m.advanced.receiptCreatedBy}</dt>
          <dd>{receipt.created_by}</dd>
        </div>
      </dl>
    </section>
  );
}
