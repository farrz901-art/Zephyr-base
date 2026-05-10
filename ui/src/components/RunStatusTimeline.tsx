import type { RunLifecycleState } from "../contracts/baseRunResult";
import { useLanguage } from "../i18n/useLanguage";

interface RunStatusTimelineProps {
  currentState: RunLifecycleState;
}

const ORDER = ["ready", "preparing", "running", "completed", "failed"] as const;
type DisplayState = (typeof ORDER)[number];

function toDisplayState(currentState: RunLifecycleState): DisplayState {
  if (currentState === "idle") {
    return "ready";
  }
  if (currentState === "preparing_request") {
    return "preparing";
  }
  if (
    currentState === "invoking_tauri_command" ||
    currentState === "processing_local_runtime" ||
    currentState === "reading_result"
  ) {
    return "running";
  }
  if (currentState === "success") {
    return "completed";
  }
  return "failed";
}

export function RunStatusTimeline({ currentState }: RunStatusTimelineProps) {
  const { messages: m } = useLanguage();
  const active = toDisplayState(currentState);
  const currentIndex = ORDER.indexOf(active);
  const labels: Record<DisplayState, string> = {
    ready: m.status.ready,
    preparing: m.status.preparing,
    running: m.status.running,
    completed: m.status.completed,
    failed: m.status.failed,
  };

  return (
    <section className="panel-card timeline-card">
      <p className="eyebrow">{m.run.title}</p>
      <h2>{m.status.runningSummary}</h2>
      <ol className="timeline-list">
        {ORDER.map((entry, index) => {
          const stateClass =
            index < currentIndex ? "is-complete" : index === currentIndex ? "is-active" : "";
          return (
            <li key={entry} className={`timeline-item ${stateClass}`}>
              <span className="timeline-step">{index + 1}</span>
              <span className="timeline-label">{labels[entry]}</span>
            </li>
          );
        })}
      </ol>
    </section>
  );
}
