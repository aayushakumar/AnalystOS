"use client";

import { useState, useCallback } from "react";
import type { EvalReport, EvalResult } from "@/lib/types";
import { runEval, getEvalResults } from "@/lib/api";
import { EvalResultCard } from "./EvalResultCard";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Skeleton } from "@/components/ui/skeleton";
import {
  Play,
  Target,
  Shield,
  Clock,
  Coins,
  Hash,
  Loader2,
  ArrowUpDown,
  Filter,
} from "lucide-react";
import { cn } from "@/lib/utils";

type SortField = "question" | "category" | "latency_ms" | "passed";
type SortDir = "asc" | "desc";

export function BenchmarkDashboard() {
  const [report, setReport] = useState<EvalReport | null>(null);
  const [running, setRunning] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [sortField, setSortField] = useState<SortField>("question");
  const [sortDir, setSortDir] = useState<SortDir>("asc");
  const [filterCategory, setFilterCategory] = useState<string | null>(null);

  const handleRun = useCallback(async () => {
    setRunning(true);
    setError(null);
    try {
      await runEval();
      setLoading(true);
      const results = await getEvalResults();
      setReport(results);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to run evaluation");
    } finally {
      setRunning(false);
      setLoading(false);
    }
  }, []);

  const handleLoad = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const results = await getEvalResults();
      setReport(results);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to load results");
    } finally {
      setLoading(false);
    }
  }, []);

  const toggleSort = (field: SortField) => {
    if (sortField === field) {
      setSortDir((d) => (d === "asc" ? "desc" : "asc"));
    } else {
      setSortField(field);
      setSortDir("asc");
    }
  };

  const categories = report
    ? Array.from(new Set(report.results.map((r) => r.category)))
    : [];

  const filteredResults: EvalResult[] = report
    ? report.results
        .filter((r) => !filterCategory || r.category === filterCategory)
        .sort((a, b) => {
          const dir = sortDir === "asc" ? 1 : -1;
          switch (sortField) {
            case "question":
              return dir * a.question.localeCompare(b.question);
            case "category":
              return dir * a.category.localeCompare(b.category);
            case "latency_ms":
              return dir * (a.latency_ms - b.latency_ms);
            case "passed":
              return dir * (Number(a.passed) - Number(b.passed));
            default:
              return 0;
          }
        })
    : [];

  return (
    <div className="space-y-6">
      {/* ── Actions ── */}
      <div className="flex items-center gap-3">
        <Button onClick={handleRun} disabled={running} className="gap-2">
          {running ? (
            <Loader2 className="h-4 w-4 animate-spin" />
          ) : (
            <Play className="h-4 w-4" />
          )}
          Run Benchmark
        </Button>
        <Button
          variant="outline"
          onClick={handleLoad}
          disabled={loading}
          className="gap-2"
        >
          Load Latest Results
        </Button>
        {error && (
          <span className="text-sm text-destructive">{error}</span>
        )}
      </div>

      {/* ── Metric Cards ── */}
      {report && (
        <div className="grid grid-cols-2 gap-4 md:grid-cols-3 lg:grid-cols-5">
          <MetricCard
            icon={<Target className="h-4 w-4" />}
            label="Accuracy"
            value={`${(report.accuracy * 100).toFixed(1)}%`}
            accent={report.accuracy >= 0.8 ? "green" : report.accuracy >= 0.5 ? "yellow" : "red"}
          />
          <MetricCard
            icon={<Shield className="h-4 w-4" />}
            label="Safety Block Rate"
            value={`${(report.safety_block_rate * 100).toFixed(1)}%`}
            accent="blue"
          />
          <MetricCard
            icon={<Clock className="h-4 w-4" />}
            label="Avg Latency"
            value={`${report.avg_latency_ms.toLocaleString()}ms`}
            accent={report.avg_latency_ms <= 3000 ? "green" : "yellow"}
          />
          <MetricCard
            icon={<Coins className="h-4 w-4" />}
            label="Avg Tokens"
            value={report.avg_tokens.toLocaleString()}
            accent="blue"
          />
          <MetricCard
            icon={<Hash className="h-4 w-4" />}
            label="Total Cases"
            value={`${report.passed}/${report.total_cases}`}
            accent="blue"
          />
        </div>
      )}

      {/* ── Loading ── */}
      {(running || loading) && !report && (
        <div className="grid grid-cols-2 gap-4 md:grid-cols-3 lg:grid-cols-5">
          {[1, 2, 3, 4, 5].map((i) => (
            <Skeleton key={i} className="h-24 rounded-lg" />
          ))}
        </div>
      )}

      {/* ── Results Table ── */}
      {report && report.results.length > 0 && (
        <Card>
          <CardHeader className="pb-3">
            <div className="flex items-center justify-between">
              <div>
                <CardTitle className="text-base">Results</CardTitle>
                <CardDescription>
                  Run {report.run_id} &middot;{" "}
                  {new Date(report.timestamp).toLocaleString()}
                </CardDescription>
              </div>
              <div className="flex items-center gap-2">
                <Filter className="h-3.5 w-3.5 text-muted-foreground" />
                <div className="flex gap-1">
                  <Badge
                    variant={filterCategory === null ? "default" : "outline"}
                    className="cursor-pointer text-xs"
                    onClick={() => setFilterCategory(null)}
                  >
                    All
                  </Badge>
                  {categories.map((cat) => (
                    <Badge
                      key={cat}
                      variant={filterCategory === cat ? "default" : "outline"}
                      className="cursor-pointer text-xs"
                      onClick={() =>
                        setFilterCategory(filterCategory === cat ? null : cat)
                      }
                    >
                      {cat}
                    </Badge>
                  ))}
                </div>
              </div>
            </div>
          </CardHeader>
          <CardContent className="p-0">
            {/* ── Table header ── */}
            <div className="grid grid-cols-[1fr_100px_100px_80px] gap-4 border-b bg-muted/30 px-4 py-2 text-xs font-medium text-muted-foreground">
              <SortableHeader
                label="Question"
                field="question"
                current={sortField}
                dir={sortDir}
                onToggle={toggleSort}
              />
              <SortableHeader
                label="Category"
                field="category"
                current={sortField}
                dir={sortDir}
                onToggle={toggleSort}
              />
              <SortableHeader
                label="Latency"
                field="latency_ms"
                current={sortField}
                dir={sortDir}
                onToggle={toggleSort}
              />
              <SortableHeader
                label="Status"
                field="passed"
                current={sortField}
                dir={sortDir}
                onToggle={toggleSort}
              />
            </div>

            <ScrollArea className="max-h-[500px]">
              <div className="divide-y">
                {filteredResults.map((result) => (
                  <EvalResultCard key={result.case_id} result={result} />
                ))}
              </div>
            </ScrollArea>
          </CardContent>
        </Card>
      )}
    </div>
  );
}

