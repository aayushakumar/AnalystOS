from __future__ import annotations

from typing import Any, TypedDict


class AnalystOSState(TypedDict, total=False):
    # Input
    question: str
    session_id: str

    # Agent outputs
    intent: dict[str, Any]
    schema_pack: dict[str, Any]
    plan: dict[str, Any]
    sql_candidate: dict[str, Any]
    validation: dict[str, Any]
    query_results: dict[str, Any]
    analysis: dict[str, Any]
    critique: dict[str, Any]
    final_answer: dict[str, Any]

    # Clarification
    clarification_question: str
    needs_user_input: bool

    # Control flow
    retry_count: int
    max_retries: int
    error: str | None

    # Observability
    trace_steps: list[dict[str, Any]]
    total_tokens: int
    total_cost: float
