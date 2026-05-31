import type { PrPatchFile, TaskRecord, TaskResult } from "../api/client";

function countPatchLineStats(patch: string): { additions: number; deletions: number } {
  let additions = 0;
  let deletions = 0;
  for (const line of patch.split("\n")) {
    if (line.startsWith("+") && !line.startsWith("+++")) additions += 1;
    else if (line.startsWith("-") && !line.startsWith("---")) deletions += 1;
  }
  return { additions, deletions };
}

function resolvePatchStats(
  patch: string,
  additions?: number,
  deletions?: number,
): { additions: number; deletions: number } {
  const fromPatch = countPatchLineStats(patch);
  if (additions == null || deletions == null) {
    return fromPatch;
  }
  if (additions === 0 && deletions === 0 && (fromPatch.additions > 0 || fromPatch.deletions > 0)) {
    return fromPatch;
  }
  return { additions, deletions };
}

export function buildPatchFiles(task: TaskRecord | null, result: TaskResult | null): PrPatchFile[] {
  const patches = task?.pr_context?.patches ?? [];
  if (patches.length > 0) {
    return patches.map((p) => {
      const patchText = p.patch ?? "";
      const stats = resolvePatchStats(patchText, p.additions, p.deletions);
      return {
        filename: p.filename,
        status: p.status,
        patch: patchText,
        additions: stats.additions,
        deletions: stats.deletions,
      };
    });
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
