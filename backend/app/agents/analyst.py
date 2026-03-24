from __future__ import annotations

import json
from typing import Any

from app.agents.base import BaseAgent
from app.config import settings
from app.schemas import AnalysisPlan, ChartSpec, Confidence, FinalAnswer

SYSTEM_PROMPT = """\
You are an analytics interpretation agent. Given query results, the original user question, \
and the analysis plan, produce a comprehensive answer.

CRITICAL REQUIREMENTS:
1. **answer_text** — Write a DETAILED natural-language paragraph (at least 2-3 sentences) that \
directly answers the user's question with specific numbers from the data. NEVER return generic \
text like "Analysis complete" or "Here are the results". Always cite actual values from the data.

2. **insights** — Provide at least 3 bullet-point insights drawn from the data. Each insight \
MUST cite specific numbers (e.g. "$1,234.56", "42%", "7,431 orders"). Look for: highest/lowest \
values, notable differences, trends, and totals.

3. **chart_spec** — Recommend a visualization:
   - chart_type: one of "bar", "line", "pie", "scatter", "table", "histogram", "stacked_bar", "area"
   - title: descriptive chart title
   - x_field / y_field: column names from the result data
   - color_field: optional grouping column
   - annotations: notable callouts
   - data: copy the actual data rows from query_results into this field

4. **sql_used** — Copy the SQL query from the context.
5. **evidence** — List data points that support your answer.
6. **confidence** — "high" if data is complete and query is straightforward, "medium" if some \
assumptions were made, "low" if data is insufficient.
7. **limitations** — Any caveats or assumptions.
8. **trace_id** — Set to empty string.

IMPORTANT: The answer_text field must contain a substantive, human-readable answer. \
Read the query_results data carefully and summarize the key findings with numbers.

Respond with ONLY valid JSON matching the required schema.\
"""


class Analyst(BaseAgent):
    def __init__(self) -> None:
        super().__init__(
            name="analyst",
            model=settings.analyst_primary_model,
            system_prompt=SYSTEM_PROMPT,
            output_schema=FinalAnswer,
        )

    async def run(
        self,
        question: str,
        data: list[dict[str, Any]],
        sql_used: str,
        plan: AnalysisPlan,
        **kwargs,
    ) -> dict:
        preview = data[:50] if len(data) > 50 else data
        context = {
            "query_results": preview,
            "total_rows": len(data),
            "sql_used": sql_used,
            "analysis_plan": plan.model_dump(),
        }
        messages = self._build_messages(question, context=context)
        return await super().run(messages, **kwargs)
