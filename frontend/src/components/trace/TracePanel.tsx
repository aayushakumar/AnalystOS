"use client";

import { useEffect, useRef } from "react";
import type { Trace, TraceStep as TraceStepType } from "@/lib/types";
import { TraceStepCard } from "./TraceStep";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Separator } from "@/components/ui/separator";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { Activity, Clock, Coins } from "lucide-react";

interface TracePanelProps {
  trace: Trace | null;
  liveSteps: TraceStepType[];
  isLoading: boolean;
}

export function TracePanel({ trace, liveSteps, isLoading }: TracePanelProps) {
  const bottomRef = useRef<HTMLDivElement>(null);
  const steps = trace?.steps ?? liveSteps;
  const totalMs = trace?.total_duration_ms ?? steps.reduce((s, st) => s + st.duration_ms, 0);
  const totalTokens = trace?.total_tokens ?? steps.reduce((s, st) => s + st.tokens_used, 0);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [steps]);

  return (
    <div className="flex h-full flex-col">
      {/* ── Header ── */}
      <div className="space-y-3 border-b px-4 py-4">
        <div className="flex items-center gap-2">
          <Activity className="h-4 w-4 text-primary" />
          <h2 className="text-sm font-semibold">Agent Trace</h2>
          {isLoading && (
            <span className="h-2 w-2 animate-pulse-subtle rounded-full bg-primary" />
          )}
        </div>
        {steps.length > 0 && (
          <div className="flex gap-2">
            <Badge
              variant="secondary"
              className="gap-1 text-xs font-normal"
            >
              <Clock className="h-3 w-3" />
              {totalMs.toLocaleString()}ms
            </Badge>
            <Badge
              variant="secondary"
              className="gap-1 text-xs font-normal"
            >
              <Coins className="h-3 w-3" />
              {totalTokens.toLocaleString()} tokens
            </Badge>
          </div>
        )}
      </div>

      {/* ── Steps ── */}
      <ScrollArea className="flex-1">
        <div className="p-4">
          {steps.length === 0 && !isLoading && (
            <div className="flex flex-col items-center gap-2 py-12 text-center">
              <Activity className="h-8 w-8 text-muted-foreground/40" />
              <p className="text-sm text-muted-foreground">
                Agent trace will appear here when you ask a question.
              </p>
            </div>
          )}

          {steps.length === 0 && isLoading && (
            <div className="space-y-4">
              {[1, 2, 3].map((i) => (
                <div key={i} className="space-y-2">
                  <Skeleton className="h-4 w-24" />
                  <Skeleton className="h-16 w-full" />
                </div>
              ))}
            </div>
          )}

          {steps.length > 0 && (
            <div className="relative space-y-0">
              {/* Timeline line */}
              <div className="absolute left-[11px] top-2 bottom-2 w-px bg-border" />

              {steps.map((step, i) => (
                <div key={i}>
                  <TraceStepCard step={step} index={i} />
                  {i < steps.length - 1 && (
                    <Separator className="ml-[11px] w-px h-3 bg-border" />
                  )}
                </div>
              ))}
            </div>
          )}

          <div ref={bottomRef} />
        </div>
      </ScrollArea>
    </div>
  );
}
