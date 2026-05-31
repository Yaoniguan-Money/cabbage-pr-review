import type { AgentProgress } from "../api/client";

interface AgentProgressBarProps {
  progress: AgentProgress[];
  stepperLabel?: string;
  parallelLaneAria?: string;
}

type StepSegment =
  | { kind: "single"; item: AgentProgress }
  | { kind: "parallel"; group: string; items: AgentProgress[] };

function buildSegments(progress: AgentProgress[]): StepSegment[] {
  const segments: StepSegment[] = [];
  let i = 0;
  while (i < progress.length) {
    const pg = progress[i].parallel_group;
    if (pg) {
      const items: AgentProgress[] = [];
      while (i < progress.length && progress[i].parallel_group === pg) {
        items.push(progress[i]);
        i += 1;
      }
      segments.push({ kind: "parallel", group: pg, items });
    } else {
      segments.push({ kind: "single", item: progress[i] });
      i += 1;
    }
  }
  return segments;
}

function StepItem({ p }: { p: AgentProgress }) {
  return (
    <li
      className={`agent-stepper-item ${p.status}`}
      title={p.message ? `${p.name}: ${p.message}` : p.name}
    >
      <span className="agent-stepper-dot" aria-hidden="true">
        {p.status === "completed" ? "✓" : p.status === "failed" ? "!" : p.agent_id}
      </span>
      <span className="agent-stepper-name">{p.name}</span>
    </li>
  );
}

export default function AgentProgressBar({
  progress,
  stepperLabel,
  parallelLaneAria,
}: AgentProgressBarProps) {
  const segments = buildSegments(progress);

  return (
    <div className="agent-stepper-wrap">
      {stepperLabel ? (
        <span className="agent-stepper-heading">{stepperLabel}</span>
      ) : null}
      <ol className="agent-stepper" aria-label={stepperLabel}>
        {segments.map((seg) => {
          if (seg.kind === "single") {
            return <StepItem key={seg.item.agent_id} p={seg.item} />;
          }
          const runningCount = seg.items.filter((p) => p.status === "running").length;
          const laneClass =
            runningCount >= 2
              ? "agent-stepper-parallel-lane parallel-active"
              : "agent-stepper-parallel-lane";
          return (
            <li
              key={`parallel-${seg.group}`}
              className={laneClass}
              aria-label={parallelLaneAria}
            >
              <ol className="agent-stepper-parallel-inner">
                {seg.items.map((p) => (
                  <StepItem key={p.agent_id} p={p} />
                ))}
              </ol>
            </li>
          );
        })}
      </ol>
    </div>
  );
}
