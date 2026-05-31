import type { DiffAtom } from "../api/client";

interface ChangesTableProps {
  atoms: DiffAtom[];
  headers: string[];
  emptyText: string;
}

function rowCells(atom: DiffAtom): string[] {
  return [atom.file_path, atom.symbol || "—", atom.change_type, atom.summary];
}

export default function ChangesTable({ atoms, headers, emptyText }: ChangesTableProps) {
  if (!atoms.length) {
    return <p className="sidebar-muted">{emptyText}</p>;
  }

  return (
    <div className="changes-table-wrap">
      <table className="rule-hits-table">
        <thead>
          <tr>
            {headers.map((header) => (
              <th key={header}>{header}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          {atoms.map((atom) => (
            <tr key={atom.id}>
              {rowCells(atom).map((cell, idx) => (
                <td key={`${atom.id}-${idx}`}>{cell}</td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
