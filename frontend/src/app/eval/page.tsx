"use client";

import Link from "next/link";
import { BrainCircuit, ArrowLeft } from "lucide-react";
import { Button } from "@/components/ui/button";
import { BenchmarkDashboard } from "@/components/eval/BenchmarkDashboard";

export default function EvalPage() {
  return (
    <div className="flex h-screen w-screen flex-col overflow-hidden bg-background">
      {/* ── Header ── */}
      <header className="flex h-14 items-center gap-4 border-b bg-card px-6">
        <Link href="/">
          <Button variant="ghost" size="sm" className="gap-2">
            <ArrowLeft className="h-4 w-4" />
            Back to Chat
          </Button>
        </Link>
        <div className="flex items-center gap-2">
          <BrainCircuit className="h-5 w-5 text-primary" />
          <span className="text-lg font-semibold tracking-tight">
            AnalystOS
          </span>
          <span className="text-sm text-muted-foreground">/</span>
          <span className="text-sm text-muted-foreground">
            Evaluation Dashboard
          </span>
        </div>
      </header>

      {/* ── Content ── */}
      <main className="flex-1 overflow-auto p-6">
        <BenchmarkDashboard />
      </main>
    </div>
  );
}
