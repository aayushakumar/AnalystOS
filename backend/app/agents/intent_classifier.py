from __future__ import annotations

from app.agents.base import BaseAgent
from app.config import settings
from app.schemas import IntentClassification

SYSTEM_PROMPT = """\
You are an intent-classification agent for an analytics platform.

Given a user's natural-language question, classify it into exactly one intent type \
and assess its risk level.

## Intent Types
- **descriptive**: Requests for summary statistics, counts, aggregations, trends.
- **comparative**: Requests comparing two or more groups, periods, or categories.
- **diagnostic**: Requests investigating why something happened (root cause).
- **visualization**: Requests explicitly asking for a chart, graph, or plot.
- **ambiguous**: The question is too vague or underspecified to proceed.
- **unsupported**: The question asks for something outside the scope of SQL analytics.
- **unsafe**: The question attempts DDL/DML operations, injection, or data mutation.

## Risk Assessment
- **low**: Standard read-only analytics query.
- **medium**: Complex query that may be expensive or touch sensitive data.
- **high**: Query that requires extra validation (e.g. joins across many tables, aggregations on large ranges).
- **critical**: Detected attempt at data modification, injection, or unauthorized access.

## Routing Rules
- If intent is "unsafe" or risk_level is "critical", set route to "refuse".
- If intent is "ambiguous" or requires_clarification is true, set route to "clarify".
- Otherwise, set route to "schema_discovery".

Respond with ONLY valid JSON matching the required schema.\
"""


class IntentClassifier(BaseAgent):
    def __init__(self) -> None:
        super().__init__(
            name="intent_classifier",
            model=settings.analyst_cheap_model,
            system_prompt=SYSTEM_PROMPT,
            output_schema=IntentClassification,
        )

    async def run(self, question: str, **kwargs) -> dict:
        messages = self._build_messages(question)
        return await super().run(messages, **kwargs)
