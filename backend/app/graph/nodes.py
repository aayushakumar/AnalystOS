from __future__ import annotations

import time
import uuid
from typing import Any

from app.graph.state import AnalystOSState
from app.schemas import (
    AnalysisPlan,
    FinalAnswer,
    SchemaPack,
    SQLCandidate,
    ValidationReport,
)


def _trace_step(
    agent_name: str,
    latency_ms: float,
    usage: dict[str, int] | None = None,
) -> dict[str, Any]:
    step: dict[str, Any] = {
        "agent": agent_name,
        "latency_ms": latency_ms,
        "timestamp": time.time(),
    }
    if usage:
        step["prompt_tokens"] = usage.get("prompt_tokens", 0)
        step["completion_tokens"] = usage.get("completion_tokens", 0)
    return step


def _append_trace(state: AnalystOSState, step: dict[str, Any]) -> list[dict[str, Any]]:
    return [*state.get("trace_steps", []), step]


def _add_tokens(state: AnalystOSState, usage: dict[str, int] | None) -> int:
    prev = state.get("total_tokens", 0)
    if not usage:
        return prev
    return prev + usage.get("prompt_tokens", 0) + usage.get("completion_tokens", 0)


# ---------------------------------------------------------------------------
# Node functions
# ---------------------------------------------------------------------------


async def classify_intent(state: AnalystOSState) -> dict[str, Any]:
    from app.agents.intent_classifier import IntentClassifier

    try:
        agent = IntentClassifier()
        result = await agent.run(state["question"])
        output = result["output"]
        step = _trace_step("intent_classifier", result["latency_ms"], result["usage"])
        return {
            "intent": output.model_dump(),
            "trace_steps": _append_trace(state, step),
            "total_tokens": _add_tokens(state, result["usage"]),
        }
    except Exception as exc:
        return {"error": f"Intent classification failed: {exc}"}


async def discover_schema(state: AnalystOSState) -> dict[str, Any]:
    from app.agents.schema_scout import SchemaScout

    if state.get("error"):
        return {}
    try:
        agent = SchemaScout()
        result = await agent.run(state["question"])
        output = result["output"]
        step = _trace_step("schema_scout", result["latency_ms"], result["usage"])
        return {
            "schema_pack": output.model_dump(),
            "trace_steps": _append_trace(state, step),
            "total_tokens": _add_tokens(state, result["usage"]),
        }
    except Exception as exc:
        return {"error": f"Schema discovery failed: {exc}"}


async def create_plan(state: AnalystOSState) -> dict[str, Any]:
    from app.agents.planner import Planner

    if state.get("error"):
        return {}
    try:
        agent = Planner()
        schema_pack = SchemaPack.model_validate(state["schema_pack"])
        result = await agent.run(state["question"], schema_pack)
        output = result["output"]
        step = _trace_step("planner", result["latency_ms"], result["usage"])
        return {
            "plan": output.model_dump(),
            "trace_steps": _append_trace(state, step),
            "total_tokens": _add_tokens(state, result["usage"]),
        }
    except Exception as exc:
        return {"error": f"Planning failed: {exc}"}


async def ask_clarification(state: AnalystOSState) -> dict[str, Any]:
    from app.agents.clarifier import Clarifier

    try:
        ambiguity_flags: list[str] = []
        plan = state.get("plan")
        intent = state.get("intent")
        if plan:
            ambiguity_flags = plan.get("ambiguity_flags", [])
            ambiguity_flags = [*ambiguity_flags, *plan.get("clarification_questions", [])]
        elif intent:
            ambiguity_flags = [intent.get("reasoning", "Ambiguous query")]

        agent = Clarifier()
        result = await agent.run(state["question"], ambiguity_flags)
        output = result["output"]
        step = _trace_step("clarifier", result["latency_ms"], result["usage"])
        return {
            "clarification_question": output.get(
                "clarification_question",
                "Could you please clarify your question?",
            ),
            "needs_user_input": True,
            "trace_steps": _append_trace(state, step),
            "total_tokens": _add_tokens(state, result["usage"]),
        }
    except Exception as exc:
        return {
            "clarification_question": "Could you please rephrase or clarify your question?",
            "needs_user_input": True,
            "error": f"Clarification agent failed: {exc}",
        }


