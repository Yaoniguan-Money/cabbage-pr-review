import { useState } from "react";
import type { DiffAtom } from "../api/client";

interface Props {
  atoms: DiffAtom[];
  disabled: boolean;
  onRerun: (paths: string[], atomIds: string[]) => Promise<void>;
}

export default function RerunPanel({ atoms, disabled, onRerun }: Props) {
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
      setError(e instanceof Error ? e.message : "重跑失败");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="card" style={{ marginTop: "1rem" }}>
      <h3>纠偏：补上下文重跑（仅一次）</h3>
      <p style={{ color: "var(--muted)", fontSize: "0.9rem" }}>
        勾选 1~3 个差异点作为重点复审，并可补充文件/目录路径。
      </p>
      <div style={{ maxHeight: 160, overflow: "auto" }}>
        {atoms.slice(0, 30).map((a) => (
          <label key={a.id} style={{ display: "block", marginBottom: 4 }}>
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
        placeholder="补充上下文路径，每行一个"
        value={paths}
        onChange={(e) => setPaths(e.target.value)}
        rows={3}
        disabled={disabled}
      />
      {error && <div className="error">{error}</div>}
      <button onClick={submit} disabled={disabled || loading}>
        {loading ? "重跑中…" : "补上下文并重跑"}
      </button>
    </div>
  );
}
