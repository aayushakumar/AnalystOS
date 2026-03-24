import type { SSEEvent, Trace, TraceStep, EvalReport } from "./types";

const API_BASE =
  process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api";

export async function sendQuestion(
  question: string,
  sessionId?: string
): Promise<{ session_id: string }> {
  const res = await fetch(`${API_BASE}/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ question, session_id: sessionId }),
  });
  if (!res.ok) {
    throw new Error(`Failed to send question: ${res.statusText}`);
  }
  return res.json();
}

export function streamChat(
  sessionId: string,
  onEvent: (event: SSEEvent) => void
): () => void {
  const url = `${API_BASE}/chat/${sessionId}/stream`;
  const eventSource = new EventSource(url);

  eventSource.onmessage = (event) => {
    try {
      const parsed: SSEEvent = JSON.parse(event.data);
      onEvent(parsed);
    } catch {
      onEvent({ type: "error", data: "Failed to parse SSE event" });
    }
  };

  eventSource.addEventListener("step", (event) => {
    try {
      onEvent({ type: "step", data: JSON.parse(event.data) });
    } catch {
      onEvent({ type: "error", data: "Failed to parse step event" });
    }
  });

  eventSource.addEventListener("answer", (event) => {
    try {
      onEvent({ type: "answer", data: JSON.parse(event.data) });
    } catch {
      onEvent({ type: "error", data: "Failed to parse answer event" });
    }
  });

  eventSource.addEventListener("error", (event) => {
    if (event instanceof MessageEvent) {
      onEvent({ type: "error", data: event.data });
    }
  });

  eventSource.onerror = () => {
    eventSource.close();
  };

  return () => eventSource.close();
}

function normalizeStep(raw: Record<string, unknown>): TraceStep {
  return {
    agent_name: (raw.agent_name ?? raw.agent ?? "unknown") as string,
    started_at: (raw.started_at ?? "") as string,
    ended_at: (raw.ended_at ?? "") as string,
    duration_ms: (raw.duration_ms ?? raw.latency_ms ?? 0) as number,
    tokens_used:
      (raw.tokens_used ??
        ((raw.prompt_tokens as number) ?? 0) +
          ((raw.completion_tokens as number) ?? 0)) as number,
    input_summary: (raw.input_summary ?? "") as string,
    output_summary: (raw.output_summary ?? "") as string,
    tools_called: (raw.tools_called ?? []) as string[],
    skills_activated: (raw.skills_activated ?? []) as string[],
    error: (raw.error ?? null) as string | null,
  };
}

export async function getTrace(traceId: string): Promise<Trace> {
  const res = await fetch(`${API_BASE}/traces/${traceId}`);
  if (!res.ok) throw new Error(`Failed to fetch trace: ${res.statusText}`);
  const data = await res.json();
  return {
    ...data,
    total_duration_ms: data.total_duration_ms ?? data.total_latency_ms ?? 0,
    steps: (data.steps ?? []).map(normalizeStep),
  };
}

export async function listTraces(): Promise<Trace[]> {
  const res = await fetch(`${API_BASE}/traces`);
  if (!res.ok) throw new Error(`Failed to list traces: ${res.statusText}`);
  return res.json();
}

export async function runEval(): Promise<{ status: string }> {
  const res = await fetch(`${API_BASE}/eval/run`, { method: "POST" });
  if (!res.ok) throw new Error(`Failed to run eval: ${res.statusText}`);
  return res.json();
}

export async function getEvalResults(): Promise<EvalReport> {
  const res = await fetch(`${API_BASE}/eval/results`);
  if (!res.ok) throw new Error(`Failed to get eval results: ${res.statusText}`);
  return res.json();
}
