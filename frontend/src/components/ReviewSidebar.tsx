import { Link } from "react-router-dom";

import type { PrPatchFile } from "../api/client";
import { exportUrl } from "../api/client";

export interface ReviewNavItem {
  id: string;
  label: string;
  show: boolean;
}

interface ReviewSidebarProps {
  taskId: string;
  nav: ReviewNavItem[];
  section: string;
  onSectionChange: (id: string) => void;
  files: PrPatchFile[];
  selectedFile: string | null;
  onSelectFile: (filename: string) => void;
  ui: Record<string, string>;
  rulesUi: Record<string, string>;
  filesSidebarLabel: string;
  exportLabel: string;
  onJumpDiagrams: () => void;
  showDiagramsLink: boolean;
  diagramsLinkLabel: string;
}

export default function ReviewSidebar({
  taskId,
  nav,
  section,
  onSectionChange,
  files,
  selectedFile,
  onSelectFile,
  ui,
  rulesUi,
  filesSidebarLabel,
  exportLabel,
  onJumpDiagrams,
  showDiagramsLink,
  diagramsLinkLabel,
}: ReviewSidebarProps) {
  return (
    <div className="review-sidebar-inner">
      <Link to="/" className="back-link">
        {rulesUi.back_link}
      </Link>

      <nav className="sidebar-nav" aria-label="任务详情导航">
        <ul className="nav-list">
          {nav
            .filter((item) => item.show)
            .map((item) => (
              <li key={item.id}>
                <button
                  type="button"
                  className={section === item.id ? "active" : ""}
                  onClick={() => onSectionChange(item.id)}
                >
                  {item.label}
                </button>
              </li>
            ))}
        </ul>
      </nav>

      {showDiagramsLink ? (
        <button type="button" className="secondary sidebar-link-btn" onClick={onJumpDiagrams}>
          {diagramsLinkLabel}
        </button>
      ) : null}

      <hr className="sidebar-divider" />

      <div className="files-sidebar">
        <h3 className="sidebar-section-title">{filesSidebarLabel}</h3>
        {files.length === 0 ? (
          <p className="sidebar-muted">{ui.no_files}</p>
        ) : (
          <ul className="file-list">
            {files.map((file) => (
              <li key={file.filename}>
                <button
                  type="button"
                  className={`file-list-item ${selectedFile === file.filename ? "active" : ""}`}
                  onClick={() => {
                    onSelectFile(file.filename);
                    onSectionChange("files");
                  }}
                >
                  <span className="file-list-name">{file.filename}</span>
                  <span className="file-list-stats">
                    <span className="file-stat-add">+{file.additions ?? 0}</span>
                    <span className="file-stat-del">-{file.deletions ?? 0}</span>
                  </span>
                </button>
              </li>
            ))}
          </ul>
        )}
      </div>

      <a href={exportUrl(taskId)} target="_blank" rel="noreferrer" className="sidebar-export">
        <button type="button" className="secondary" style={{ width: "100%" }}>
          {exportLabel}
        </button>
      </a>
    </div>
  );
}
