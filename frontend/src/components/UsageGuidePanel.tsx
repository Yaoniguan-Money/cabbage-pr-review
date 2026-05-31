import { useState } from "react";

export interface UsageGuideSection {
  id: string;
  heading: string;
  paragraphs: string[];
}

export interface UsageGuideMeta {
  title: string;
  toggle_show: string;
  toggle_hide: string;
  default_expanded: boolean;
  sections: UsageGuideSection[];
}

type Props = {
  guide: UsageGuideMeta | null | undefined;
};

export default function UsageGuidePanel({ guide }: Props) {
  const [open, setOpen] = useState(guide?.default_expanded ?? true);

  if (!guide?.sections?.length) return null;

  const toggleLabel = open ? guide.toggle_hide : guide.toggle_show;

  return (
    <section className="card usage-guide-panel" aria-label={guide.title}>
      <button
        type="button"
        className="usage-guide-toggle"
        onClick={() => setOpen((v) => !v)}
        aria-expanded={open}
      >
        {guide.title}
        <span className="usage-guide-toggle-hint">{toggleLabel}</span>
      </button>
      {open ? (
        <div className="usage-guide-body">
          {guide.sections.map((section) => (
            <article key={section.id} className="usage-guide-section">
              <h3 className="usage-guide-heading">{section.heading}</h3>
              {section.paragraphs.map((para, i) => (
                <p key={`${section.id}-${i}`} className="usage-guide-paragraph">
                  {para}
                </p>
              ))}
            </article>
          ))}
        </div>
      ) : null}
    </section>
  );
}
