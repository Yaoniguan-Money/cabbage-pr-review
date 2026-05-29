import { useEffect, useRef, useState } from "react";
import mermaid from "mermaid";

mermaid.initialize({ startOnLoad: false, theme: "default", securityLevel: "loose" });

export default function MermaidDiagram({ code, id }: { code: string; id: string }) {
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
        const msg = e instanceof Error ? e.message : "未知错误";
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
          图表渲染失败：{error}
          <details style={{ marginTop: "0.5rem" }}>
            <summary>展开查看原始 Mermaid</summary>
            <pre style={{ whiteSpace: "pre-wrap" }}>{code}</pre>
          </details>
        </div>
      ) : null}
      <div ref={ref} />
    </div>
  );
}
