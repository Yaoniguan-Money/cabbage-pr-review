import type { AgentProgress } from "../api/client";

export default function AgentProgressBar({ progress }: { progress: AgentProgress[] }) {
  return (
    <div className="agent-progress">
      {progress.map((p) => (
        <span key={p.agent_id} className={`agent-step ${p.status}`} title={p.message}>
          {p.agent_id}. {p.name}: {p.status}
        </span>
      ))}
    </div>
  );
}
