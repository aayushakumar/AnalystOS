"""Analytics DB MCP Server — exposes schema exploration and read-only query tools."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

import yaml

from app.db.connection import db_manager

logger = logging.getLogger(__name__)

_DATA_DIR = Path(__file__).resolve().parent.parent.parent.parent / "data"
_DATA_DICT_PATH = _DATA_DIR / "ecommerce" / "data_dictionary.yaml"


class AnalyticsDBServer:
    """MCP service that wraps the DuckDB analytics database."""

    def __init__(self) -> None:
        self._data_dict: dict[str, Any] = {}
        self._load_data_dictionary()

    # ------------------------------------------------------------------
    # Initialisation
    # ------------------------------------------------------------------

    def _load_data_dictionary(self) -> None:
        try:
            with _DATA_DICT_PATH.open() as f:
                self._data_dict = yaml.safe_load(f) or {}
        except FileNotFoundError:
            logger.warning("Data dictionary not found at %s", _DATA_DICT_PATH)
        except yaml.YAMLError as exc:
            logger.error("Failed to parse data dictionary: %s", exc)

    # ------------------------------------------------------------------
    # Tools
    # ------------------------------------------------------------------

    def list_tables(self) -> list[dict[str, str]]:
        """Return table names with descriptions sourced from the data dictionary."""
        tables_meta: dict[str, Any] = self._data_dict.get("tables", {})
        results: list[dict[str, str]] = []
        for name, info in tables_meta.items():
            results.append({
                "table_name": name,
                "description": info.get("description", ""),
                "freshness": info.get("freshness", ""),
            })
        return results

    def describe_table(self, table_name: str) -> dict[str, Any]:
        """Return column metadata, types, descriptions, and sample values for a table."""
        table_meta = self._data_dict.get("tables", {}).get(table_name)
        if table_meta is None:
            return {"error": f"Table '{table_name}' not found in data dictionary."}

        db_columns: list[dict] = []
        try:
            db_columns = db_manager.describe_table(table_name)
        except Exception as exc:
            logger.warning("DB describe failed for %s: %s", table_name, exc)

        db_type_map = {col["column_name"]: col for col in db_columns}

        columns: list[dict[str, Any]] = []
        for col in table_meta.get("columns", []):
            col_name = col["name"]
            db_col = db_type_map.get(col_name, {})
            columns.append({
                "name": col_name,
                "type": col.get("type", db_col.get("data_type", "UNKNOWN")),
                "description": col.get("description", ""),
                "nullable": col.get("nullable", db_col.get("is_nullable") == "YES"),
                "example": col.get("example"),
            })

        return {
            "table_name": table_name,
            "description": table_meta.get("description", ""),
            "freshness": table_meta.get("freshness", ""),
            "columns": columns,
            "relationships": table_meta.get("relationships", []),
        }

    def get_table_relationships(self) -> list[dict[str, str]]:
        """Return all declared join paths across the schema."""
        relationships: list[dict[str, str]] = []
        for table_name, info in self._data_dict.get("tables", {}).items():
            for rel in info.get("relationships", []) or []:
                relationships.append({
                    "source": table_name,
                    "target": rel["target"],
                    "join": rel["join"],
                    "cardinality": rel.get("cardinality", ""),
                })
        return relationships

    def run_read_only_query(self, sql: str) -> list[dict]:
        """Execute a read-only SQL statement and return rows as dicts."""
        try:
            return db_manager.execute_query(sql)
        except PermissionError as exc:
            return [{"error": str(exc)}]
        except Exception as exc:
            return [{"error": f"Query failed: {exc}"}]

    def explain_query(self, sql: str) -> str:
        """Return the DuckDB EXPLAIN plan for a query."""
        try:
            return db_manager.explain_query(sql)
        except PermissionError as exc:
            return f"Error: {exc}"
        except Exception as exc:
            return f"Explain failed: {exc}"

    def get_sample_rows(self, table_name: str, n: int = 5) -> list[dict]:
        """Return the first *n* rows of a table."""
        try:
            return db_manager.get_sample_rows(table_name, n)
        except Exception as exc:
            return [{"error": f"Failed to sample '{table_name}': {exc}"}]
