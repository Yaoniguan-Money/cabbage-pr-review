import type { ProjectIndex } from "../api/client";

interface IndexPanelProps {
  baseIndex: ProjectIndex | null | undefined;
  headIndex: ProjectIndex | null | undefined;
  ui: Record<string, string>;
}

function renderList(label: string, items: string[] | undefined) {
  if (!items?.length) return null;
  return (
    <div className="index-panel-block">
      <span className="stat-label">{label}</span>
      <ul className="index-panel-list">
        {items.slice(0, 10).map((item) => (
          <li key={item}>{item}</li>
        ))}
      </ul>
    </div>
  );
}

export default function IndexPanel({ baseIndex, headIndex, ui }: IndexPanelProps) {
  if (!baseIndex && !headIndex) {
    return null;
  }

  return (
    <section className="index-panel">
      <h3 className="content-heading">{ui.index_panel_title}</h3>
      {renderList(ui.index_base_entries, baseIndex?.entry_files)}
      {renderList(ui.index_head_entries, headIndex?.entry_files)}
      {renderList(ui.index_base_modules, baseIndex?.modules)}
      {renderList(ui.index_head_modules, headIndex?.modules)}
    </section>
  );
}
