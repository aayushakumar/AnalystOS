from __future__ import annotations

from app.agents.base import BaseAgent
from app.config import settings
from app.db.connection import db_manager
from app.schemas import SchemaPack

SYSTEM_PROMPT = """\
You are a schema-discovery agent for an analytics platform backed by a SQL database.

Given a user's analytics question and the available database schema, identify:
1. **Tables** relevant to answering the question (with descriptions and approximate row counts).
2. **Columns** needed from each table (with data types, descriptions, and representative sample values).
3. **Joins** required to connect the relevant tables (specifying left/right tables, columns, and join type).
4. **Relevant metrics** — business measures that the query should compute.
5. **Data freshness** — a brief note on how recent the data is, based on date columns.

Be precise. Only include tables and columns that are directly relevant. Prefer inner joins \
unless there is a reason to use outer joins.

Respond with ONLY valid JSON matching the required schema.\
"""


class SchemaScout(BaseAgent):
    def __init__(self) -> None:
        super().__init__(
            name="schema_scout",
            model=settings.analyst_cheap_model,
            system_prompt=SYSTEM_PROMPT,
            output_schema=SchemaPack,
        )

    async def run(self, question: str, **kwargs) -> dict:
        schema_context = self._gather_schema()
        messages = self._build_messages(question, context=schema_context)
        return await super().run(messages, **kwargs)

    def _gather_schema(self) -> dict:
        tables = db_manager.get_table_names()
        schema_info: dict = {"tables": {}}
        for table in tables:
            cols = db_manager.describe_table(table)
            schema_info["tables"][table] = {
                "columns": [
                    {"name": c["column_name"], "type": c["data_type"]}
                    for c in cols
                ],
            }
        return schema_info