async def generate_sql(state: AnalystOSState) -> dict[str, Any]:
    from app.agents.sql_builder import SQLBuilder

    if state.get("error"):
        return {}
    try:
        retry_count = state.get("retry_count", 0)
        if state.get("sql_candidate") is not None:
            retry_count += 1

        agent = SQLBuilder()
        plan = AnalysisPlan.model_validate(state["plan"])
        schema_pack = SchemaPack.model_validate(state["schema_pack"])
        result = await agent.run(plan, schema_pack)
        output = result["output"]
        step = _trace_step("sql_builder", result["latency_ms"], result["usage"])
        return {
            "sql_candidate": output.model_dump(),
            "retry_count": retry_count,
            "trace_steps": _append_trace(state, step),
            "total_tokens": _add_tokens(state, result["usage"]),
        }
    except Exception as exc:
        return {"error": f"SQL generation failed: {exc}"}


async def validate_sql(state: AnalystOSState) -> dict[str, Any]:
    from app.agents.validator import Validator

    if state.get("error"):
        return {}
    try:
        agent = Validator()
        sql_candidate = SQLCandidate.model_validate(state["sql_candidate"])
        result = await agent.run(sql_candidate, use_llm_review=False)
        output = result["output"]
        step = _trace_step("validator", result["latency_ms"], result["usage"])
        return {
            "validation": output.model_dump(),
            "trace_steps": _append_trace(state, step),
            "total_tokens": _add_tokens(state, result["usage"]),
        }
    except Exception as exc:
        return {"error": f"SQL validation failed: {exc}"}


async def execute_query(state: AnalystOSState) -> dict[str, Any]:
    from app.agents.executor import QueryExecutor

    if state.get("error"):
        return {}
    try:
        executor = QueryExecutor()
        sql = state["sql_candidate"]["sql"]
        result = await executor.run(sql)

        if result.get("error"):
            return {"error": f"Query execution failed: {result['error']}"}

        output = result["output"]
        step = _trace_step("query_executor", output.get("execution_ms", 0))
        return {
            "query_results": output,
            "trace_steps": _append_trace(state, step),
        }
    except Exception as exc:
        return {"error": f"Query execution failed: {exc}"}


async def analyze_results(state: AnalystOSState) -> dict[str, Any]:
    from app.agents.analyst import Analyst

    if state.get("error"):
        return {}
    try:
        agent = Analyst()
        plan = AnalysisPlan.model_validate(state["plan"])
        data = state.get("query_results", {}).get("data", [])
        sql_used = state.get("sql_candidate", {}).get("sql", "")
        result = await agent.run(
            question=state["question"],
            data=data,
            sql_used=sql_used,
            plan=plan,
        )
        output = result["output"]
        step = _trace_step("analyst", result["latency_ms"], result["usage"])
        return {
            "analysis": output.model_dump() if hasattr(output, "model_dump") else output,
            "trace_steps": _append_trace(state, step),
            "total_tokens": _add_tokens(state, result["usage"]),
        }
    except Exception as exc:
        return {"error": f"Analysis failed: {exc}"}


async def critique_analysis(state: AnalystOSState) -> dict[str, Any]:
    from app.agents.critic import Critic

    if state.get("error"):
        return {}
    try:
        agent = Critic()
        plan = AnalysisPlan.model_validate(state["plan"])
        analysis = state.get("analysis", {})
        answer = FinalAnswer.model_validate(analysis) if isinstance(analysis, dict) else analysis
        result = await agent.run(
            question=state["question"],
            answer=answer,
            plan=plan,
        )
        output = result["output"]
        step = _trace_step("critic", result["latency_ms"], result["usage"])
        return {
            "critique": output.model_dump(),
            "trace_steps": _append_trace(state, step),
            "total_tokens": _add_tokens(state, result["usage"]),
        }
    except Exception as exc:
        return {"error": f"Critique failed: {exc}"}


