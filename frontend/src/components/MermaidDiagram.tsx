import { useEffect, useRef } from "react";
import mermaid from "mermaid";

mermaid.initialize({ startOnLoad: false, theme: "default", securityLevel: "loose" });

export default function MermaidDiagram({ code, id }: { code: string; id: string }) {
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!ref.current || !code) return;
    const render = async () => {
      try {
        const { svg } = await mermaid.render(`mmd-${id}`, code);
        ref.current!.innerHTML = svg;
      } catch {
        ref.current!.innerHTML = `<pre>图表渲染失败\n${code}</pre>`;
      }
    };
    render();
  }, [code, id]);

  return <div className="mermaid-wrap" ref={ref} />;
}
