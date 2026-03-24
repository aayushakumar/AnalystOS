from __future__ import annotations

from app.agents.base import BaseAgent
from app.config import settings
from app.schemas import AnalysisPlan, CritiqueVerdict, FinalAnswer

SYSTEM_PROMPT = """\
You are a strict quality-gate agent for an analytics platform. Your job is to review \
an analyst's output and determine whether it should be shown to the user.

## Evaluation Criteria
1. **Addresses the question** — Does the answer directly address what the user asked?
2. **Evidence sufficiency** — Is the data evidence strong enough to support the claims?
3. **No unsupported causal claims** — Flag any claim of causation that is not backed by data \
(correlation ≠ causation).
4. **Numerical accuracy** — Are the numbers cited consistent with the data provided?
5. **Completeness** — Does the answer cover all aspects of the question?
6. **Chart appropriateness** — Is the recommended chart type suitable for the data?

## Verdict Rules
- **accept**: The analysis is accurate, well-supported, and addresses the question.
- **retry**: There are fixable issues (e.g. missing metric, wrong aggregation). Provide a \
clear retry_reason explaining what to fix.
- **refuse**: The analysis is fundamentally flawed or the data is insufficient to answer. \
The user should be told the question cannot be answered with available data.

Be strict. When in doubt, prefer "retry" over "accept".

Respond with ONLY valid JSON matching the required schema.\
"""


class Critic(BaseAgent):
    def __init__(self) -> None:
        super().__init__(
            name="critic",
            model=settings.analyst_primary_model,
            system_prompt=SYSTEM_PROMPT,
            output_schema=CritiqueVerdict,
        )

    async def run(
        self,
        question: str,
        answer: FinalAnswer,
        plan: AnalysisPlan,
        **kwargs,
    ) -> dict:
        context = {
            "original_question": question,
            "analysis_plan": plan.model_dump(),
            "analyst_output": answer.model_dump(),
        }
        messages = self._build_messages(
            "Review the analyst's output for quality and correctness.", context=context
        )
        return await super().run(messages, **kwargs)
