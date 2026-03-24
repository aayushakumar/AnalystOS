from typing import Any

from fastapi import APIRouter, HTTPException

router = APIRouter(prefix="/traces", tags=["traces"])


@router.get("")
async def list_traces(limit: int = 50, offset: int = 0) -> list[dict[str, Any]]:
    from app.tracing.store import trace_store

    return trace_store.list_traces(limit=limit, offset=offset)


@router.get("/stats")
async def get_trace_stats() -> dict[str, Any]:
    from app.tracing.store import trace_store

    return trace_store.get_trace_stats()


@router.get("/{trace_id}")
async def get_trace(trace_id: str) -> dict[str, Any]:
    from app.tracing.store import trace_store

    trace = trace_store.get_trace(trace_id)
    if not trace:
        raise HTTPException(status_code=404, detail=f"Trace {trace_id} not found")
    return trace
