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
  return (
    <section className="panel-card">
      <p className="eyebrow">Interaction proof</p>
      <h2>Visible window proof pack</h2>
      <p className="panel-copy">
        Export a manual proof pack after a real Tauri run. The proof pack records
        invoke usage, local artifact paths, and the display surfaces shown in the window.
      </p>
      <div className="proof-status-row">
        <span className={`status-pill ${proofStatus}`}>
          {proofStatus === "exported"
            ? "Proof exported"
            : proofStatus === "failed"
              ? "Proof export failed"
              : "Proof not exported"}
        </span>
        <button
          className="secondary-button"
          disabled={!enabled}
          type="button"
          onClick={onExport}
        >
          Export interaction proof
        </button>
      </div>
      <p className="toolbar-note">{note}</p>
      <p className="toolbar-note">
        Proof path: <strong>{proofPath ?? ".tmp/s10_tauri_window_interaction/ui_interaction_proof.json"}</strong>
      </p>
    </section>
  );
}
