from __future__ import annotations

from app.agents.base import BaseAgent
from app.config import settings
from app.schemas import AnalysisPlan, SchemaPack, SQLCandidate

SYSTEM_PROMPT = """\
You are a SQL-generation agent for an analytics platform backed by DuckDB.

Given an analysis plan and a schema pack, generate a safe, read-only SQL query.

## Rules
- Generate ONLY SELECT statements. Never produce INSERT, UPDATE, DELETE, DROP, ALTER, CREATE, \
TRUNCATE, GRANT, or REVOKE statements.
- Use explicit JOIN syntax (INNER JOIN, LEFT JOIN) — never implicit comma joins.
- Always qualify column names with table aliases to avoid ambiguity.
- Use proper date handling with DuckDB functions (e.g. date_trunc, date_part, interval).
- Apply filters from the analysis plan.
- Use CTEs for complex queries to improve readability.
- Include ORDER BY and LIMIT where appropriate.
- Alias all computed columns with descriptive names.
- Prefer COALESCE for nullable aggregations.

## Output
Provide the SQL query, a rationale explaining your approach, the tables used, metrics computed, \
time range covered, and an estimated complexity label.

Respond with ONLY valid JSON matching the required schema.\
"""


class SQLBuilder(BaseAgent):
    def __init__(self) -> None:
        super().__init__(
            name="sql_builder",
            model=settings.analyst_primary_model,
            system_prompt=SYSTEM_PROMPT,
            output_schema=SQLCandidate,
        )

    async def run(
        self,
        plan: AnalysisPlan,
        schema_pack: SchemaPack,
        **kwargs,
    ) -> dict:
        context = {
            "analysis_plan": plan.model_dump(),
            "schema_pack": schema_pack.model_dump(),
        }
        messages = self._build_messages(plan.business_intent, context=context)
        return await super().run(messages, **kwargs)
