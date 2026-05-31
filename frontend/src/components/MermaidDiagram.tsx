import { useEffect, useRef, useState } from "react";
import mermaid from "mermaid";
import type { DiagramUiStrings } from "../api/client";

mermaid.initialize({ startOnLoad: false, theme: "default", securityLevel: "loose" });

export default function MermaidDiagram({
  code,
  id,
  uiStrings,
}: {
  code: string;
  id: string;
  uiStrings: DiagramUiStrings;
}) {
  const ref = useRef<HTMLDivElement>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    if (!ref.current || !code) return;
    const render = async () => {
      try {
        setError("");
        const { svg } = await mermaid.render(`mmd-${id}`, code);
        ref.current!.innerHTML = svg;
      } catch (e) {
        const msg = e instanceof Error ? e.message : String(e);
        setError(msg);
        ref.current!.innerHTML = "";
      }
    };
    render();
  }, [code, id]);

  return (
    <div className="mermaid-wrap">
      {error ? (
        <div className="error">
          {uiStrings.render_error_title}：{error}
          <details style={{ marginTop: "0.5rem" }}>
            <summary>{uiStrings.render_error_hint}</summary>
            <pre style={{ whiteSpace: "pre-wrap" }}>{code}</pre>
          </details>
        </div>
      ) : null}
      <div ref={ref} />
    </div>
  );
}
