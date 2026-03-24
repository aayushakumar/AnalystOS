"""Eval MCP Server — manages benchmarks and evaluation results."""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml

logger = logging.getLogger(__name__)

_DATA_DIR = Path(__file__).resolve().parent.parent.parent.parent / "data"
_BENCHMARKS_DIR = _DATA_DIR / "benchmarks"
_RESULTS_DIR = _DATA_DIR / "eval_results"


class EvalServer:
    """MCP service for loading benchmarks and storing evaluation results."""

    def __init__(self) -> None:
        _RESULTS_DIR.mkdir(parents=True, exist_ok=True)

    # ------------------------------------------------------------------
    # Benchmarks
    # ------------------------------------------------------------------

    def list_benchmarks(self) -> list[str]:
        """Return the file names of all available benchmark YAML files."""
        if not _BENCHMARKS_DIR.is_dir():
            logger.warning("Benchmarks directory not found: %s", _BENCHMARKS_DIR)
            return []
        return sorted(p.name for p in _BENCHMARKS_DIR.glob("*.yaml"))

    def get_benchmark(self, name: str) -> dict[str, Any]:
        """Load and return a benchmark by file name (e.g. 'benchmark_v1.yaml')."""
        path = _BENCHMARKS_DIR / name
        if not path.is_file():
            return {"error": f"Benchmark '{name}' not found."}
        try:
            with path.open() as f:
                return yaml.safe_load(f) or {}
        except yaml.YAMLError as exc:
            return {"error": f"Failed to parse benchmark '{name}': {exc}"}

    def get_eval_case(self, benchmark_name: str, case_id: str) -> dict[str, Any] | None:
        """Return a single evaluation case from a benchmark by its id."""
        benchmark = self.get_benchmark(benchmark_name)
        if "error" in benchmark:
            return benchmark
        for case in benchmark.get("cases", []):
            if str(case.get("id")) == str(case_id):
                return case
        return None

    # ------------------------------------------------------------------
    # Results
    # ------------------------------------------------------------------

    def store_eval_result(self, case_id: str, result: dict[str, Any]) -> None:
        """Append an evaluation result to the results JSON-lines file."""
        record = {
            "case_id": case_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            **result,
        }
        results_file = _RESULTS_DIR / "results.jsonl"
        try:
            with results_file.open("a", encoding="utf-8") as f:
                f.write(json.dumps(record) + "\n")
        except OSError as exc:
            logger.error("Failed to write eval result: %s", exc)

    def get_eval_history(self) -> list[dict[str, Any]]:
        """Read all stored evaluation results."""
        results_file = _RESULTS_DIR / "results.jsonl"
        if not results_file.is_file():
            return []
        records: list[dict[str, Any]] = []
        try:
            for line in results_file.read_text(encoding="utf-8").splitlines():
                line = line.strip()
                if line:
                    records.append(json.loads(line))
        except (OSError, json.JSONDecodeError) as exc:
            logger.error("Failed to read eval history: %s", exc)
        return records
