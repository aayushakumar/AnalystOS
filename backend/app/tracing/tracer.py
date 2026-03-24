from __future__ import annotations

import time
import uuid
from contextlib import asynccontextmanager
from dataclasses import dataclass, field
from typing import Any

MODEL_PRICING: dict[str, dict[str, float]] = {
    "gpt-4o": {"input": 2.50 / 1_000_000, "output": 10.00 / 1_000_000},
    "gpt-4o-mini": {"input": 0.15 / 1_000_000, "output": 0.60 / 1_000_000},
    "claude-sonnet-4-20250514": {"input": 3.00 / 1_000_000, "output": 15.00 / 1_000_000},
    "groq/llama-3.3-70b-versatile": {"input": 0.0, "output": 0.0},
    "groq/llama-3.1-8b-instant": {"input": 0.0, "output": 0.0},
}


def estimate_cost(model: str, tokens_in: int, tokens_out: int) -> float:
    pricing = MODEL_PRICING.get(model)
    if pricing is None:
        return 0.0
    return round(
        tokens_in * pricing["input"] + tokens_out * pricing["output"],
        8,
    )


@dataclass
class TraceStep:
    agent_name: str
    started_at: float
    ended_at: float = 0.0
    latency_ms: float = 0.0
    input_summary: str = ""
    output_summary: str = ""
    tools_called: list[str] = field(default_factory=list)
    skills_activated: list[str] = field(default_factory=list)
    mcp_resources_used: list[str] = field(default_factory=list)
    tokens_in: int = 0
    tokens_out: int = 0
    model_used: str = ""
    error: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "agent_name": self.agent_name,
            "started_at": self.started_at,
            "ended_at": self.ended_at,
            "latency_ms": self.latency_ms,
            "input_summary": self.input_summary,
            "output_summary": self.output_summary,
            "tools_called": self.tools_called,
            "skills_activated": self.skills_activated,
            "mcp_resources_used": self.mcp_resources_used,
            "tokens_in": self.tokens_in,
            "tokens_out": self.tokens_out,
            "model_used": self.model_used,
            "error": self.error,
        }


@dataclass
class Trace:
    trace_id: str
    session_id: str
    question: str
    started_at: float
    ended_at: float = 0.0
    steps: list[TraceStep] = field(default_factory=list)
    total_tokens: int = 0
    total_latency_ms: float = 0.0
    total_cost: float = 0.0
    final_answer: dict[str, Any] | None = None
    error: str | None = None

    def add_step(self, step: TraceStep) -> None:
        self.steps.append(step)
        self.total_tokens += step.tokens_in + step.tokens_out
        self.total_cost += estimate_cost(step.model_used, step.tokens_in, step.tokens_out)

    def finalize(self) -> None:
        self.ended_at = time.time()
        self.total_latency_ms = round((self.ended_at - self.started_at) * 1000, 1)

    def to_dict(self) -> dict[str, Any]:
        return {
            "trace_id": self.trace_id,
            "session_id": self.session_id,
            "question": self.question,
            "started_at": self.started_at,
            "ended_at": self.ended_at,
            "steps": [s.to_dict() for s in self.steps],
            "total_tokens": self.total_tokens,
            "total_latency_ms": self.total_latency_ms,
            "total_cost": self.total_cost,
            "final_answer": self.final_answer,
            "error": self.error,
        }


@asynccontextmanager
async def trace_context(question: str, session_id: str):
    """Context manager that creates and manages a Trace."""
    trace = Trace(
        trace_id=uuid.uuid4().hex,
        session_id=session_id,
        question=question,
        started_at=time.time(),
    )
    try:
        yield trace
    except Exception as exc:
        trace.error = f"{type(exc).__name__}: {exc}"
        raise
    finally:
        trace.finalize()


@asynccontextmanager
async def trace_step(trace: Trace, agent_name: str):
    """Context manager for individual agent steps within a trace."""
    step = TraceStep(agent_name=agent_name, started_at=time.time())
    try:
        yield step
    except Exception as exc:
        step.error = f"{type(exc).__name__}: {exc}"
        raise
    finally:
        step.ended_at = time.time()
        step.latency_ms = round((step.ended_at - step.started_at) * 1000, 1)
        trace.add_step(step)
