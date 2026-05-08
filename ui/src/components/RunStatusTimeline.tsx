import type { RunLifecycleState } from "../contracts/baseRunResult";

interface RunStatusTimelineProps {
  currentState: RunLifecycleState;
}

const TIMELINE: Array<{ key: RunLifecycleState; label: string }> = [
  { key: "idle", label: "Idle" },
  { key: "preparing_request", label: "Preparing request" },
  { key: "invoking_tauri_command", label: "Invoking Tauri command" },
  { key: "processing_local_runtime", label: "Processing local runtime" },
  { key: "reading_result", label: "Reading result" },
  { key: "success", label: "Success" },
  { key: "failed", label: "Failed" },
];

export function RunStatusTimeline({ currentState }: RunStatusTimelineProps) {
  const currentIndex = TIMELINE.findIndex((entry) => entry.key === currentState);
  return (
    <section className="panel-card timeline-card">
      <p className="eyebrow">Run lifecycle</p>
      <h2>Local result lifecycle</h2>
      <ol className="timeline-list">
        {TIMELINE.map((entry, index) => {
          const stateClass =
            index < currentIndex
              ? "is-complete"
              : index === currentIndex
                ? "is-active"
                : "";
          return (
            <li key={entry.key} className={`timeline-item ${stateClass}`}>
              <span className="timeline-step">{index + 1}</span>
              <span className="timeline-label">{entry.label}</span>
            </li>
          );
        })}
      </ol>
    </section>
  );
}
