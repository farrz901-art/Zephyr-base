export type RunMode =
  | "real_tauri_local_text"
  | "real_tauri_local_file"
  | "sample_success"
  | "sample_error";

interface RunModePanelProps {
  mode: RunMode;
  onModeChange: (mode: RunMode) => void;
}

const MODES: Array<{ mode: RunMode; label: string; detail: string }> = [
  {
    mode: "real_tauri_local_text",
    label: "Real Tauri local text",
    detail: "Visible first-class path through Tauri invoke and the bundled adapter.",
  },
  {
    mode: "real_tauri_local_file",
    label: "Real Tauri local file",
    detail: "Use a local file path without falling back to fixture mode.",
  },
  {
    mode: "sample_success",
    label: "Sample success",
    detail: "Regression-only artifact view for known success-shaped data.",
  },
  {
    mode: "sample_error",
    label: "Sample error",
    detail: "Regression-only artifact view for secret-safe failed data.",
  },
];

export function RunModePanel({ mode, onModeChange }: RunModePanelProps) {
  return (
    <section className="panel-card mode-panel-card">
      <p className="eyebrow">Run mode</p>
      <h2>Choose the local run path</h2>
      <div className="mode-grid">
        {MODES.map((entry) => (
          <label
            key={entry.mode}
            className={`mode-option ${entry.mode === mode ? "is-selected" : ""}`}
          >
            <input
              checked={entry.mode === mode}
              name="run-mode"
              type="radio"
              value={entry.mode}
              onChange={() => onModeChange(entry.mode)}
            />
            <span className="mode-label">{entry.label}</span>
            <span className="mode-detail">{entry.detail}</span>
          </label>
        ))}
      </div>
    </section>
  );
}
