import type { TaskResult } from "../api/client";

export default function SummaryBar({ result }: { result: TaskResult }) {
  return (
    <div className="summary-bar">
      <h2>摘要</h2>
      <p>{result.summary}</p>
      <ul>
        {result.summary_bullets.map((b, i) => (
          <li key={i}>{b}</li>
        ))}
      </ul>
      <p style={{ color: "var(--muted)", fontSize: "0.9rem" }}>
        识别：{result.detected_framework} / {result.detected_project_type}
      </p>
    </div>
  );
}
