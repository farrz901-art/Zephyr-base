import { useLanguage } from "../i18n/useLanguage";

interface LocalOutputControlsProps {
  lastOutputDir: string;
  onReadLatest: () => void;
  onExportProof: () => void;
  proofEnabled: boolean;
  showProofAction?: boolean;
}

export function LocalOutputControls({
  lastOutputDir,
  onReadLatest,
  onExportProof,
  proofEnabled,
  showProofAction = true,
}: LocalOutputControlsProps) {
  const { messages: m } = useLanguage();

  return (
    <section className="panel-card nested-card">
      <p className="eyebrow">{m.result.outputTitle}</p>
      <h3>{m.result.outputDir}</h3>
      <div className="toolbar-row">
        <button className="secondary-button" type="button" onClick={onReadLatest}>
          {m.run.readLatest}
        </button>
        {showProofAction ? (
          <button
            className="ghost-button"
            disabled={!proofEnabled}
            type="button"
            onClick={onExportProof}
          >
            {m.advanced.proofExport}
          </button>
        ) : null}
      </div>
      <p className="toolbar-note">
        {m.result.outputDir}: <strong>{lastOutputDir}</strong>
      </p>
    </section>
  );
}
