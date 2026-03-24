"use client";

import { useState } from "react";
import type { FinalAnswer } from "@/lib/types";
import { Badge } from "@/components/ui/badge";
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from "@/components/ui/collapsible";
import { Separator } from "@/components/ui/separator";
import { SqlViewer } from "./SqlViewer";
import { ChartViewer } from "./ChartViewer";
import { EvidencePanel } from "./EvidencePanel";
import {
  ChevronDown,
  ChevronRight,
  Lightbulb,
  AlertTriangle,
  Code2,
  BookOpen,
} from "lucide-react";
import { cn } from "@/lib/utils";

interface AnswerCardProps {
  answer: FinalAnswer;
}

const confidenceConfig = {
  high: {
    color: "bg-emerald-500/15 text-emerald-400 border-emerald-500/30",
    label: "High Confidence",
  },
  medium: {
    color: "bg-amber-500/15 text-amber-400 border-amber-500/30",
    label: "Medium Confidence",
  },
  low: {
    color: "bg-red-500/15 text-red-400 border-red-500/30",
    label: "Low Confidence",
  },
};

export function AnswerCard({ answer }: AnswerCardProps) {
  const [sqlOpen, setSqlOpen] = useState(false);
  const [evidenceOpen, setEvidenceOpen] = useState(false);
  const conf = confidenceConfig[answer.confidence];

  return (
    <div className="space-y-4 rounded-xl border bg-card p-5">
      {/* ── Answer text ── */}
      <div className="space-y-3">
        <div className="flex items-start justify-between gap-3">
          <p className="text-sm leading-relaxed">{answer.answer_text}</p>
          <Badge
            className={cn(
              "shrink-0 whitespace-nowrap text-xs",
              conf.color
            )}
          >
            {conf.label}
          </Badge>
        </div>
      </div>

      {/* ── Chart ── */}
      {answer.chart_spec && (
        <>
          <Separator />
          <ChartViewer spec={answer.chart_spec} />
        </>
      )}

      {/* ── Insights ── */}
      {answer.insights.length > 0 && (
        <>
          <Separator />
          <div className="space-y-2">
            <div className="flex items-center gap-2 text-xs font-medium uppercase tracking-wider text-muted-foreground">
              <Lightbulb className="h-3.5 w-3.5" />
              Key Insights
            </div>
            <ul className="space-y-1.5">
              {answer.insights.map((insight, i) => (
                <li
                  key={i}
                  className="flex items-start gap-2 text-sm text-muted-foreground"
                >
                  <span className="mt-1.5 h-1.5 w-1.5 shrink-0 rounded-full bg-primary/60" />
                  {insight}
                </li>
              ))}
            </ul>
          </div>
        </>
      )}

      {/* ── Limitations ── */}
      {answer.limitations.length > 0 && (
        <>
          <Separator />
          <div className="space-y-2">
            <div className="flex items-center gap-2 text-xs font-medium uppercase tracking-wider text-amber-400/80">
              <AlertTriangle className="h-3.5 w-3.5" />
              Limitations
            </div>
            <ul className="space-y-1.5">
              {answer.limitations.map((lim, i) => (
                <li
                  key={i}
                  className="flex items-start gap-2 text-sm text-muted-foreground"
                >
                  <span className="mt-1.5 h-1.5 w-1.5 shrink-0 rounded-full bg-amber-400/60" />
                  {lim}
                </li>
              ))}
            </ul>
          </div>
        </>
      )}

      {/* ── Collapsible SQL ── */}
      <Separator />
      <Collapsible open={sqlOpen} onOpenChange={setSqlOpen}>
        <CollapsibleTrigger className="flex w-full items-center gap-2 text-xs font-medium uppercase tracking-wider text-muted-foreground transition-colors hover:text-foreground">
          {sqlOpen ? (
            <ChevronDown className="h-3.5 w-3.5" />
          ) : (
            <ChevronRight className="h-3.5 w-3.5" />
          )}
          <Code2 className="h-3.5 w-3.5" />
          View SQL
        </CollapsibleTrigger>
        <CollapsibleContent className="pt-3">
          <SqlViewer sql={answer.sql_used} />
        </CollapsibleContent>
      </Collapsible>

      {/* ── Collapsible Evidence ── */}
      {answer.evidence.length > 0 && (
        <>
          <Separator />
          <Collapsible open={evidenceOpen} onOpenChange={setEvidenceOpen}>
            <CollapsibleTrigger className="flex w-full items-center gap-2 text-xs font-medium uppercase tracking-wider text-muted-foreground transition-colors hover:text-foreground">
              {evidenceOpen ? (
                <ChevronDown className="h-3.5 w-3.5" />
              ) : (
                <ChevronRight className="h-3.5 w-3.5" />
              )}
              <BookOpen className="h-3.5 w-3.5" />
              View Evidence
            </CollapsibleTrigger>
            <CollapsibleContent className="pt-3">
              <EvidencePanel evidence={answer.evidence} />
            </CollapsibleContent>
          </Collapsible>
        </>
      )}
    </div>
  );
}
