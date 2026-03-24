"use client";

import { useState } from "react";
import type { TraceStep } from "@/lib/types";
import { Badge } from "@/components/ui/badge";
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from "@/components/ui/collapsible";
import { cn } from "@/lib/utils";
import {
  ChevronDown,
  ChevronRight,
  Clock,
  Coins,
  Wrench,
  BookMarked,
  AlertCircle,
} from "lucide-react";

interface TraceStepCardProps {
  step: TraceStep;
  index: number;
}

const AGENT_COLORS: Record<string, string> = {
  intent_classifier: "bg-blue-400",
  schema_scout: "bg-emerald-400",
  planner: "bg-violet-400",
  sql_builder: "bg-amber-400",
  validator: "bg-teal-400",
  executor: "bg-cyan-400",
  analyst: "bg-pink-400",
  critic: "bg-orange-400",
  clarifier: "bg-indigo-400",
};

function getAgentColor(name: string): string {
  if (!name) return "bg-muted-foreground";
  const lower = name.toLowerCase();
  for (const [key, color] of Object.entries(AGENT_COLORS)) {
    if (lower.includes(key)) return color;
  }
  return "bg-muted-foreground";
}

function formatAgentName(name: string): string {
  if (!name) return "Unknown Agent";
  return name
    .replace(/_/g, " ")
    .replace(/\b\w/g, (c) => c.toUpperCase());
}

export function TraceStepCard({ step, index }: TraceStepCardProps) {
  const [open, setOpen] = useState(false);
  const hasError = !!step.error;

  return (
    <Collapsible open={open} onOpenChange={setOpen}>
      <CollapsibleTrigger className="flex w-full items-start gap-3 rounded-md px-1 py-2 text-left transition-colors hover:bg-accent/50">
        {/* Timeline dot */}
        <div className="relative mt-1.5 flex shrink-0">
          <span
            className={cn(
              "h-[9px] w-[9px] rounded-full ring-2 ring-background",
              hasError ? "bg-red-400" : getAgentColor(step.agent_name)
            )}
          />
        </div>

        <div className="min-w-0 flex-1">
          <div className="flex items-center gap-2">
            <span className="text-xs font-medium">
              {formatAgentName(step.agent_name)}
            </span>
            {hasError && (
              <AlertCircle className="h-3 w-3 text-red-400" />
            )}
            <div className="ml-auto flex items-center gap-1.5 text-[10px] text-muted-foreground">
              <Clock className="h-2.5 w-2.5" />
              {step.duration_ms}ms
              <Coins className="ml-1 h-2.5 w-2.5" />
              {step.tokens_used}
            </div>
            {open ? (
              <ChevronDown className="h-3 w-3 shrink-0 text-muted-foreground" />
            ) : (
              <ChevronRight className="h-3 w-3 shrink-0 text-muted-foreground" />
            )}
          </div>
          <p className="mt-0.5 truncate text-[11px] text-muted-foreground">
            {step.output_summary || step.input_summary}
          </p>
        </div>
      </CollapsibleTrigger>

      <CollapsibleContent className="ml-6 space-y-2 pb-2 pl-2">
        {/* Input summary */}
        {step.input_summary && (
          <div className="space-y-1">
            <span className="text-[10px] font-medium uppercase tracking-wider text-muted-foreground">
              Input
            </span>
            <p className="text-xs text-muted-foreground">
              {step.input_summary}
            </p>
          </div>
        )}

        {/* Output summary */}
        {step.output_summary && (
          <div className="space-y-1">
            <span className="text-[10px] font-medium uppercase tracking-wider text-muted-foreground">
              Output
            </span>
            <p className="text-xs text-muted-foreground">
              {step.output_summary}
            </p>
          </div>
        )}

        {/* Tools called */}
        {step.tools_called.length > 0 && (
          <div className="flex flex-wrap items-center gap-1.5">
            <Wrench className="h-3 w-3 text-muted-foreground" />
            {step.tools_called.map((tool) => (
              <Badge
                key={tool}
                variant="outline"
                className="text-[10px] font-normal"
              >
                {tool}
              </Badge>
            ))}
          </div>
        )}

        {/* Skills activated */}
        {step.skills_activated.length > 0 && (
          <div className="flex flex-wrap items-center gap-1.5">
            <BookMarked className="h-3 w-3 text-muted-foreground" />
            {step.skills_activated.map((skill) => (
              <Badge
                key={skill}
                variant="secondary"
                className="text-[10px] font-normal"
              >
                {skill}
              </Badge>
            ))}
          </div>
        )}

        {/* Error */}
        {hasError && (
          <div className="rounded-md border border-red-500/20 bg-red-500/10 px-3 py-2">
            <p className="text-xs text-red-400">{step.error}</p>
          </div>
        )}
      </CollapsibleContent>
    </Collapsible>
  );
}
