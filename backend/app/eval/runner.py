"""Batch evaluation runner — executes benchmark cases through the workflow and scores results."""

from __future__ import annotations

import asyncio
import json
import logging
import sys
import time
from pathlib import Path
from typing import Any

import yaml

from app.eval.metrics import compute_all_scores
from app.eval.reporter import EvalReporter

logger = logging.getLogger(__name__)

_BENCHMARKS_DIR = Path(__file__).resolve().parent.parent.parent / "data" / "benchmarks"


class EvalRunner:
    """Load a benchmark YAML and run every case through the analyst workflow."""

    def __init__(self, benchmark_path: Path | None = None) -> None:
        self._benchmark_path = benchmark_path
        self._reporter = EvalReporter()

    def _resolve_benchmark(self, benchmark_name: str) -> Path:
        if self._benchmark_path:
            return self._benchmark_path
        path = _BENCHMARKS_DIR / f"{benchmark_name}.yaml"
        if not path.is_file():
            raise FileNotFoundError(f"Benchmark not found: {path}")
        return path

    @staticmethod
    def _load_benchmark(path: Path) -> dict[str, Any]:
        with path.open() as f:
            data = yaml.safe_load(f)
        if not data or "cases" not in data:
            raise ValueError(f"Invalid benchmark file: {path}")
        return data

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def run_benchmark(
        self,
        benchmark_name: str = "benchmark_v1",
        *,
        concurrency: int = 4,
        category_filter: str | None = None,
        save_report: bool = True,
    ) -> dict[str, Any]:
        """Run all cases in a benchmark and return the evaluation report.

        Args:
            benchmark_name: Name of the YAML file (without extension).
            concurrency: Max number of cases to evaluate in parallel.
            category_filter: If set, only run cases matching this category.
            save_report: Persist the report JSON alongside the benchmark.
        """
        path = self._resolve_benchmark(benchmark_name)
        benchmark = self._load_benchmark(path)

        cases: list[dict[str, Any]] = benchmark["cases"]
        if category_filter:
            cases = [c for c in cases if c.get("category") == category_filter]

        logger.info(
            "Starting benchmark '%s' — %d cases (concurrency=%d)",
            benchmark.get("name", benchmark_name),
            len(cases),
            concurrency,
        )

        semaphore = asyncio.Semaphore(concurrency)
        start = time.perf_counter()

        async def _bounded(case: dict[str, Any]) -> dict[str, Any]:
            async with semaphore:
                return await self.run_single_case(case)

        results = await asyncio.gather(*[_bounded(c) for c in cases])
        total_elapsed_ms = (time.perf_counter() - start) * 1000

        report = self._reporter.generate_report(
            results=list(results),
            benchmark_meta={
                "name": benchmark.get("name", benchmark_name),
                "version": benchmark.get("version", "unknown"),
                "total_elapsed_ms": round(total_elapsed_ms, 1),
            },
        )

        if save_report:
            output_dir = _BENCHMARKS_DIR.parent / "eval_results"
            output_dir.mkdir(parents=True, exist_ok=True)
            ts = time.strftime("%Y%m%d_%H%M%S")
            self._reporter.save_report(report, output_dir / f"report_{ts}.json")

        return report

    async def run_single_case(self, case: dict[str, Any]) -> dict[str, Any]:
        """Run a single eval case through the workflow and score it."""
        from app.graph.workflow import run_workflow

        case_id = case["id"]
        question = case["question"]

        logger.info("[%s] Running: %s", case_id, question[:80])
        start = time.perf_counter()

        try:
            state = await run_workflow(question, session_id=f"eval_{case_id}")
        except Exception as exc:
            logger.error("[%s] Workflow error: %s", case_id, exc)
            state = {"error": str(exc), "question": question}

        latency_ms = (time.perf_counter() - start) * 1000
        scores = self.score_case(case, state)

        return {
            "case_id": case_id,
            "question": question,
            "category": case.get("category", "unknown"),
            "scores": scores,
            "latency_ms": round(latency_ms, 1),
            "tokens": state.get("total_tokens", 0),
            "cost": state.get("total_cost", 0.0),
            "error": state.get("error"),
        }

    @staticmethod
    def score_case(case: dict[str, Any], state: dict[str, Any]) -> dict[str, float]:
        """Score a completed workflow state against expected values."""
        return compute_all_scores(case, state)


# ---------------------------------------------------------------------------
# CLI entry point: python -m app.eval.runner
# ---------------------------------------------------------------------------

async def _main() -> None:
    import argparse

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)-8s %(name)s — %(message)s",
    )

    parser = argparse.ArgumentParser(description="AnalystOS Eval Harness")
    parser.add_argument(
        "--benchmark", default="benchmark_v1", help="Benchmark name (default: benchmark_v1)"
    )
    parser.add_argument(
        "--concurrency", type=int, default=4, help="Max parallel evaluations (default: 4)"
    )
    parser.add_argument(
        "--category", default=None, help="Only run cases in this category"
    )
    parser.add_argument(
        "--case", default=None, help="Run a single case by id"
    )
    parser.add_argument(
        "--no-save", action="store_true", help="Skip saving the report file"
    )
    args = parser.parse_args()

    runner = EvalRunner()

    if args.case:
        path = runner._resolve_benchmark(args.benchmark)
        benchmark = runner._load_benchmark(path)
        matched = [c for c in benchmark["cases"] if c["id"] == args.case]
        if not matched:
            print(f"Case '{args.case}' not found in {args.benchmark}")
            sys.exit(1)
        result = await runner.run_single_case(matched[0])
        print(json.dumps(result, indent=2))
        return

    report = await runner.run_benchmark(
        benchmark_name=args.benchmark,
        concurrency=args.concurrency,
        category_filter=args.category,
        save_report=not args.no_save,
    )

    print("\n" + "=" * 72)
    print("EVALUATION REPORT")
    print("=" * 72)
    print(f"Benchmark : {report['benchmark']['name']}")
    print(f"Cases     : {report['summary']['total_cases']}")
    print(f"Elapsed   : {report['benchmark'].get('total_elapsed_ms', 0):.0f} ms")
    print()

    for metric, value in report["summary"]["overall_scores"].items():
        print(f"  {metric:30s} {value:.3f}")

    print()
    print("Per-category breakdown:")
    for cat, cat_data in report["by_category"].items():
        avg = cat_data.get("avg_composite", 0)
        n = cat_data.get("count", 0)
        print(f"  {cat:20s}  n={n:3d}  avg_composite={avg:.3f}")

    if report.get("worst_cases"):
        print()
        print("Worst-performing cases:")
        for wc in report["worst_cases"][:5]:
            print(f"  [{wc['case_id']}] composite={wc['composite']:.3f} — {wc['question'][:60]}")

    print()


if __name__ == "__main__":
    asyncio.run(_main())
