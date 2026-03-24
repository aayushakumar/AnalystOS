"use client";

import { useState, useCallback, useRef } from "react";
import type { ChatMessage, FinalAnswer, Trace, TraceStep } from "@/lib/types";
import { sendQuestion, streamChat, getTrace } from "@/lib/api";

export function useChat() {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [currentTrace, setCurrentTrace] = useState<Trace | null>(null);
  const [liveSteps, setLiveSteps] = useState<TraceStep[]>([]);
  const sessionIdRef = useRef<string | null>(null);
  const cleanupRef = useRef<(() => void) | null>(null);

  const sendMessage = useCallback(async (question: string) => {
    const userMessage: ChatMessage = {
      id: crypto.randomUUID(),
      role: "user",
      content: question,
      timestamp: new Date().toISOString(),
    };

    setMessages((prev) => [...prev, userMessage]);
    setIsLoading(true);
    setLiveSteps([]);
    setCurrentTrace(null);

    try {
      const { session_id } = await sendQuestion(
        question,
        sessionIdRef.current ?? undefined
      );
      sessionIdRef.current = session_id;

      const cleanup = streamChat(session_id, (event) => {
        switch (event.type) {
          case "step": {
            const raw = event.data as Record<string, unknown>;
            const step: TraceStep = {
              agent_name: (raw.agent_name ?? raw.agent ?? "unknown") as string,
              started_at: (raw.started_at ?? "") as string,
              ended_at: (raw.ended_at ?? "") as string,
              duration_ms: (raw.duration_ms ?? raw.latency_ms ?? 0) as number,
              tokens_used: (raw.tokens_used ?? ((raw.prompt_tokens as number ?? 0) + (raw.completion_tokens as number ?? 0))) as number,
              input_summary: (raw.input_summary ?? "") as string,
              output_summary: (raw.output_summary ?? "") as string,
              tools_called: (raw.tools_called ?? []) as string[],
              skills_activated: (raw.skills_activated ?? []) as string[],
              error: (raw.error ?? null) as string | null,
            };
            setLiveSteps((prev) => [...prev, step]);
            break;
          }
          case "answer": {
            const answer = event.data as FinalAnswer;
            const assistantMessage: ChatMessage = {
              id: crypto.randomUUID(),
              role: "assistant",
              content: answer.answer_text,
              answer,
              timestamp: new Date().toISOString(),
            };
            setMessages((prev) => [...prev, assistantMessage]);
            setIsLoading(false);

            if (answer.trace_id) {
              getTrace(answer.trace_id)
                .then((trace) => {
                  setCurrentTrace(trace);
                  setMessages((prev) =>
                    prev.map((m) =>
                      m.id === assistantMessage.id ? { ...m, trace } : m
                    )
                  );
                })
                .catch(() => {});
            }
            break;
          }
          case "error": {
            const errorMessage: ChatMessage = {
              id: crypto.randomUUID(),
              role: "assistant",
              content:
                typeof event.data === "string"
                  ? event.data
                  : "An error occurred while processing your question.",
              timestamp: new Date().toISOString(),
            };
            setMessages((prev) => [...prev, errorMessage]);
            setIsLoading(false);
            break;
          }
        }
      });

      cleanupRef.current = cleanup;
    } catch {
      const errorMessage: ChatMessage = {
        id: crypto.randomUUID(),
        role: "assistant",
        content: "Failed to connect to the server. Please try again.",
        timestamp: new Date().toISOString(),
      };
      setMessages((prev) => [...prev, errorMessage]);
      setIsLoading(false);
    }
  }, []);

  const clearMessages = useCallback(() => {
    if (cleanupRef.current) {
      cleanupRef.current();
      cleanupRef.current = null;
    }
    setMessages([]);
    setCurrentTrace(null);
    setLiveSteps([]);
    sessionIdRef.current = null;
    setIsLoading(false);
  }, []);

  return {
    messages,
    isLoading,
    currentTrace,
    liveSteps,
    sendMessage,
    clearMessages,
  };
}
