from __future__ import annotations

import json
import sqlite3
import threading
from pathlib import Path
from typing import Any


class TraceStore:
    """SQLite-backed persistence for execution traces."""

    def __init__(self, db_path: Path) -> None:
        self._db_path = db_path
        self._db_path.parent.mkdir(parents=True, exist_ok=True)
        self._local = threading.local()
        self._init_db()

    def _get_conn(self) -> sqlite3.Connection:
        conn: sqlite3.Connection | None = getattr(self._local, "conn", None)
        if conn is None:
            conn = sqlite3.connect(str(self._db_path), check_same_thread=False)
            conn.row_factory = sqlite3.Row
            conn.execute("PRAGMA journal_mode=WAL")
            conn.execute("PRAGMA busy_timeout=5000")
            self._local.conn = conn
        return conn

    def _init_db(self) -> None:
        conn = self._get_conn()
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS traces (
                trace_id         TEXT PRIMARY KEY,
                session_id       TEXT NOT NULL,
                question         TEXT NOT NULL,
                started_at       REAL NOT NULL,
                ended_at         REAL,
                total_tokens     INTEGER DEFAULT 0,
                total_latency_ms REAL DEFAULT 0.0,
                total_cost       REAL DEFAULT 0.0,
                steps_json       TEXT DEFAULT '[]',
                final_answer_json TEXT,
                error            TEXT
            )
            """
        )
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_traces_session ON traces(session_id)"
        )
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_traces_started ON traces(started_at DESC)"
        )
        conn.commit()

    def save_trace(self, trace_dict: dict[str, Any]) -> None:
        conn = self._get_conn()
        conn.execute(
            """
            INSERT OR REPLACE INTO traces
                (trace_id, session_id, question, started_at, ended_at,
                 total_tokens, total_latency_ms, total_cost,
                 steps_json, final_answer_json, error)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                trace_dict["trace_id"],
                trace_dict["session_id"],
                trace_dict["question"],
                trace_dict["started_at"],
                trace_dict.get("ended_at"),
                trace_dict.get("total_tokens", 0),
                trace_dict.get("total_latency_ms", 0.0),
                trace_dict.get("total_cost", 0.0),
                json.dumps(trace_dict.get("steps", [])),
                json.dumps(trace_dict.get("final_answer")) if trace_dict.get("final_answer") else None,
                trace_dict.get("error"),
            ),
        )
        conn.commit()

    def get_trace(self, trace_id: str) -> dict[str, Any] | None:
        conn = self._get_conn()
        row = conn.execute(
            "SELECT * FROM traces WHERE trace_id = ?", (trace_id,)
        ).fetchone()
        if row is None:
            return None
        return self._row_to_dict(row)

    def list_traces(
        self,
        limit: int = 50,
        offset: int = 0,
        session_id: str | None = None,
    ) -> list[dict[str, Any]]:
        conn = self._get_conn()
        if session_id is not None:
            rows = conn.execute(
                "SELECT * FROM traces WHERE session_id = ? ORDER BY started_at DESC LIMIT ? OFFSET ?",
                (session_id, limit, offset),
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT * FROM traces ORDER BY started_at DESC LIMIT ? OFFSET ?",
                (limit, offset),
            ).fetchall()
        return [self._row_to_dict(r) for r in rows]

    def get_trace_stats(self) -> dict[str, Any]:
        conn = self._get_conn()
        row = conn.execute(
            """
            SELECT
                COUNT(*)          AS total_traces,
                COALESCE(AVG(total_latency_ms), 0) AS avg_latency_ms,
                COALESCE(AVG(total_tokens), 0)     AS avg_tokens,
                COALESCE(AVG(total_cost), 0)        AS avg_cost,
                COALESCE(SUM(total_cost), 0)        AS total_cost,
                COALESCE(SUM(total_tokens), 0)      AS total_tokens_sum,
                COUNT(CASE WHEN error IS NOT NULL THEN 1 END) AS error_count
            FROM traces
            """
        ).fetchone()
        assert row is not None
        return {
            "total_traces": row["total_traces"],
            "avg_latency_ms": round(row["avg_latency_ms"], 1),
            "avg_tokens": int(row["avg_tokens"]),
            "avg_cost": round(row["avg_cost"], 6),
            "total_cost": round(row["total_cost"], 6),
            "total_tokens": row["total_tokens_sum"],
            "error_count": row["error_count"],
        }

    def delete_trace(self, trace_id: str) -> bool:
        conn = self._get_conn()
        cursor = conn.execute("DELETE FROM traces WHERE trace_id = ?", (trace_id,))
        conn.commit()
        return cursor.rowcount > 0

    @staticmethod
    def _row_to_dict(row: sqlite3.Row) -> dict[str, Any]:
        d: dict[str, Any] = dict(row)
        d["steps"] = json.loads(d.pop("steps_json", "[]"))
        raw_answer = d.pop("final_answer_json", None)
        d["final_answer"] = json.loads(raw_answer) if raw_answer else None
        return d


def _build_store() -> TraceStore:
    from app.config import settings

    return TraceStore(settings.trace_db_abs_path)


trace_store: TraceStore = _build_store()
