"use client";

import { useState } from "react";
import type { EvalResult } from "@/lib/types";
import { Badge } from "@/components/ui/badge";
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from "@/components/ui/collapsible";
import { SqlViewer } from "@/components/answer/SqlViewer";
import { cn } from "@/lib/utils";
import {
  CheckCircle2,
  XCircle,
  ChevronDown,
  ChevronRight,
  Clock,
  Coins,
} from "lucide-react";

interface EvalResultCardProps {
  result: EvalResult;
}

export function EvalResultCard({ result }: EvalResultCardProps) {
  const [open, setOpen] = useState(false);

  return (
    <Collapsible open={open} onOpenChange={setOpen}>
      <CollapsibleTrigger className="grid w-full grid-cols-[1fr_100px_100px_80px] items-center gap-4 px-4 py-3 text-left transition-colors hover:bg-accent/30">
        <div className="flex items-center gap-2 min-w-0">
          {open ? (
            <ChevronDown className="h-3.5 w-3.5 shrink-0 text-muted-foreground" />
          ) : (
            <ChevronRight className="h-3.5 w-3.5 shrink-0 text-muted-foreground" />
          )}
          <span className="truncate text-sm">{result.question}</span>
        </div>
        <Badge variant="outline" className="w-fit text-xs font-normal">
          {result.category}
        </Badge>
        <div className="flex items-center gap-1 text-xs text-muted-foreground">
          <Clock className="h-3 w-3" />
          {result.latency_ms.toLocaleString()}ms
        </div>
        <div className="flex items-center gap-1">
          {result.passed ? (
            <CheckCircle2 className="h-4 w-4 text-emerald-400" />
          ) : (
            <XCircle className="h-4 w-4 text-red-400" />
          )}
          <span
            className={cn(
              "text-xs font-medium",
              result.passed ? "text-emerald-400" : "text-red-400"
            )}
          >
            {result.passed ? "Pass" : "Fail"}
          </span>
        </div>
      </CollapsibleTrigger>

      <CollapsibleContent className="border-t bg-muted/20 px-4 py-4">
        <div className="space-y-4">
          {/* ── Scores ── */}
          <div className="flex flex-wrap gap-3">
            <ScorePill label="SQL Match" value={result.sql_match_score} />
            <ScorePill label="Answer Relevance" value={result.answer_relevance_score} />
            <div className="flex items-center gap-1 text-xs text-muted-foreground">
              <Coins className="h-3 w-3" />
              {result.tokens_used.toLocaleString()} tokens
            </div>
            {result.safety_blocked && (
              <Badge variant="destructive" className="text-xs">
                Safety Blocked
              </Badge>
            )}
          </div>

          {/* ── Expected SQL ── */}
          <div className="space-y-1">
            <span className="text-xs font-medium uppercase tracking-wider text-muted-foreground">
              Expected SQL
            </span>
            <SqlViewer sql={result.expected_sql} />
          </div>

          {/* ── Actual SQL ── */}
          <div className="space-y-1">
            <span className="text-xs font-medium uppercase tracking-wider text-muted-foreground">
              Actual SQL
            </span>
            <SqlViewer sql={result.actual_sql} />
          </div>

          {/* ── Error ── */}
          {result.error && (
            <div className="rounded-md border border-red-500/20 bg-red-500/10 px-3 py-2">
              <p className="text-xs text-red-400">{result.error}</p>
            </div>
          )}
        </div>
      </CollapsibleContent>
    </Collapsible>
  );
}

function ScorePill({ label, value }: { label: string; value: number }) {
  const pct = (value * 100).toFixed(0);
  const color =
    value >= 0.8
      ? "text-emerald-400"
      : value >= 0.5
        ? "text-amber-400"
        : "text-red-400";

  return (
    <div className="flex items-center gap-1.5 text-xs">
      <span className="text-muted-foreground">{label}:</span>
      <span className={cn("font-semibold", color)}>{pct}%</span>
    </div>
  );
}
