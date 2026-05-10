import { useLanguage } from "../i18n/useLanguage";

interface InteractionProofPanelProps {
  proofStatus: "not_exported" | "exported" | "failed";
  proofPath: string | null;
  note: string;
  enabled: boolean;
  onExport: () => void;
}

export function InteractionProofPanel({
  proofStatus,
  proofPath,
  note,
  enabled,
  onExport,
}: InteractionProofPanelProps) {
  const { messages: m } = useLanguage();

  const statusLabel =
    proofStatus === "exported"
      ? m.advanced.proofExported
      : proofStatus === "failed"
        ? m.advanced.proofExportFailed
        : m.advanced.proofNotExported;

  return (
    <section className="panel-card nested-card">
      <p className="eyebrow">{m.advanced.proofTitle}</p>
      <h3>{m.advanced.proofSubtitle}</h3>
      <div className="proof-status-row">
        <span className={`status-pill ${proofStatus}`}>{statusLabel}</span>
        <button
          className="secondary-button"
          disabled={!enabled}
          type="button"
          onClick={onExport}
        >
          {m.advanced.proofExport}
        </button>
      </div>
      <p className="toolbar-note">{note}</p>
      <p className="toolbar-note">
        {m.advanced.proofPath}:{" "}
        <strong>{proofPath ?? ".tmp/s10_tauri_window_interaction/ui_interaction_proof.json"}</strong>
      </p>
    </section>
  );
}
