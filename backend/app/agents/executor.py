from __future__ import annotations

import time

from app.db.connection import db_manager


class QueryExecutor:
    """Pure execution agent — no LLM involved."""

    async def run(self, sql: str, **kwargs) -> dict:
        try:
            start = time.perf_counter()
            data = db_manager.execute_query(sql)
            execution_ms = round((time.perf_counter() - start) * 1000, 1)
            return {
                "output": {
                    "data": data,
                    "row_count": len(data),
                    "execution_ms": execution_ms,
                },
                "error": None,
            }
        except PermissionError as exc:
            return {
                "output": None,
                "error": {"type": "permission_error", "message": str(exc)},
            }
        except Exception as exc:
            return {
                "output": None,
                "error": {"type": type(exc).__name__, "message": str(exc)},
            }
