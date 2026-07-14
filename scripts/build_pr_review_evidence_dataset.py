"""Build a fixed 50-patch review set from a pinned SWE-bench Lite revision."""

from __future__ import annotations

import hashlib
import io
import json
import re
import random
import sys
import time
from pathlib import Path
from typing import Any

import polars as pl
import requests


ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = ROOT / "evidence" / "config" / "dataset-selection.json"
SOURCE_PATH = ROOT / "evidence" / "source" / "SWE-bench_Lite-test.parquet"
DATASET_PATH = ROOT / "evidence" / "datasets" / "pr_review_cases.jsonl"
PATCH_DIR = ROOT / "evidence" / "datasets" / "patches"
_HUNK_RE = re.compile(
    r"^@@\s+-(?P<old>\d+)(?:,(?P<old_count>\d+))?\s+\+(?P<new>\d+)(?:,(?P<new_count>\d+))?\s+@@(?P<tail>.*)$"
)
_SEVERITY = {
    "security": "high",
    "exception": "medium",
    "compatibility": "medium",
    "performance": "medium",
    "logic": "medium",
}


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _source_url(config: dict[str, Any]) -> str:
    revision = config["source_revision"]
    return (
        "https://huggingface.co/datasets/SWE-bench/SWE-bench_Lite/resolve/"
        f"{revision}/data/test-00000-of-00001.parquet"
    )


def _download(config: dict[str, Any]) -> bytes:
    if SOURCE_PATH.is_file() and SOURCE_PATH.stat().st_size >= 1_000_000:
        return SOURCE_PATH.read_bytes()
    last_error: Exception | None = None
    content = b""
    for attempt in range(4):
        try:
            response = requests.get(_source_url(config), timeout=120)
            response.raise_for_status()
            content = response.content
            break
        except requests.RequestException as exc:
            last_error = exc
            if attempt < 3:
                time.sleep(2 ** attempt)
    if not content:
        raise RuntimeError(f"failed to download pinned source after 4 attempts: {last_error}")
    if len(content) < 1_000_000:
        raise RuntimeError(f"source parquet unexpectedly small: {len(content)} bytes")
    SOURCE_PATH.parent.mkdir(parents=True, exist_ok=True)
    SOURCE_PATH.write_bytes(content)
    return content


def _swap_hunk_header(line: str) -> str:
    match = _HUNK_RE.match(line)
    if not match:
        return line
    old_count = f",{match.group('old_count')}" if match.group("old_count") is not None else ""
    new_count = f",{match.group('new_count')}" if match.group("new_count") is not None else ""
    return (
        f"@@ -{match.group('new')}{new_count} +{match.group('old')}{old_count} @@"
        f"{match.group('tail')}"
    )


def reverse_unified_diff(patch: str) -> str:
    reversed_lines: list[str] = []
    old_header: str | None = None
    for line in patch.splitlines():
        if line.startswith("@@"):
            reversed_lines.append(_swap_hunk_header(line))
        elif line.startswith("--- "):
            old_header = line[4:]
            reversed_lines.append("__OLD_HEADER__")
        elif line.startswith("+++ "):
            new_header = line[4:]
            if reversed_lines and reversed_lines[-1] == "__OLD_HEADER__":
                reversed_lines[-1] = f"--- {new_header}"
                reversed_lines.append(f"+++ {old_header}")
                old_header = None
            else:
                reversed_lines.append(f"--- {new_header}")
        elif line.startswith("index ") and ".." in line:
            prefix, hashes_and_mode = line.split(" ", 1)
            hashes, *mode = hashes_and_mode.split(" ")
            left, right = hashes.split("..", 1)
            reversed_lines.append(" ".join([prefix, f"{right}..{left}", *mode]).rstrip())
        elif line.startswith("new file mode "):
            reversed_lines.append(line.replace("new file mode", "deleted file mode", 1))
        elif line.startswith("deleted file mode "):
            reversed_lines.append(line.replace("deleted file mode", "new file mode", 1))
        elif line.startswith("+") and not line.startswith("+++"):
            reversed_lines.append("-" + line[1:])
        elif line.startswith("-") and not line.startswith("---"):
            reversed_lines.append("+" + line[1:])
        else:
            reversed_lines.append(line)
    return "\n".join(reversed_lines) + "\n"


def _patch_file_path(diff_line: str) -> str:
    parts = diff_line.split()
    if len(parts) < 4:
        return "unknown.patch"
    return parts[3].removeprefix("b/")


def changed_locations(patch: str) -> list[dict[str, Any]]:
    by_file: dict[str, set[int]] = {}
    current_file = "unknown.patch"
    new_line: int | None = None
    for line in patch.splitlines():
        if line.startswith("diff --git "):
            current_file = _patch_file_path(line)
            by_file.setdefault(current_file, set())
            new_line = None
            continue
        header = _HUNK_RE.match(line)
        if header:
            new_line = int(header.group("new"))
            continue
        if new_line is None:
            continue
        if line.startswith("+") and not line.startswith("+++"):
            by_file.setdefault(current_file, set()).add(max(1, new_line))
            new_line += 1
        elif line.startswith("-") and not line.startswith("---"):
            by_file.setdefault(current_file, set()).add(max(1, new_line))
        elif line.startswith("\\ No newline at end of file"):
            continue
        else:
            new_line += 1
    return [
        {
            "file_path": file_path,
            "lines": sorted(lines),
            "line_start": min(lines),
            "line_end": max(lines),
        }
        for file_path, lines in sorted(by_file.items())
        if lines
    ]


