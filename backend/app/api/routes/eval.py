from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Any

from fastapi import APIRouter

router = APIRouter(prefix="/eval", tags=["eval"])

_eval_state: dict[str, Any] = {"running": False, "latest_report": None}


@router.post("/run")
async def run_eval(
    benchmark: str = "benchmark_v1",
    category: str | None = None,
) -> dict[str, str]:
    if _eval_state["running"]:
        return {"status": "already_running"}

    _eval_state["running"] = True
    asyncio.create_task(_run_benchmark(benchmark, category))
    return {"status": "started"}


async def _run_benchmark(benchmark: str, category: str | None) -> None:
    from app.eval.runner import EvalRunner

    try:
        runner = EvalRunner()
        report = await runner.run_benchmark(benchmark_name=benchmark)
        _eval_state["latest_report"] = report
    except Exception as exc:
        _eval_state["latest_report"] = {"error": str(exc)}
    finally:
        _eval_state["running"] = False


@router.get("/results")
async def get_results() -> dict[str, Any]:
    return {
        "running": _eval_state["running"],
        "report": _eval_state["latest_report"],
    }


@router.get("/benchmarks")
async def list_benchmarks() -> list[str]:
    benchmarks_dir = Path(__file__).parent.parent.parent.parent / "data" / "benchmarks"
    if not benchmarks_dir.exists():
        return []
    return [f.stem for f in benchmarks_dir.glob("*.yaml")]
