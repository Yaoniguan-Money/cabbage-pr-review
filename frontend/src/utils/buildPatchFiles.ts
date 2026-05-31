import type { PrPatchFile, TaskRecord, TaskResult } from "../api/client";

export function buildPatchFiles(task: TaskRecord | null, result: TaskResult | null): PrPatchFile[] {
  const patches = task?.pr_context?.patches ?? [];
  if (patches.length > 0) {
    return patches.map((p) => ({
      filename: p.filename,
      status: p.status,
      patch: p.patch ?? "",
      additions: p.additions ?? 0,
      deletions: p.deletions ?? 0,
    }));
  }

  if (!result?.diff_atoms?.length) {
    const paths = task?.pr_context?.file_paths ?? [];
    return paths.map((filename) => ({
      filename,
      status: "modified",
      patch: "",
      additions: 0,
      deletions: 0,
    }));
  }

  const byFile = new Map<string, PrPatchFile>();
  for (const atom of result.diff_atoms) {
    const hunk = atom.hunk_patch || atom.patch_excerpt || "";
    const existing = byFile.get(atom.file_path);
    if (existing) {
      if (hunk) {
        existing.patch = existing.patch ? `${existing.patch}\n${hunk}` : hunk;
      }
      existing.additions = (existing.additions ?? 0) + (atom.added_line_count ?? 0);
      existing.deletions = (existing.deletions ?? 0) + (atom.removed_line_count ?? 0);
    } else {
      byFile.set(atom.file_path, {
        filename: atom.file_path,
        status: atom.change_type,
        patch: hunk,
        additions: atom.added_line_count ?? 0,
        deletions: atom.removed_line_count ?? 0,
      });
    }
  }
  return Array.from(byFile.values());
}

export function aggregatePatchStats(files: PrPatchFile[]) {
  return files.reduce(
    (acc, file) => ({
      additions: acc.additions + (file.additions ?? 0),
      deletions: acc.deletions + (file.deletions ?? 0),
    }),
    { additions: 0, deletions: 0 },
  );
}
