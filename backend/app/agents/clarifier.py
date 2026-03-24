from __future__ import annotations

from app.agents.base import BaseAgent
from app.config import settings

SYSTEM_PROMPT = """\
You are a clarification agent for an analytics platform.

When an analytics question is ambiguous or underspecified, you generate a concise, helpful \
follow-up question to ask the user. Your goal is to ask the *minimum* needed to proceed \
with a meaningful analysis.

Guidelines:
- Ask ONE focused question (not a laundry list).
- Offer concrete options when possible (e.g. "Did you mean revenue or profit?").
- Provide a sensible default assumption so the user can simply confirm.
- Never ask for information the system already has (e.g. available tables).
- Keep the tone conversational and helpful.

Respond with ONLY valid JSON in this format:
{"clarification_question": "your question here"}\
"""


class Clarifier(BaseAgent):
    def __init__(self) -> None:
        super().__init__(
            name="clarifier",
            model=settings.analyst_cheap_model,
            system_prompt=SYSTEM_PROMPT,
            output_schema=None,
        )

    async def run(self, question: str, ambiguity_flags: list[str] | None = None, **kwargs) -> dict:
        context = {}
        if ambiguity_flags:
            context["ambiguity_flags"] = ambiguity_flags
        messages = self._build_messages(question, context=context if context else None)
        result = await super().run(messages, **kwargs)
        raw = result["output"]
        import json

        try:
            parsed = json.loads(raw)
            result["output"] = parsed
        except (json.JSONDecodeError, TypeError):
            result["output"] = {"clarification_question": raw}
        return result
