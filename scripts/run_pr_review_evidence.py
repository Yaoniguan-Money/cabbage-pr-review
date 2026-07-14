"""Evaluate rules-only and an optional live structured LLM reviewer on 50 fixed patches."""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path
from typing import Any

import httpx


ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "backend"
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

from app.llm.openai_compat import OpenAICompatibleProvider
from app.llm.task_context import TaskLLMContext, clear_task_llm_context, set_task_llm_context
from app.llm.token_usage import get_task_token_stats, reset_task_token_usage
from app.local.file_io import parse_patch_text
from app.local.result_repair import repair_model
from app.models.schemas import RiskReviewSchema
from app.rules.pipeline.rules_diff import run_rules_diff
from app.rules.pipeline.rules_review import run_rules_review


DATASET_PATH = ROOT / "evidence" / "datasets" / "pr_review_cases.jsonl"
CONFIG_PATH = ROOT / "evidence" / "config" / "review-experiment.json"
RULES_RAW = ROOT / "evidence" / "raw" / "pr_review_rules.json"
LIVE_RAW = ROOT / "evidence" / "raw" / "pr_review_live_qwen.json"
REPORT_RAW = ROOT / "evidence" / "raw" / "pr_review_metrics.json"
FAILURES_PATH = ROOT / "evidence" / "failures" / "pr_review_failures.jsonl"


def _load_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def _percentile(values: list[float], percentile: int) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    index = max(0, min(len(ordered) - 1, int(len(ordered) * percentile / 100 + 0.9999) - 1))
    return ordered[index]


def _review_context(case: dict[str, Any], patch: str) -> dict[str, Any]:
    patches = parse_patch_text(patch)
    return {
        "title": case["review_title"],
        "body": "Review this maintenance diff for concrete, actionable defects.",
        "patches": patches,
        "file_paths": [item["filename"] for item in patches],
    }


def _rules_result(case: dict[str, Any]) -> dict[str, Any]:
    patch = (ROOT / case["patch_path"]).read_text(encoding="utf-8")
    context = _review_context(case, patch)
    started = time.perf_counter()
    diff, diff_notes = run_rules_diff(context)
    review, hits, stats, review_notes = run_rules_review(diff, context)
    latency_ms = (time.perf_counter() - started) * 1000.0
    return {
        "case_id": case["case_id"],
        "mode": "rules_only",
        "success": True,
        "latency_ms": latency_ms,
        "tokens": {"prompt": 0, "completion": 0, "total": 0},
        "risks": [risk.model_dump(mode="json") for risk in review.risks],
        "rule_hits": [hit.model_dump(mode="json") for hit in hits],
        "notes": diff_notes + review_notes,
        "review_stats": stats.model_dump(mode="json"),
    }


def _llm_prompt(case: dict[str, Any], patch: str) -> tuple[str, str]:
    system = (
        "You are a conservative pull-request reviewer. Report only concrete defects introduced by the diff. "
        "Do not report generic change risk, style, missing tests, or pre-existing behavior. "
        "Use new-file line numbers from unified-diff hunk headers. Return RiskReviewSchema JSON. "
        "For each risk set an exact file_paths entry, line_start, line_end, risk_level, evidence, suggestion, "
        "and category chosen from security, logic, exception, compatibility, performance, or other. "
        "If no concrete defect is present, return an empty risks list."
    )
    user = json.dumps(
        {
            "pr_title": case["review_title"],
            "patch": patch,
            "json_contract": {
                "risks": [
                    {
                        "id": "r1",
                        "title": "Concrete defect",
                        "description": "Failure mechanism and impact",
                        "risk_level": "high|medium|low",
                        "confidence": "high|medium|low",
                        "evidence": "Exact changed code",
                        "suggestion": "Specific correction",
                        "related_atoms": [],
                        "file_paths": ["path/from/diff.py"],
                        "line_start": 1,
                        "line_end": 1,
                        "category": "security|logic|exception|compatibility|performance|other"
                    }
                ],
                "missing_info": [],
                "degradation_notes": []
            }
        },
        ensure_ascii=False,
    )
    return system, user