def _tracker_url(repo: str, instance_id: str) -> str:
    number = instance_id.rsplit("-", 1)[-1]
    # SWE-bench instance IDs identify the source tracker item, not necessarily
    # the numeric pull request that supplied the gold patch.  Keep the link
    # truthful and rely on the pinned SWE-bench row for the Issue-PR pairing.
    return f"https://github.com/{repo}/issues/{number}"


def _record(
    *,
    ordinal: int,
    source_index: int,
    row: dict[str, Any],
    direction: str,
    category: str | None,
) -> dict[str, Any]:
    patch = reverse_unified_diff(row["patch"]) if direction == "reverse_bug" else row["patch"]
    case_id = f"prcase-{ordinal:03d}"
    patch_path = PATCH_DIR / f"{case_id}.patch"
    patch_path.write_text(patch, encoding="utf-8", newline="\n")
    title = (row["problem_statement"] or "").splitlines()[0].strip()
    positive = direction == "reverse_bug"
    locations = changed_locations(patch) if positive else []
    if positive and not locations:
        raise RuntimeError(f"{row['instance_id']}: reversed patch has no locatable changed lines")
    return {
        "case_id": case_id,
        "source_index": source_index,
        "source_dataset": "SWE-bench/SWE-bench_Lite",
        "source_instance_id": row["instance_id"],
        "source_repo": row["repo"],
        "source_tracker_url": _tracker_url(row["repo"], row["instance_id"]),
        "source_base_commit": row["base_commit"],
        "source_created_at": str(row["created_at"]),
        "source_issue_title": title,
        "construction": direction,
        "review_title": f"Maintenance change {case_id}",
        "patch_path": str(patch_path.relative_to(ROOT)).replace("\\", "/"),
        "patch_sha256": _sha256_bytes(patch.encode("utf-8")),
        "has_target_defect": positive,
        "target_category": category,
        "target_severity": _SEVERITY.get(category) if category else None,
        "target_locations": locations,
        "annotation_basis": (
            "Reverse of the official gold patch; changed locations are the reverse diff's changed new-file coordinates."
            if positive
            else "Forward official gold fix from a distinct PR; no target defect from its source issue."
        ),
    }


def main() -> None:
    config = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    source_bytes = _download(config)
    rows = list(pl.read_parquet(io.BytesIO(source_bytes)).iter_rows(named=True))
    records: list[dict[str, Any]] = []
    ordinal = 1
    selected_indices: set[int] = set()

    for category, indices in config["positive_reverse_patch_indices"].items():
        if len(indices) != 5:
            raise RuntimeError(f"{category}: expected 5 positive indices")
        for index in indices:
            if index in selected_indices:
                raise RuntimeError(f"duplicate source index: {index}")
            selected_indices.add(index)
            records.append(
                _record(
                    ordinal=ordinal,
                    source_index=index,
                    row=rows[index],
                    direction="reverse_bug",
                    category=category,
                )
            )
            ordinal += 1

    for index in config["negative_forward_patch_indices"]:
        if index in selected_indices:
            raise RuntimeError(f"duplicate source index: {index}")
        selected_indices.add(index)
        records.append(
            _record(
                ordinal=ordinal,
                source_index=index,
                row=rows[index],
                direction="forward_clean_control",
                category=None,
            )
        )
        ordinal += 1

    if len(records) != 50 or len(selected_indices) != 50:
        raise RuntimeError(f"expected 50 distinct source PRs, got {len(records)} records / {len(selected_indices)} sources")
    if len({record["patch_sha256"] for record in records}) != 50:
        raise RuntimeError("patch hashes are not unique")
    if sum(record["has_target_defect"] for record in records) != 25:
        raise RuntimeError("expected 25 positive cases")

    random.Random(config["case_order_seed"]).shuffle(records)

    DATASET_PATH.parent.mkdir(parents=True, exist_ok=True)
    DATASET_PATH.write_text(
        "".join(json.dumps(record, ensure_ascii=False) + "\n" for record in records),
        encoding="utf-8",
        newline="\n",
    )
    manifest = {
        "schema_version": 1,
        "source_url": _source_url(config),
        "source_revision": config["source_revision"],
        "source_parquet_sha256": _sha256_bytes(source_bytes),
        "dataset_path": str(DATASET_PATH.relative_to(ROOT)).replace("\\", "/"),
        "dataset_sha256": _sha256_bytes(DATASET_PATH.read_bytes()),
        "total_patches": 50,
        "distinct_source_issue_pr_pairs": 50,
        "source_pair_basis": "Each selected row is one pinned SWE-bench Lite Issue-PR pair; the row carries the official gold patch. Tracker URLs identify the issue and are not asserted to be PR URLs.",
        "positive_reverse_bug_patches": 25,
        "negative_forward_fix_controls": 25,
        "categories": {
            category: sum(record["target_category"] == category for record in records)
            for category in _SEVERITY
        },
        "case_order_seed": config["case_order_seed"],
        "label_limit": "Forward controls are accepted source fixes with no target issue defect; they are not guaranteed free of every unrelated defect.",
    }
    manifest_path = ROOT / "evidence" / "dataset-manifest.json"
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(manifest, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    sys.exit(main())
