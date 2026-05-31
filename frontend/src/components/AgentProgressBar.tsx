import type { AgentProgress } from "../api/client";

interface AgentProgressBarProps {
  progress: AgentProgress[];
  stepperLabel?: string;
}

export default function AgentProgressBar({ progress, stepperLabel }: AgentProgressBarProps) {
  return (
    <div className="agent-stepper-wrap">
      {stepperLabel ? (
        <span className="agent-stepper-heading">{stepperLabel}</span>
      ) : null}
      <ol className="agent-stepper" aria-label={stepperLabel}>
        {progress.map((p) => (
          <li
            key={p.agent_id}
            className={`agent-stepper-item ${p.status}`}
            title={p.message ? `${p.name}: ${p.message}` : p.name}
          >
            <span className="agent-stepper-dot" aria-hidden="true">
              {p.status === "completed" ? "✓" : p.status === "failed" ? "!" : p.agent_id}
            </span>
            <span className="agent-stepper-name">{p.name}</span>
          </li>
        ))}
      </ol>
    </div>
  );
}