/* ── Metric Card ── */

function MetricCard({
  icon,
  label,
  value,
  accent,
}: {
  icon: React.ReactNode;
  label: string;
  value: string;
  accent: "green" | "yellow" | "red" | "blue";
}) {
  const accentClasses = {
    green: "text-emerald-400",
    yellow: "text-amber-400",
    red: "text-red-400",
    blue: "text-primary",
  };

  return (
    <Card>
      <CardContent className="flex flex-col gap-2 p-4">
        <div className="flex items-center gap-2 text-muted-foreground">
          {icon}
          <span className="text-xs">{label}</span>
        </div>
        <span className={cn("text-2xl font-bold", accentClasses[accent])}>
          {value}
        </span>
      </CardContent>
    </Card>
  );
}

/* ── Sortable Header ── */

function SortableHeader({
  label,
  field,
  current,
  dir,
  onToggle,
}: {
  label: string;
  field: SortField;
  current: SortField;
  dir: SortDir;
  onToggle: (f: SortField) => void;
}) {
  return (
    <button
      onClick={() => onToggle(field)}
      className="flex items-center gap-1 transition-colors hover:text-foreground"
    >
      {label}
      <ArrowUpDown
        className={cn(
          "h-3 w-3",
          current === field ? "text-foreground" : "text-muted-foreground/50"
        )}
      />
      {current === field && (
        <span className="text-[10px]">{dir === "asc" ? "↑" : "↓"}</span>
      )}
    </button>
  );
}
