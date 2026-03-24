/* ------------------------------------------------------------------ */
/*  Backend schema mirrors                                            */
/* ------------------------------------------------------------------ */

export type IntentType =
  | "descriptive"
  | "comparative"
  | "diagnostic"
  | "visualization"
  | "ambiguous"
  | "unsupported"
  | "unsafe";

export type RiskLevel = "low" | "medium" | "high" | "critical";

export interface IntentClassification {
  intent: IntentType;
  risk_level: RiskLevel;
  requires_clarification: boolean;
  route: string;
  reasoning: string;
}

export interface TableInfo {
  table_name: string;
  description: string;
  row_count_estimate: number;
}

export interface ColumnInfo {
  table_name: string;
  column_name: string;
  data_type: string;
  description: string;
  sample_values: string[];
}

export interface JoinInfo {
  left_table: string;
  left_column: string;
  right_table: string;
  right_column: string;
  join_type: string;
  description: string;
}

export interface SchemaPack {
  tables: TableInfo[];
  columns: ColumnInfo[];
  joins: JoinInfo[];
  relevant_metrics: string[];
  data_freshness: string;
}

export interface TimeWindow {
  start: string;
  end: string;
  granularity: string;
}

export interface FilterSpec {
  column: string;
  operator: string;
  value: string;
}

export type Complexity = "simple" | "moderate" | "complex";

export interface AnalysisPlan {
  business_intent: string;
  entities: string[];
  metrics: string[];
  time_window: TimeWindow | null;
  dimensions: string[];
  filters: FilterSpec[];
  ambiguity_flags: string[];
  candidate_tables: string[];
  complexity: Complexity;
  requires_clarification: boolean;
  clarification_questions: string[];
}

export interface SQLCandidate {
  sql: string;
  rationale: string;
  tables_used: string[];
  metrics_computed: string[];
  time_range: string | null;
  estimated_complexity: string;
}

export type Severity = "error" | "warning" | "info";

export interface ValidationIssue {
  severity: Severity;
  message: string;
  location: string;
}

export interface ValidationReport {
  valid: boolean;
  issues: ValidationIssue[];
  requires_retry: boolean;
  risk_notes: string[];
  tables_verified: string[];
  columns_verified: string[];
}

export type ChartType =
  | "bar"
  | "line"
  | "pie"
  | "scatter"
  | "table"
  | "histogram"
  | "stacked_bar"
  | "area";

export interface ChartSpec {
  chart_type: ChartType;
  title: string;
  x_field: string;
  y_field: string;
  color_field: string | null;
  annotations: string[];
  data: Record<string, unknown>[];
}

export type Verdict = "accept" | "retry" | "refuse";

export interface CritiqueVerdict {
  verdict: Verdict;
  issues: string[];
  confidence_score: number;
  addresses_question: boolean;
  evidence_sufficient: boolean;
  retry_recommended: boolean;
  retry_reason: string | null;
}

export type Confidence = "high" | "medium" | "low";

export interface FinalAnswer {
  answer_text: string;
  insights: string[];
  chart_spec: ChartSpec | null;
  sql_used: string;
  evidence: string[];
  confidence: Confidence;
  limitations: string[];
  trace_id: string;
}

/* ------------------------------------------------------------------ */
/*  Trace types                                                       */
/* ------------------------------------------------------------------ */

export interface TraceStep {
  agent_name: string;
  started_at: string;
  ended_at: string;
  duration_ms: number;
  tokens_used: number;
  input_summary: string;
  output_summary: string;
  tools_called: string[];
  skills_activated: string[];
  error: string | null;
}

export interface Trace {
  trace_id: string;
  session_id: string;
  question: string;
  steps: TraceStep[];
  total_duration_ms: number;
  total_tokens: number;
  created_at: string;
}

/* ------------------------------------------------------------------ */
/*  Chat types                                                        */
/* ------------------------------------------------------------------ */

export interface ChatMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
  answer?: FinalAnswer;
  trace?: Trace;
  timestamp: string;
}

/* ------------------------------------------------------------------ */
/*  Eval types                                                        */
/* ------------------------------------------------------------------ */

export interface EvalCase {
  id: string;
  question: string;
  expected_sql: string;
  expected_answer_contains: string[];
  category: string;
  difficulty: string;
}

export interface EvalResult {
  case_id: string;
  question: string;
  category: string;
  difficulty: string;
  expected_sql: string;
  actual_sql: string;
  sql_match_score: number;
  answer_relevance_score: number;
  safety_blocked: boolean;
  latency_ms: number;
  tokens_used: number;
  passed: boolean;
  error: string | null;
}

export interface EvalReport {
  run_id: string;
  timestamp: string;
  total_cases: number;
  passed: number;
  failed: number;
  accuracy: number;
  safety_block_rate: number;
  avg_latency_ms: number;
  avg_tokens: number;
  results: EvalResult[];
}

/* ------------------------------------------------------------------ */
/*  SSE types                                                         */
/* ------------------------------------------------------------------ */

export interface SSEEvent {
  type: "step" | "answer" | "error";
  data: unknown;
}
