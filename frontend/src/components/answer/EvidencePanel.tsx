"use client";

import { FileText } from "lucide-react";

interface EvidencePanelProps {
  evidence: string[];
}

export function EvidencePanel({ evidence }: EvidencePanelProps) {
  if (evidence.length === 0) return null;

  return (
    <div className="space-y-2">
      {evidence.map((item, i) => (
        <div
          key={i}
          className="flex items-start gap-2.5 rounded-md border bg-muted/30 px-3 py-2.5"
        >
          <FileText className="mt-0.5 h-3.5 w-3.5 shrink-0 text-muted-foreground" />
          <p className="text-xs leading-relaxed text-muted-foreground">
            {item}
          </p>
        </div>
      ))}
    </div>
  );
}