def _live_result(
    case: dict[str, Any],
    *,
    provider: OpenAICompatibleProvider,
    model: str,
    max_attempts: int,
) -> dict[str, Any]:
    patch = (ROOT / case["patch_path"]).read_text(encoding="utf-8")
    system, user = _llm_prompt(case, patch)
    errors: list[str] = []
    started = time.perf_counter()
    reset_task_token_usage("_default")
    final_attempt = 0
    for attempt in range(1, max_attempts + 1):
        final_attempt = attempt
        try:
            raw = provider.complete_json_sync(model=model, system=system, user=user, tier="pro")
            review = repair_model(RiskReviewSchema, raw)
            stats = get_task_token_stats("_default")
            tokens = {
                "prompt": stats.cloud_prompt_tokens if stats else 0,
                "completion": stats.cloud_completion_tokens if stats else 0,
                "total": stats.cloud_total_tokens if stats else 0,
            }
            return {
                "case_id": case["case_id"],
                "mode": "live_llm_single_pass_qwen_plus",
                "model": model,
                "success": True,
                "attempts": attempt,
                "latency_ms": (time.perf_counter() - started) * 1000.0,
                "tokens": tokens,
                "risks": [risk.model_dump(mode="json") for risk in review.risks],
                "notes": list(review.degradation_notes),
                "errors": errors,
            }
        except Exception as exc:
            errors.append(f"attempt {attempt}: {type(exc).__name__}: {exc}")
            retryable = isinstance(exc, httpx.TransportError)
            if isinstance(exc, httpx.HTTPStatusError):
                status = exc.response.status_code
                retryable = status in {408, 409, 429} or status >= 500
            if not retryable:
                break
    stats = get_task_token_stats("_default")
    return {
        "case_id": case["case_id"],
        "mode": "live_llm_single_pass_qwen_plus",
        "model": model,
        "success": False,
        "attempts": final_attempt,
        "latency_ms": (time.perf_counter() - started) * 1000.0,
        "tokens": {
            "prompt": stats.cloud_prompt_tokens if stats else 0,
            "completion": stats.cloud_completion_tokens if stats else 0,
            "total": stats.cloud_total_tokens if stats else 0,
        },
        "risks": [],
        "notes": [],
        "errors": errors,
    }


