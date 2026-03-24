from __future__ import annotations

import sqlglot
from sqlglot import exp

from app.agents.base import BaseAgent
from app.config import settings
from app.db.connection import db_manager
from app.schemas import (
    SQLCandidate,
    Severity,
    ValidationIssue,
    ValidationReport,
)

SYSTEM_PROMPT = """\
You are a SQL-validation review agent. Given a SQL query, the programmatic validation results, \
and the database schema, perform a semantic review.

Check for:
- Logical correctness of JOINs (are the join conditions sensible?).
- Appropriate aggregation (GROUP BY matches selected non-aggregate columns).
- Filter logic soundness.
- Potential performance issues (missing filters on large tables, Cartesian products).
- Whether the query actually answers the stated business intent.

Respond with ONLY valid JSON matching the required schema.\
"""

_WRITE_KEYWORDS = {
    "INSERT", "UPDATE", "DELETE", "DROP", "ALTER", "CREATE",
    "TRUNCATE", "GRANT", "REVOKE", "MERGE",
}


class Validator(BaseAgent):
    """Hybrid validator: programmatic AST checks + optional LLM semantic review."""

    def __init__(self) -> None:
        super().__init__(
            name="validator",
            model=settings.analyst_cheap_model,
            system_prompt=SYSTEM_PROMPT,
            output_schema=ValidationReport,
        )

    async def run(
        self,
        candidate: SQLCandidate,
        use_llm_review: bool = True,
        **kwargs,
    ) -> dict:
        issues: list[ValidationIssue] = []
        tables_verified: list[str] = []
        columns_verified: list[str] = []

        self._check_write_ops(candidate.sql, issues)
        self._check_multiple_statements(candidate.sql, issues)
        self._check_tables_exist(candidate.sql, issues, tables_verified)
        self._check_columns_exist(candidate.sql, issues, columns_verified)

        has_errors = any(i.severity == Severity.ERROR for i in issues)

        if has_errors or not use_llm_review:
            report = ValidationReport(
                valid=not has_errors,
                issues=issues,
                requires_retry=has_errors,
                risk_notes=[],
                tables_verified=tables_verified,
                columns_verified=columns_verified,
            )
            return {
                "output": report,
                "usage": {"prompt_tokens": 0, "completion_tokens": 0},
                "model": "programmatic",
                "latency_ms": 0,
            }

        context = {
            "sql": candidate.sql,
            "rationale": candidate.rationale,
            "programmatic_issues": [i.model_dump() for i in issues],
            "tables_verified": tables_verified,
            "columns_verified": columns_verified,
        }
        messages = self._build_messages(
            "Review this SQL query for correctness and safety.", context=context
        )
        result = await super().run(messages, **kwargs)
        report: ValidationReport = result["output"]
        report.issues = issues + report.issues
        report.tables_verified = list(set(tables_verified + report.tables_verified))
        report.columns_verified = list(set(columns_verified + report.columns_verified))
        report.valid = not any(i.severity == Severity.ERROR for i in report.issues)
        report.requires_retry = not report.valid
        result["output"] = report
        return result

    def _check_write_ops(self, sql: str, issues: list[ValidationIssue]) -> None:
        try:
            for statement in sqlglot.parse(sql, dialect="duckdb"):
                if statement is None:
                    continue
                stmt_type = type(statement).__name__.upper()
                for kw in _WRITE_KEYWORDS:
                    if kw in stmt_type:
                        issues.append(ValidationIssue(
                            severity=Severity.ERROR,
                            message=f"Write operation detected: {kw}",
                            location=sql[:80],
                        ))
                        return
        except sqlglot.errors.ParseError:
            issues.append(ValidationIssue(
                severity=Severity.WARNING,
                message="SQL could not be fully parsed for write-op detection.",
                location=sql[:80],
            ))

    def _check_multiple_statements(self, sql: str, issues: list[ValidationIssue]) -> None:
        try:
            statements = [s for s in sqlglot.parse(sql, dialect="duckdb") if s is not None]
            if len(statements) > 1:
                issues.append(ValidationIssue(
                    severity=Severity.ERROR,
                    message=f"Multiple SQL statements detected ({len(statements)}). Only single statements are allowed.",
                    location=sql[:80],
                ))
        except sqlglot.errors.ParseError:
            pass

    def _check_tables_exist(
        self,
        sql: str,
        issues: list[ValidationIssue],
        tables_verified: list[str],
    ) -> None:
        try:
            available = set(db_manager.get_table_names())
        except Exception:
            return

        available_lower = {t.lower() for t in available}

        try:
            for statement in sqlglot.parse(sql, dialect="duckdb"):
                if statement is None:
                    continue
                cte_names: set[str] = set()
                for cte in statement.find_all(exp.CTE):
                    if cte.alias:
                        cte_names.add(cte.alias.lower())

                subquery_aliases: set[str] = set()
                for subq in statement.find_all(exp.Subquery):
                    if subq.alias:
                        subquery_aliases.add(subq.alias.lower())

                virtual_names = cte_names | subquery_aliases

                for table in statement.find_all(exp.Table):
                    name = table.name
                    if not name:
                        continue
                    if name.lower() in virtual_names:
                        continue
                    if name.lower() in available_lower:
                        tables_verified.append(name)
                    else:
                        issues.append(ValidationIssue(
                            severity=Severity.WARNING,
                            message=f"Table '{name}' not found in database (may be an alias or CTE).",
                            location=name,
                        ))
        except sqlglot.errors.ParseError:
            pass

    def _check_columns_exist(
        self,
        sql: str,
        issues: list[ValidationIssue],
        columns_verified: list[str],
    ) -> None:
        try:
            available_tables = db_manager.get_table_names()
        except Exception:
            return

        all_columns: dict[str, set[str]] = {}
        for table in available_tables:
            try:
                cols = db_manager.describe_table(table)
                all_columns[table.lower()] = {c["column_name"].lower() for c in cols}
            except Exception:
                continue

        all_col_names = set()
        for cols in all_columns.values():
            all_col_names.update(cols)

        try:
            for statement in sqlglot.parse(sql, dialect="duckdb"):
                if statement is None:
                    continue
                for col in statement.find_all(exp.Column):
                    col_name = col.name
                    if not col_name:
                        continue
                    table_ref = col.table
                    if table_ref and table_ref.lower() in all_columns:
                        if col_name.lower() in all_columns[table_ref.lower()]:
                            columns_verified.append(f"{table_ref}.{col_name}")
                        else:
                            issues.append(ValidationIssue(
                                severity=Severity.ERROR,
                                message=f"Column '{col_name}' does not exist in table '{table_ref}'.",
                                location=f"{table_ref}.{col_name}",
                            ))
                    elif col_name.lower() in all_col_names:
                        columns_verified.append(col_name)
                    # Columns with unresolved aliases (e.g. o.order_id) are OK — we
                    # can't resolve aliases statically without full scope analysis.
        except sqlglot.errors.ParseError:
            pass
