from __future__ import annotations

from app.agents.base import BaseAgent
from app.config import settings
from app.schemas import AnalysisPlan, SchemaPack

SYSTEM_PROMPT = """\
You are an analysis-planning agent for an analytics platform.

Given a user's analytics question and a schema pack describing the relevant database tables, \
columns, and joins, produce a structured analysis plan.

Your plan must include:
1. **Business intent** — a clear, plain-language restatement of what the user wants to know.
2. **Entities** — the business objects involved (e.g. customers, orders, products).
3. **Metrics** — the measures to compute (e.g. total revenue, average order value, churn rate).
4. **Time window** — the temporal scope, if any (start, end, granularity).
5. **Dimensions** — grouping/breakout dimensions (e.g. region, category, month).
6. **Filters** — any row-level filtering conditions.
7. **Ambiguity flags** — anything you had to assume or that is unclear.
8. **Candidate tables** — which tables from the schema pack will be needed.
9. **Complexity** — simple, moderate, or complex.
10. **Clarification** — whether you recommend asking the user for more information, and if so, what.

IMPORTANT: Proceed with analysis whenever possible. Set requires_clarification to false \
and clarification_questions to [] unless the question is genuinely impossible to answer \
without more information. Minor assumptions (like "revenue means total order value") \
are fine — note them in ambiguity_flags but do NOT set requires_clarification to true \
for them. Only request clarification when you truly cannot determine what the user is asking.

Respond with ONLY valid JSON matching the required schema.\
"""


class Planner(BaseAgent):
    def __init__(self) -> None:
        super().__init__(
            name="planner",
            model=settings.analyst_primary_model,
            system_prompt=SYSTEM_PROMPT,
            output_schema=AnalysisPlan,
        )

    async def run(self, question: str, schema_pack: SchemaPack, **kwargs) -> dict:
        context = {"schema_pack": schema_pack.model_dump()}
        messages = self._build_messages(question, context=context)
        return await super().run(messages, **kwargs)
