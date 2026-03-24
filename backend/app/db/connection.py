import re
import threading
from pathlib import Path

import duckdb


class DuckDBManager:
    _WRITE_PATTERN = re.compile(
        r"\b(INSERT|UPDATE|DELETE|DROP|ALTER|CREATE|TRUNCATE|GRANT|REVOKE)\b",
        re.IGNORECASE,
    )

    def __init__(self) -> None:
        self._conn: duckdb.DuckDBPyConnection | None = None
        self._lock = threading.Lock()

    def initialize(self, db_path: Path) -> None:
        db_path.parent.mkdir(parents=True, exist_ok=True)
        self._conn = duckdb.connect(str(db_path))

    @property
    def conn(self) -> duckdb.DuckDBPyConnection:
        if self._conn is None:
            raise RuntimeError("DuckDB not initialized — call initialize() first.")
        return self._conn

    def close(self) -> None:
        with self._lock:
            if self._conn is not None:
                self._conn.close()
                self._conn = None

    def execute_query(self, sql: str) -> list[dict]:
        if self._WRITE_PATTERN.search(sql):
            raise PermissionError(f"Write operations are not allowed. Rejected: {sql[:80]}")
        with self._lock:
            result = self.conn.execute(sql)
            columns = [desc[0] for desc in result.description]
            return [dict(zip(columns, row)) for row in result.fetchall()]

    def execute_query_raw(self, sql: str) -> duckdb.DuckDBPyConnection:
        """Execute without read-only guard — used only by seed script."""
        with self._lock:
            return self.conn.execute(sql)

    def get_table_names(self) -> list[str]:
        rows = self.execute_query(
            "SELECT table_name FROM information_schema.tables "
            "WHERE table_schema = 'main' ORDER BY table_name"
        )
        return [r["table_name"] for r in rows]

    def describe_table(self, table_name: str) -> list[dict]:
        return self.execute_query(
            "SELECT column_name, data_type, is_nullable "
            "FROM information_schema.columns "
            f"WHERE table_name = '{table_name}' ORDER BY ordinal_position"
        )

    def get_sample_rows(self, table_name: str, n: int = 5) -> list[dict]:
        safe_name = table_name.replace("'", "").replace(";", "")
        return self.execute_query(f'SELECT * FROM "{safe_name}" LIMIT {n}')

    def explain_query(self, sql: str) -> str:
        if self._WRITE_PATTERN.search(sql):
            raise PermissionError("Write operations are not allowed.")
        with self._lock:
            result = self.conn.execute(f"EXPLAIN {sql}")
            return "\n".join(row[1] for row in result.fetchall())


db_manager = DuckDBManager()
