import type { RunLifecycleState, RuntimeModeSummary } from "../../contracts/baseRunResult";
import { useLanguage } from "../../i18n/useLanguage";
import { ProgressPanel } from "../ProgressPanel";
import { RunStatusTimeline } from "../RunStatusTimeline";

interface RunCardProps {
  inputMode: "text" | "file";
  lifecycleState: RunLifecycleState;
  runtimeMode: RuntimeModeSummary;
  status: string;
  detail: string;
  onRun: () => void;
  onReadLatest: () => void;
  isRunning: boolean;
}

export function RunCard({
  inputMode,
  lifecycleState,
  runtimeMode,
  status,
  detail,
  onRun,
  onReadLatest,
  isRunning,
}: RunCardProps) {
  const { messages: m } = useLanguage();

  return (
    <section className="panel-card wide-card">
      <div className="section-heading">
        <div>
          <p className="eyebrow">{m.run.title}</p>
          <h2>{m.run.subtitle}</h2>
        </div>
        <div className="toolbar-row">
          <button className="primary-button" type="button" onClick={onRun} disabled={isRunning}>
            {m.run.primary}
          </button>
          <button className="secondary-button" type="button" onClick={onReadLatest} disabled={isRunning}>
            {m.run.readLatest}
          </button>
        </div>
      </div>
      <p className="toolbar-note">
        {inputMode === "text" ? m.run.selectedText : m.run.selectedFile}
        {isRunning ? ` ${m.run.disabled}` : ""}
      </p>
      <div className="result-grid">
        <RunStatusTimeline currentState={lifecycleState} />
        <ProgressPanel status={status} detail={detail} runtimeMode={runtimeMode} />
      </div>
    </section>
  );
}