def _fallback_summary(question: str, query_results: dict) -> tuple[str, list[str]]:
    """Build a basic NL summary from raw query data when the analyst returns nothing useful."""
    data = query_results.get("data", [])
    if not data:
        return "No data was returned for this query.", []

    row_count = len(data)
    cols = list(data[0].keys())
    lines = []
    for row in data[:10]:
        parts = [f"{k}: {v}" for k, v in row.items()]
        lines.append(", ".join(parts))

    summary = f"Based on {row_count} result row(s) for \"{question}\":\n" + "\n".join(f"  - {l}" for l in lines)
    if row_count > 10:
        summary += f"\n  ... and {row_count - 10} more rows."

    insights = [f"{cols[0]}: {data[i][cols[0]]} — {cols[-1]}: {data[i][cols[-1]]}" for i in range(min(3, len(data)))]
    return summary, insights


async def build_final_answer(state: AnalystOSState) -> dict[str, Any]:
    analysis = state.get("analysis", {})
    critique = state.get("critique", {})
    sql_candidate = state.get("sql_candidate", {})
    validation = state.get("validation", {})
    query_results = state.get("query_results", {})

    confidence_score = critique.get("confidence_score", 0.5)
    if confidence_score >= 0.8:
        confidence = "high"
    elif confidence_score >= 0.5:
        confidence = "medium"
    else:
        confidence = "low"

    if critique.get("verdict") not in (None, "accept"):
        confidence = "low"

    limitations: list[str] = []
    if critique.get("issues"):
        limitations.extend(critique["issues"])
    if validation.get("risk_notes"):
        limitations.extend(validation["risk_notes"])

    evidence: list[str] = []
    if validation.get("tables_verified"):
        evidence.append(f"Verified tables: {', '.join(validation['tables_verified'])}")
    if validation.get("columns_verified"):
        evidence.append(f"Verified columns: {', '.join(validation['columns_verified'])}")

    answer_text = analysis.get("answer_text", "")
    insights = analysis.get("insights", [])

    is_empty = not answer_text or answer_text.strip().lower() in (
        "analysis complete.", "analysis complete", "",
    )
    if is_empty:
        answer_text, insights = _fallback_summary(state.get("question", ""), query_results)

    final = FinalAnswer(
        answer_text=answer_text,
        insights=insights,
        chart_spec=analysis.get("chart_spec"),
        sql_used=sql_candidate.get("sql", ""),
        evidence=evidence,
        confidence=confidence,
        limitations=limitations,
        trace_id=state.get("session_id") or uuid.uuid4().hex,
    )
    return {"final_answer": final.model_dump()}


async def refuse_request(state: AnalystOSState) -> dict[str, Any]:
    intent = state.get("intent", {})
    error = state.get("error")
    validation = state.get("validation", {})

    if not error and validation and not validation.get("valid"):
        issues = validation.get("issues", [])
        issue_msgs = [i.get("message", "") if isinstance(i, dict) else str(i) for i in issues[:3]]
        reason = f"SQL validation failed after retries: {'; '.join(issue_msgs)}" if issue_msgs else "SQL validation failed after maximum retries."
    else:
        reason = error or intent.get("reasoning", "This request cannot be processed.")

    final = FinalAnswer(
        answer_text=f"I'm unable to process this request. {reason}",
        insights=[],
        chart_spec=None,
        sql_used="",
        evidence=[],
        confidence="low",
        limitations=[reason],
        trace_id=state.get("session_id") or uuid.uuid4().hex,
    )
    return {"final_answer": final.model_dump(), "error": None}
