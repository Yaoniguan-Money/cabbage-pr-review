import type { PrPatchFile } from "../api/client";
import UnifiedDiffView from "./UnifiedDiffView";

interface CodeDiffPanelProps {
  files: PrPatchFile[];
  selectedFile: string | null;
  ui: Record<string, string>;
}

export default function CodeDiffPanel({ files, selectedFile, ui }: CodeDiffPanelProps) {
  const active = files.find((f) => f.filename === selectedFile) ?? files[0];
  if (!active) {
    return <p className="diff-empty">{ui.no_files}</p>;
  }
  return (
    <section className="code-diff-panel">
      <div className="code-diff-toolbar">
        <h2 className="code-diff-filename">{active.filename}</h2>
        <span className="code-diff-meta">
          <span className="file-stat-add">+{active.additions ?? 0}</span>
          <span className="file-stat-del">-{active.deletions ?? 0}</span>
        </span>
      </div>
      <UnifiedDiffView patch={active.patch} emptyText={ui.diff_empty} />
    </section>
  );
}
