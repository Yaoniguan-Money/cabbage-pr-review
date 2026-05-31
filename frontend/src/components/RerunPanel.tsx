import { useState } from "react";
import type { DiffAtom } from "../api/client";

interface Props {
  atoms: DiffAtom[];
  disabled: boolean;
  onRerun: (paths: string[], atomIds: string[]) => Promise<void>;
  ui: Record<string, string>;
}

export default function RerunPanel({ atoms, disabled, onRerun, ui }: Props) {
  const [paths, setPaths] = useState("");
  const [selected, setSelected] = useState<string[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const toggle = (id: string) => {
    setSelected((prev) => {
      if (prev.includes(id)) return prev.filter((x) => x !== id);
      if (prev.length >= 3) return prev;
      return [...prev, id];
    });
  };

  const submit = async () => {
    setLoading(true);
    setError("");
    try {
      const pathList = paths
        .split("\n")
        .map((s) => s.trim())
        .filter(Boolean);
      await onRerun(pathList, selected);
    } catch (e) {
      setError(e instanceof Error ? e.message : ui.rerun_error_fallback);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="card rerun-panel">
      <h3>{ui.rerun_title}</h3>
      <p className="section-hint">{ui.rerun_hint}</p>
      <div className="rerun-atoms">
        {atoms.slice(0, 30).map((a) => (
          <label key={a.id} className="rerun-atom-label">
            <input
              type="checkbox"
              checked={selected.includes(a.id)}
              onChange={() => toggle(a.id)}
              disabled={disabled}
            />{" "}
            {a.summary || a.file_path}
          </label>
        ))}
      </div>
      <textarea
        placeholder={ui.rerun_paths_placeholder}
        value={paths}
        onChange={(e) => setPaths(e.target.value)}
        rows={3}
        disabled={disabled}
      />
      {error && <div className="error">{error}</div>}
      <button type="button" onClick={submit} disabled={disabled || loading}>
        {loading ? ui.rerun_submit_loading : ui.rerun_submit_idle}
      </button>
    </div>
  );
}
