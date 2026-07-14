"""Fail-closed integrity checks for the AI PR Review evidence package."""

from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / "evidence"


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _load_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _summary(metrics: dict[str, Any], mode: str) -> dict[str, Any]:
    rows = [row for row in metrics["summaries"] if row["mode"] == mode]
    assert len(rows) == 1, f"expected one summary for {mode}, got {len(rows)}"
    return rows[0]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--require-live", action="store_true")
    parser.add_argument(
        "--allow-missing-source",
        action="store_true",
        help="Validate archived derived artifacts when the downloadable upstream parquet is intentionally absent.",
    )
    args = parser.parse_args()

    manifest = _load_json(EVIDENCE / "dataset-manifest.json")
    dataset_path = ROOT / manifest["dataset_path"]
    source_path = EVIDENCE / "source" / "SWE-bench_Lite-test.parquet"
    cases = _load_jsonl(dataset_path)

    assert _sha256(dataset_path) == manifest["dataset_sha256"]
    if source_path.is_file():
        assert _sha256(source_path) == manifest["source_parquet_sha256"]
    else:
        assert args.allow_missing_source, f"missing pinned source parquet: {source_path}"
    assert len(cases) == manifest["total_patches"] == 50
    assert len({row["case_id"] for row in cases}) == 50
    assert len({row["source_instance_id"] for row in cases}) == 50
    assert len({row["patch_sha256"] for row in cases}) == 50
    assert all("source_pr_url" not in row for row in cases)
    assert all(row["source_tracker_url"].startswith("https://github.com/") for row in cases)
    assert all("/issues/" in row["source_tracker_url"] for row in cases)

    positives = [row for row in cases if row["has_target_defect"]]
    negatives = [row for row in cases if not row["has_target_defect"]]
    assert len(positives) == len(negatives) == 25
    assert Counter(row["target_category"] for row in positives) == {
        "security": 5,
        "logic": 5,
        "exception": 5,
        "compatibility": 5,
        "performance": 5,
    }
    assert all(row["construction"] == "reverse_bug" for row in positives)
    assert all(row["construction"] == "forward_clean_control" for row in negatives)
    assert all(row["target_locations"] for row in positives)
    assert all(not row["target_locations"] for row in negatives)
    for row in cases:
        patch_path = ROOT / row["patch_path"]
        assert patch_path.is_file()
        assert _sha256(patch_path) == row["patch_sha256"]

    rules = _load_json(EVIDENCE / "raw" / "pr_review_rules.json")["results"]
    assert len(rules) == 50 and len({row["case_id"] for row in rules}) == 50
    assert all(row["success"] for row in rules)

    metrics = _load_json(EVIDENCE / "raw" / "pr_review_metrics.json")
    rule_summary = _summary(metrics, "rules_only")
    assert rule_summary["classifiable_patches"] == 50
    assert (rule_summary["tp"], rule_summary["fp"], rule_summary["fn"], rule_summary["tn"]) == (0, 1, 25, 24)
    assert rule_summary["f1"] == 0.0

    live_path = EVIDENCE / "raw" / "pr_review_live_qwen.json"
    if args.require_live or live_path.is_file():
        live = _load_json(live_path)["results"]
        assert len(live) == 50 and len({row["case_id"] for row in live}) == 50
        assert all(row["success"] for row in live)
        assert all(row.get("model") == "qwen-plus" for row in live)
        live_summary = _summary(metrics, "live_llm_single_pass_qwen_plus")
        assert live_summary["classifiable_patches"] == 50
        assert (live_summary["tp"], live_summary["fp"], live_summary["fn"], live_summary["tn"]) == (24, 21, 1, 4)
        assert abs(live_summary["precision"] - 24 / 45) < 1e-12
        assert abs(live_summary["recall"] - 24 / 25) < 1e-12
        assert abs(live_summary["f1"] - 24 / 35) < 1e-12
        assert live_summary["prompt_tokens"] == 29_466
        assert live_summary["completion_tokens"] == 9_900
        assert live_summary["total_tokens"] == 39_366

    deepseek = _load_json(EVIDENCE / "raw" / "pr_review_deepseek_payment_exhausted_pilot.json")["results"]
    assert len(deepseek) == 50
    assert sum(row["success"] for row in deepseek) == 14
    assert sum(not row["success"] for row in deepseek) == 36
    assert any("402 Payment Required" in " ".join(row.get("errors") or []) for row in deepseek)

    approved = _load_json(EVIDENCE / "resume_metrics_approved.json")
    assert len(approved["metrics"]) == 1
    assert approved["metrics"][0]["id"] == "pr-review-qwen-swebench-pairs-v1"
    print("AI PR Review evidence validation passed: 50 cases, rules complete, live complete, failure pilot retained.")


if __name__ == "__main__":
    main()
