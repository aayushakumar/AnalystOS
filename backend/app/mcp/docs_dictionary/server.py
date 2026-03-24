"""Docs & Dictionary MCP Server — exposes glossary, join guide, and metric definitions."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

import yaml

logger = logging.getLogger(__name__)

_DATA_DIR = Path(__file__).resolve().parent.parent.parent.parent / "data"
_DATA_DICT_PATH = _DATA_DIR / "ecommerce" / "data_dictionary.yaml"
_GLOSSARY_PATH = _DATA_DIR / "docs" / "business_glossary.md"
_JOIN_GUIDE_PATH = _DATA_DIR / "docs" / "join_guide.md"

_PROMPT_TEMPLATES: dict[str, str] = {
    "metric_lookup": (
        "You are a data analyst assistant. The user is asking about a specific metric.\n"
        "Use the canonical definition below to answer accurately.\n\n"
        "Metric: {metric_name}\n"
        "Definition: {description}\n"
        "SQL:\n```sql\n{sql}\n```\n"
        "Pitfalls:\n{pitfalls}\n\n"
        "Answer the user's question using ONLY this definition. "
        "If the question requires data beyond this metric, say so explicitly."
    ),
    "schema_exploration": (
        "You are a schema exploration assistant for an e-commerce analytics database.\n"
        "The user wants to understand the available tables and how they connect.\n\n"
        "Provide a clear summary of the schema, highlight approved join patterns, "
        "and warn about known anti-patterns. Use the join guide and data dictionary "
        "as your sole source of truth."
    ),
}


class DocsDictionaryServer:
    """MCP service that exposes documentation, glossary, and metric definitions."""

    def __init__(self) -> None:
        self._data_dict: dict[str, Any] = {}
        self._glossary: str = ""
        self._join_guide: str = ""
        self._load_resources()

    # ------------------------------------------------------------------
    # Initialisation
    # ------------------------------------------------------------------

    def _load_resources(self) -> None:
        self._data_dict = self._read_yaml(_DATA_DICT_PATH)
        self._glossary = self._read_text(_GLOSSARY_PATH)
        self._join_guide = self._read_text(_JOIN_GUIDE_PATH)

    @staticmethod
    def _read_yaml(path: Path) -> dict[str, Any]:
        try:
            with path.open() as f:
                return yaml.safe_load(f) or {}
        except FileNotFoundError:
            logger.warning("YAML file not found: %s", path)
            return {}
        except yaml.YAMLError as exc:
            logger.error("Failed to parse YAML %s: %s", path, exc)
            return {}

    @staticmethod
    def _read_text(path: Path) -> str:
        try:
            return path.read_text(encoding="utf-8")
        except FileNotFoundError:
            logger.warning("Text file not found: %s", path)
            return ""

    # ------------------------------------------------------------------
    # Resources / Tools
    # ------------------------------------------------------------------

    def get_data_dictionary(self) -> dict[str, Any]:
        """Return the full data dictionary (tables + metrics + pitfalls)."""
        return self._data_dict

    def get_business_glossary(self) -> str:
        """Return the business glossary as markdown."""
        return self._glossary

    def get_join_guide(self) -> str:
        """Return the join guide as markdown."""
        return self._join_guide

    def get_metric_definition(self, metric_name: str) -> dict[str, Any] | None:
        """Look up a single metric by name (case-insensitive)."""
        metrics: dict[str, Any] = self._data_dict.get("metrics", {})
        key = metric_name.lower().replace(" ", "_")
        metric = metrics.get(key)
        if metric is None:
            for k, v in metrics.items():
                if k.lower() == key:
                    return {"name": k, **v}
            return None
        return {"name": key, **metric}

    def get_metric_names(self) -> list[str]:
        """Return a sorted list of all defined metric names."""
        return sorted(self._data_dict.get("metrics", {}).keys())

    def get_prompt_template(self, template_name: str) -> str:
        """Return a named prompt template, or an empty string if not found."""
        return _PROMPT_TEMPLATES.get(template_name, "")
