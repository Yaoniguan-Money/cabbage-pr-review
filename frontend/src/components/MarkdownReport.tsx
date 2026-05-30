import { useMemo } from "react";

type Props = {
  content: string;
};

/** 轻量 Markdown 展示：按 ## 分段渲染标题与正文（无第三方依赖）。 */
export default function MarkdownReport({ content }: Props) {
  const sections = useMemo(() => {
    const parts = content.split(/^## /m).filter(Boolean);
    return parts.map((block) => {
      const newline = block.indexOf("\n");
      const title = newline >= 0 ? block.slice(0, newline).trim() : block.trim();
      const body = newline >= 0 ? block.slice(newline + 1).trim() : "";
      return { title, body };
    });
  }, [content]);

  if (!content.trim()) {
    return null;
  }

  return (
    <article className="markdown-report">
      {sections.map((section) => (
        <section key={section.title} className="markdown-section">
          <h3>{section.title}</h3>
          <pre className="markdown-body">{section.body}</pre>
        </section>
      ))}
    </article>
  );
}
