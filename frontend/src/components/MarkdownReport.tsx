import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

type Props = {
  content: string;
};

export default function MarkdownReport({ content }: Props) {
  if (!content.trim()) {
    return null;
  }

  return (
    <article className="markdown-report">
      <ReactMarkdown remarkPlugins={[remarkGfm]}>{content}</ReactMarkdown>
    </article>
  );
}
