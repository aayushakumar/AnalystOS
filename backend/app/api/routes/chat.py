from __future__ import annotations

import asyncio
import json
import logging
import uuid
from typing import Any

from fastapi import APIRouter
from pydantic import BaseModel
from sse_starlette.sse import EventSourceResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/chat", tags=["chat"])

_sessions: dict[str, dict[str, Any]] = {}


class ChatRequest(BaseModel):
    question: str
    session_id: str | None = None


class ChatResponse(BaseModel):
    session_id: str
    status: str


@router.post("")
async def create_chat(request: ChatRequest) -> ChatResponse:
    session_id = request.session_id or uuid.uuid4().hex
    _sessions[session_id] = {"question": request.question, "status": "processing", "state": {}}
    asyncio.create_task(_run_workflow(session_id, request.question))
    return ChatResponse(session_id=session_id, status="processing")


async def _run_workflow(session_id: str, question: str) -> None:
    from app.graph.workflow import run_workflow
    from app.tracing.store import trace_store

    try:
        logger.info("Starting workflow for session %s: %s", session_id, question[:80])
        state = await run_workflow(question, session_id)
        logger.info(
            "Workflow done for %s — steps: %d, tokens: %d, error: %s",
            session_id,
            len(state.get("trace_steps", [])),
            state.get("total_tokens", 0),
            state.get("error"),
        )
        _sessions[session_id] = {
            **_sessions.get(session_id, {}),
            "status": "done",
            "state": state,
        }
        trace_data = {
            "trace_id": session_id,
            "session_id": session_id,
            "question": question,
            "started_at": 0,
            "ended_at": 0,
            "total_tokens": state.get("total_tokens", 0),
            "total_latency_ms": sum(
                s.get("latency_ms", 0) for s in state.get("trace_steps", [])
            ),
            "total_cost": state.get("total_cost", 0),
            "steps": state.get("trace_steps", []),
            "final_answer": state.get("final_answer"),
            "error": state.get("error"),
        }
        trace_store.save_trace(trace_data)
    except Exception as exc:
        logger.exception("Workflow failed for session %s", session_id)
        _sessions[session_id] = {
            **_sessions.get(session_id, {}),
            "status": "error",
            "error": str(exc),
        }


async def _event_generator(session_id: str):
    session = _sessions.get(session_id)
    if not session:
        yield {"data": json.dumps({"type": "error", "data": {"message": "Session not found"}})}
        return

    last_step_count = 0
    max_wait = 300

    for _ in range(max_wait):
        session = _sessions.get(session_id, {})
        status = session.get("status", "processing")

        state = session.get("state", {})
        steps = state.get("trace_steps", [])

        while last_step_count < len(steps):
            step = steps[last_step_count]
            yield {
                "data": json.dumps({
                    "type": "step",
                    "data": {
                        "agent": step.get("agent", "unknown"),
                        "latency_ms": step.get("latency_ms", 0),
                        "prompt_tokens": step.get("prompt_tokens", 0),
                        "completion_tokens": step.get("completion_tokens", 0),
                    },
                })
            }
            last_step_count += 1

        if status == "done":
            final_answer = state.get("final_answer")
            clarification = state.get("clarification_question")

            if state.get("needs_user_input") and clarification:
                yield {
                    "data": json.dumps({
                        "type": "clarification",
                        "data": {"question": clarification},
                    })
                }
            elif final_answer:
                yield {
                    "data": json.dumps({
                        "type": "answer",
                        "data": final_answer,
                    })
                }
            else:
                yield {
                    "data": json.dumps({
                        "type": "answer",
                        "data": {
                            "answer_text": state.get("error", "Analysis complete."),
                            "confidence": "low",
                        },
                    })
                }
            _sessions.pop(session_id, None)
            return

        if status == "error":
            yield {
                "data": json.dumps({
                    "type": "error",
                    "data": {"message": session.get("error", "Unknown error")},
                })
            }
            _sessions.pop(session_id, None)
            return

        await asyncio.sleep(0.5)

    yield {"data": json.dumps({"type": "error", "data": {"message": "Timeout"}})}
    _sessions.pop(session_id, None)


@router.get("/{session_id}/stream")
async def stream_chat(session_id: str) -> EventSourceResponse:
    return EventSourceResponse(_event_generator(session_id))
