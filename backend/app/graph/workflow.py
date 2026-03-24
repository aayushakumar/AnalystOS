from __future__ import annotations

import uuid

from langgraph.graph import END, StateGraph

from app.graph.nodes import (
    analyze_results,
    ask_clarification,
    build_final_answer,
    classify_intent,
    create_plan,
    critique_analysis,
    discover_schema,
    execute_query,
    generate_sql,
    refuse_request,
    validate_sql,
)
from app.graph.state import AnalystOSState


# ---------------------------------------------------------------------------
# Routing functions (pure, no side-effects)
# ---------------------------------------------------------------------------


def route_after_intent(state: AnalystOSState) -> str:
    if state.get("error"):
        return "refuse_request"
    intent = state.get("intent", {})
    route = intent.get("route", "schema_discovery")
    if route == "refuse":
        return "refuse_request"
    if route == "clarify":
        return "ask_clarification"
    return "discover_schema"


def route_after_plan(state: AnalystOSState) -> str:
    if state.get("error"):
        return "refuse_request"
    plan = state.get("plan", {})
    if plan.get("requires_clarification") and len(plan.get("clarification_questions", [])) > 0:
        return "ask_clarification"
    return "generate_sql"


def route_after_validation(state: AnalystOSState) -> str:
    if state.get("error"):
        return "refuse_request"
    validation = state.get("validation", {})
    if validation.get("valid"):
        return "execute_query"
    if validation.get("requires_retry"):
        if state.get("retry_count", 0) < state.get("max_retries", 3):
            return "generate_sql"
    return "refuse_request"


def route_after_critique(state: AnalystOSState) -> str:
    if state.get("error"):
        return "build_final_answer"
    critique = state.get("critique", {})
    verdict = critique.get("verdict", "accept")
    if verdict == "accept":
        return "build_final_answer"
    if verdict == "retry":
        if state.get("retry_count", 0) < state.get("max_retries", 3):
            return "generate_sql"
    return "build_final_answer"


# ---------------------------------------------------------------------------
# Graph construction
# ---------------------------------------------------------------------------


def build_workflow() -> StateGraph:
    graph = StateGraph(AnalystOSState)

    # --- Nodes ---
    graph.add_node("classify_intent", classify_intent)
    graph.add_node("discover_schema", discover_schema)
    graph.add_node("create_plan", create_plan)
    graph.add_node("ask_clarification", ask_clarification)
    graph.add_node("generate_sql", generate_sql)
    graph.add_node("validate_sql", validate_sql)
    graph.add_node("execute_query", execute_query)
    graph.add_node("analyze_results", analyze_results)
    graph.add_node("critique_analysis", critique_analysis)
    graph.add_node("build_final_answer", build_final_answer)
    graph.add_node("refuse_request", refuse_request)

    # --- Entry point ---
    graph.set_entry_point("classify_intent")

    # --- Edges ---

    graph.add_conditional_edges(
        "classify_intent",
        route_after_intent,
        {
            "refuse_request": "refuse_request",
            "ask_clarification": "ask_clarification",
            "discover_schema": "discover_schema",
        },
    )

    graph.add_edge("discover_schema", "create_plan")

    graph.add_conditional_edges(
        "create_plan",
        route_after_plan,
        {
            "ask_clarification": "ask_clarification",
            "generate_sql": "generate_sql",
            "refuse_request": "refuse_request",
        },
    )

    graph.add_edge("ask_clarification", END)

    graph.add_edge("generate_sql", "validate_sql")

    graph.add_conditional_edges(
        "validate_sql",
        route_after_validation,
        {
            "execute_query": "execute_query",
            "generate_sql": "generate_sql",
            "refuse_request": "refuse_request",
        },
    )

    graph.add_edge("execute_query", "analyze_results")
    graph.add_edge("analyze_results", "critique_analysis")

    graph.add_conditional_edges(
        "critique_analysis",
        route_after_critique,
        {
            "build_final_answer": "build_final_answer",
            "generate_sql": "generate_sql",
        },
    )

    graph.add_edge("build_final_answer", END)
    graph.add_edge("refuse_request", END)

    return graph


workflow = build_workflow().compile()


async def run_workflow(question: str, session_id: str | None = None) -> dict:
    """Run the full analyst pipeline and return the final state."""
    initial_state: AnalystOSState = {
        "question": question,
        "session_id": session_id or uuid.uuid4().hex,
        "retry_count": 0,
        "max_retries": 3,
        "trace_steps": [],
        "total_tokens": 0,
        "total_cost": 0.0,
    }
    return await workflow.ainvoke(initial_state)
