"""Report generation — aggregates scored eval results into structured reports."""

from __future__ import annotations

import json
import logging
from collections import defaultdict
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

# Weights for computing a composite score per case.
# Metrics not listed here are excluded from the composite.
_METRIC_WEIGHTS: dict[str, float] = {
    "intent_accuracy": 0.25,
    "sql_validity": 0.20,
    "table_coverage": 0.15,
    "safety_classification": 0.20,
    "clarification_detection": 0.10,
    "answer_contains": 0.10,
}


def _composite_score(scores: dict[str, float]) -> float:
    """Weighted average of individual metric scores."""
    total_weight = 0.0
    weighted_sum = 0.0
    for metric, weight in _METRIC_WEIGHTS.items():
        if metric in scores:
            weighted_sum += scores[metric] * weight
            total_weight += weight
    return round(weighted_sum / total_weight, 4) if total_weight else 0.0


class EvalReporter:
    """Aggregates per-case eval results into a structured report."""

    def generate_report(
        self,
        results: list[dict[str, Any]],
        benchmark_meta: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Generate an aggregate evaluation report.

        Args:
            results: List of per-case dicts from EvalRunner.run_single_case.
            benchmark_meta: Optional metadata (name, version, elapsed).

        Returns:
            Structured report dict with summary, per-category, and worst cases.
        """
        if not results:
            return {
                "benchmark": benchmark_meta or {},
                "summary": {"total_cases": 0, "overall_scores": {}},
                "by_category": {},
                "worst_cases": [],
                "results": [],
            }

        for r in results:
            r["composite"] = _composite_score(r.get("scores", {}))

        by_cat: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for r in results:
            by_cat[r.get("category", "unknown")].append(r)

        all_metrics = set()
        for r in results:
            all_metrics.update(r.get("scores", {}).keys())

        overall: dict[str, float] = {}
        for metric in sorted(all_metrics):
            vals = [r["scores"][metric] for r in results if metric in r.get("scores", {})]
            overall[metric] = round(sum(vals) / len(vals), 4) if vals else 0.0
        overall["composite"] = round(
            sum(r["composite"] for r in results) / len(results), 4
        )

        category_summary: dict[str, Any] = {}
        for cat, cat_results in sorted(by_cat.items()):
            cat_metrics: dict[str, float] = {}
            for metric in sorted(all_metrics):
                vals = [r["scores"][metric] for r in cat_results if metric in r.get("scores", {})]
                cat_metrics[metric] = round(sum(vals) / len(vals), 4) if vals else 0.0
            cat_metrics["composite"] = round(
                sum(r["composite"] for r in cat_results) / len(cat_results), 4
            )
            category_summary[cat] = {
                "count": len(cat_results),
                "scores": cat_metrics,
                "avg_composite": cat_metrics["composite"],
                "avg_latency_ms": round(
                    sum(r.get("latency_ms", 0) for r in cat_results) / len(cat_results), 1
                ),
                "avg_tokens": round(
                    sum(r.get("tokens", 0) for r in cat_results) / len(cat_results)
                ),
                "total_cost": round(
                    sum(r.get("cost", 0) for r in cat_results), 6
                ),
                "error_count": sum(1 for r in cat_results if r.get("error")),
            }

        sorted_by_score = sorted(results, key=lambda r: r["composite"])
        worst = [
            {
                "case_id": r["case_id"],
                "question": r["question"],
                "category": r.get("category"),
                "composite": r["composite"],
                "scores": r.get("scores", {}),
                "error": r.get("error"),
            }
            for r in sorted_by_score[:10]
        ]

        total_cost = round(sum(r.get("cost", 0) for r in results), 6)
        total_tokens = sum(r.get("tokens", 0) for r in results)
        error_count = sum(1 for r in results if r.get("error"))

        return {
            "benchmark": benchmark_meta or {},
            "summary": {
                "total_cases": len(results),
                "overall_scores": overall,
                "total_tokens": total_tokens,
                "total_cost": total_cost,
                "error_count": error_count,
            },
            "by_category": category_summary,
            "worst_cases": worst,
            "results": results,
        }

    @staticmethod
    def save_report(report: dict[str, Any], output_path: Path) -> None:
        """Persist the report as a formatted JSON file."""
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with output_path.open("w", encoding="utf-8") as f:
            json.dump(report, f, indent=2, default=str)
        logger.info("Report saved to %s", output_path)