def _write_raw(path: Path, mode: str, results: list[dict[str, Any]], config: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(
            {"schema_version": 1, "mode": mode, "config": config, "results": results},
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )


def _overlaps_target(risk: dict[str, Any], target: dict[str, Any]) -> bool:
    if target["file_path"] not in (risk.get("file_paths") or []):
        return False
    start = risk.get("line_start")
    end = risk.get("line_end") or start
    if not isinstance(start, int) or not isinstance(end, int):
        return False
    return any(start <= line <= end for line in target["lines"])


def _score_mode(
    mode: str,
    cases: list[dict[str, Any]],
    results: list[dict[str, Any]],
    config: dict[str, Any],
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    by_id = {row["case_id"]: row for row in results}
    scored = []
    for case in cases:
        result = by_id.get(case["case_id"])
        if result is None:
            continue
        risks = result.get("risks") or []
        predicted = bool(risks)
        positive = bool(case["has_target_defect"])
        target_paths = {target["file_path"] for target in case["target_locations"]}
        file_match = positive and any(target_paths.intersection(risk.get("file_paths") or []) for risk in risks)
        line_match = positive and any(
            _overlaps_target(risk, target)
            for risk in risks
            for target in case["target_locations"]
        )
        localized_risks = [
            risk for risk in risks if target_paths.intersection(risk.get("file_paths") or [])
        ]
        severity_match = positive and any(
            risk.get("risk_level") == case["target_severity"] for risk in localized_risks
        )
        category_match = positive and any(
            str(risk.get("category") or "").casefold() == case["target_category"]
            for risk in localized_risks
        )
        scored.append(
            {
                "case_id": case["case_id"],
                "source_instance_id": case["source_instance_id"],
                "positive": positive,
                "category": case["target_category"],
                "predicted_positive": predicted,
                "risk_count": len(risks),
                "success": result.get("success", False),
                "file_match": bool(file_match),
                "line_match": bool(line_match),
                "severity_match": bool(severity_match),
                "category_match": bool(category_match),
                "latency_ms": result.get("latency_ms", 0.0),
                "tokens": result.get("tokens") or {},
            }
        )

    # Provider/protocol failures are reported separately and never converted
    # into negative predictions.  This prevents outages from inflating TN or FN.
    classifiable = [row for row in scored if row["success"]]
    tp = sum(row["positive"] and row["predicted_positive"] for row in classifiable)
    fp = sum(not row["positive"] and row["predicted_positive"] for row in classifiable)
    fn = sum(row["positive"] and not row["predicted_positive"] for row in classifiable)
    tn = sum(not row["positive"] and not row["predicted_positive"] for row in classifiable)
    precision = tp / (tp + fp) if tp + fp else 0.0
    recall = tp / (tp + fn) if tp + fn else 0.0
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
    positives = [row for row in classifiable if row["positive"]]
    negatives = [row for row in classifiable if not row["positive"]]
    latencies = [row["latency_ms"] for row in classifiable]
    prompt_tokens = sum(int(row["tokens"].get("prompt") or 0) for row in classifiable)
    completion_tokens = sum(int(row["tokens"].get("completion") or 0) for row in classifiable)
    price = config["pricing_cny_per_thousand_tokens_upper_bound"]
    upper_cost = prompt_tokens / 1_000 * price["input"] + completion_tokens / 1_000 * price["output"]
    category_recall = {}
    for category in ("security", "logic", "exception", "compatibility", "performance"):
        rows = [row for row in positives if row["category"] == category]
        category_recall[category] = sum(row["predicted_positive"] for row in rows) / len(rows) if rows else 0.0
    summary = {
        "mode": mode,
        "evaluated_patches": len(scored),
        "classifiable_patches": len(classifiable),
        "successful_runs": sum(row["success"] for row in scored),
        "failed_runs": sum(not row["success"] for row in scored),
        "tp": tp,
        "fp": fp,
        "fn": fn,
        "tn": tn,
        "precision": precision,
        "recall": recall,
        "f1": f1,
        "clean_patch_flag_rate": fp / len(negatives) if negatives else 0.0,
        "false_risks_per_clean_patch": sum(row["risk_count"] for row in negatives) / len(negatives) if negatives else 0.0,
        "file_localization_rate_all_positives": sum(row["file_match"] for row in positives) / len(positives) if positives else 0.0,
        "line_localization_rate_all_positives": sum(row["line_match"] for row in positives) / len(positives) if positives else 0.0,
        "severity_match_rate_all_positives": sum(row["severity_match"] for row in positives) / len(positives) if positives else 0.0,
        "category_match_rate_all_positives": sum(row["category_match"] for row in positives) / len(positives) if positives else 0.0,
        "category_detection_recall": category_recall,
        "latency_p50_ms": _percentile(latencies, 50),
        "latency_p95_ms": _percentile(latencies, 95),
        "prompt_tokens": prompt_tokens,
        "completion_tokens": completion_tokens,
        "total_tokens": prompt_tokens + completion_tokens,
        "estimated_cost_cny_upper_bound": upper_cost,
    }
    return summary, scored


def _read_results(path: Path) -> list[dict[str, Any]]:
    if not path.is_file():
        return []
    return json.loads(path.read_text(encoding="utf-8")).get("results") or []


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--live", action="store_true")
    parser.add_argument("--limit", type=int, default=0)
    parser.add_argument("--resume", action="store_true")
    args = parser.parse_args()
    config = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    cases = _load_jsonl(DATASET_PATH)
    selected = cases[: args.limit] if args.limit > 0 else cases

    rules_results = [_rules_result(case) for case in selected]
    _write_raw(RULES_RAW, "rules_only", rules_results, config)
    print(f"rules_only complete: {len(rules_results)} patches", flush=True)

    if args.live:
        existing = _read_results(LIVE_RAW) if args.resume else []
        by_id = {row["case_id"]: row for row in existing}
        api_key = os.environ.get(config["live_api_key_env"], "").strip()
        if not api_key:
            raise RuntimeError(f"missing {config['live_api_key_env']}")
        set_task_llm_context(
            TaskLLMContext(
                llm_mode="cloud_only",
                local_compress_enabled=False,
                local_model="",
                cloud_flash_model=config["live_model"],
                cloud_pro_model=config["live_model"],
                cloud_api_base=config["live_api_base"],
                cloud_api_key=api_key,
            )
        )
        provider = OpenAICompatibleProvider(timeout_sec=config["timeout_seconds"])
        try:
            for index, case in enumerate(selected, start=1):
                if case["case_id"] in by_id:
                    continue
                result = _live_result(
                    case,
                    provider=provider,
                    model=config["live_model"],
                    max_attempts=config["max_attempts_per_patch"],
                )
                by_id[case["case_id"]] = result
                ordered = [by_id[item["case_id"]] for item in cases if item["case_id"] in by_id]
                _write_raw(LIVE_RAW, "live_llm_single_pass_qwen_plus", ordered, config)
                print(
                    f"live {index}/{len(selected)} {case['case_id']} success={result['success']} "
                    f"risks={len(result['risks'])} latency_ms={result['latency_ms']:.0f}",
                    flush=True,
                )
        finally:
            clear_task_llm_context()

    mode_results = {"rules_only": _read_results(RULES_RAW)}
    if LIVE_RAW.is_file():
        mode_results["live_llm_single_pass_qwen_plus"] = _read_results(LIVE_RAW)
    summaries = []
    all_scored = {}
    failures = []
    for mode, results in mode_results.items():
        summary, scored = _score_mode(mode, cases, results, config)
        summaries.append(summary)
        all_scored[mode] = scored
        failures.extend(
            {"mode": mode, **row}
            for row in scored
            if (row["positive"] and not row["predicted_positive"])
            or (not row["positive"] and row["predicted_positive"])
            or not row["success"]
        )
    REPORT_RAW.write_text(
        json.dumps(
            {"schema_version": 1, "summaries": summaries, "scored_cases": all_scored},
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    FAILURES_PATH.write_text(
        "".join(json.dumps(row, ensure_ascii=False) + "\n" for row in failures),
        encoding="utf-8",
    )
    print(json.dumps(summaries, ensure_ascii=False, indent=2), flush=True)


if __name__ == "__main__":
    main()
