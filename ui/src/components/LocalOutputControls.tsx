interface LocalOutputControlsProps {
  lastOutputDir: string;
  onReadLatest: () => void;
  onExportProof: () => void;
  proofEnabled: boolean;
}

export function LocalOutputControls({
  lastOutputDir,
  onReadLatest,
  onExportProof,
  proofEnabled,
}: LocalOutputControlsProps) {
  return (
    <section className="panel-card">
      <p className="eyebrow">Local outputs</p>
      <h2>Result artifacts</h2>
      <p className="panel-copy">
        The visible shell reads one `base_run_result_v1` family and keeps the output folder
        path visible.
      </p>
      <div className="toolbar-row">
        <button className="secondary-button" type="button" onClick={onReadLatest}>
          Read latest result
        </button>
        <button
          className="ghost-button"
          disabled={!proofEnabled}
          type="button"
          onClick={onExportProof}
        >
          Export proof from current result
        </button>
      </div>
      <p className="toolbar-note">
        Last output dir: <strong>{lastOutputDir}</strong>
      </p>
    </section>
  );
}
