type DiffLineKind = "add" | "del" | "ctx" | "hunk" | "meta";

interface DiffLine {
  kind: DiffLineKind;
  text: string;
  oldNo?: number;
  newNo?: number;
}

function classifyLine(line: string): DiffLineKind {
  if (line.startsWith("@@")) return "hunk";
  if (line.startsWith("+++") || line.startsWith("---") || line.startsWith("diff --git")) return "meta";
  if (line.startsWith("+")) return "add";
  if (line.startsWith("-")) return "del";
  return "ctx";
}

export function parseUnifiedDiff(patch: string): DiffLine[] {
  const lines = patch.replace(/\r\n/g, "\n").split("\n");
  let oldNo = 0;
  let newNo = 0;
  const out: DiffLine[] = [];

  for (const line of lines) {
    const kind = classifyLine(line);
    if (kind === "hunk") {
      const m = line.match(/@@ -(\d+)(?:,\d+)? \+(\d+)(?:,\d+)? @@/);
      if (m) {
        oldNo = Number(m[1]);
        newNo = Number(m[2]);
      }
      out.push({ kind, text: line });
      continue;
    }
    if (kind === "add") {
      out.push({ kind, text: line, newNo });
      newNo += 1;
      continue;
    }
    if (kind === "del") {
      out.push({ kind, text: line, oldNo });
      oldNo += 1;
      continue;
    }
    if (kind === "ctx" && line.startsWith(" ")) {
      out.push({ kind, text: line, oldNo, newNo });
      oldNo += 1;
      newNo += 1;
      continue;
    }
    out.push({ kind, text: line });
  }
  return out;
}

export default function UnifiedDiffView({ patch, emptyText }: { patch: string; emptyText: string }) {
  if (!patch.trim()) {
    return <p className="diff-empty">{emptyText}</p>;
  }
  const lines = parseUnifiedDiff(patch);
  return (
    <pre className="unified-diff">
      <code>
        {lines.map((line, index) => (
          <div key={index} className={`diff-line diff-line-${line.kind}`}>
            <span className="diff-gutter diff-gutter-old">{line.oldNo ?? ""}</span>
            <span className="diff-gutter diff-gutter-new">{line.newNo ?? ""}</span>
            <span className="diff-text">{line.text || " "}</span>
          </div>
        ))}
      </code>
    </pre>
  );
}
