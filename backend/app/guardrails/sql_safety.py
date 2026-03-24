"""AST-based SQL safety checker using sqlglot."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

import sqlglot
from sqlglot import exp

DIALECT = "duckdb"

BLOCKED_EXPRESSION_TYPES = (
    exp.Insert,
    exp.Update,
    exp.Delete,
    exp.Drop,
    exp.Alter,
    exp.Create,
    exp.Grant,
)

BLOCKED_COMMAND_NAMES = {"TRUNCATE", "REVOKE"}


class SafetyLevel(str, Enum):
    SAFE = "safe"
    WARNING = "warning"
    BLOCKED = "blocked"


@dataclass
class SafetyCheckResult:
    level: SafetyLevel
    passed: bool
    issues: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


def _check_write_operations(expressions: list[exp.Expression]) -> list[str]:
    """Block any DML/DDL write operations."""
    issues: list[str] = []
    for expression in expressions:
        for blocked_type in BLOCKED_EXPRESSION_TYPES:
            if isinstance(expression, blocked_type):
                issues.append(f"Write operation blocked: {type(expression).__name__}")
                break
        if isinstance(expression, exp.Command):
            cmd_name = expression.this
            if isinstance(cmd_name, str) and cmd_name.upper() in BLOCKED_COMMAND_NAMES:
                issues.append(f"Write operation blocked: {cmd_name.upper()}")
    return issues


def _check_multiple_statements(sql: str, expressions: list[exp.Expression]) -> list[str]:
    """Block SQL containing multiple semicolon-separated statements."""
    if len(expressions) > 1:
        return ["Multiple statements detected — only single statements are allowed"]

    stripped = sql.strip().rstrip(";").strip()
    if ";" in stripped:
        return ["Multiple statements detected — only single statements are allowed"]

    return []


def _check_table_existence(
    expressions: list[exp.Expression], available_tables: list[str]
) -> list[str]:
    """Verify all referenced tables exist in the allowed set."""
    issues: list[str] = []
    allowed = {t.lower() for t in available_tables}

    for expression in expressions:
        for table in expression.find_all(exp.Table):
            table_name = table.name
            if not table_name:
                continue
            if table_name.lower() not in allowed:
                issues.append(f"Unknown table: '{table_name}'")
    return issues


def _check_column_existence(
    expressions: list[exp.Expression], available_columns: dict[str, list[str]]
) -> list[str]:
    """Verify referenced columns exist for their respective tables."""
    issues: list[str] = []
    col_lookup: dict[str, set[str]] = {
        t.lower(): {c.lower() for c in cols} for t, cols in available_columns.items()
    }

    for expression in expressions:
        table_aliases: dict[str, str] = {}
        for table_node in expression.find_all(exp.Table):
            name = table_node.name
            alias = table_node.alias
            if alias and name:
                table_aliases[alias.lower()] = name.lower()
            if name:
                table_aliases[name.lower()] = name.lower()

        for column in expression.find_all(exp.Column):
            col_name = column.name
            tbl_ref = column.table
            if not tbl_ref:
                continue
            real_table = table_aliases.get(tbl_ref.lower(), tbl_ref.lower())
            if real_table in col_lookup and col_name.lower() not in col_lookup[real_table]:
                issues.append(f"Unknown column: '{col_name}' in table '{real_table}'")
    return issues


def _check_missing_where(expressions: list[exp.Expression]) -> list[str]:
    """Warn when a SELECT has no WHERE clause (potential full table scan)."""
    warnings: list[str] = []
    for expression in expressions:
        for select in expression.find_all(exp.Select):
            has_from = select.find(exp.From)
            has_where = select.find(exp.Where)
            if has_from and not has_where:
                warnings.append("SELECT without WHERE clause — potential full table scan")
                break
    return warnings


def _count_subquery_depth(node: exp.Expression, current: int = 0) -> int:
    """Return maximum subquery nesting depth."""
    max_depth = current
    for child in node.iter_expressions():
        if isinstance(child, (exp.Subquery, exp.Select)) and child is not node:
            depth = _count_subquery_depth(child, current + 1)
            max_depth = max(max_depth, depth)
        else:
            depth = _count_subquery_depth(child, current)
            max_depth = max(max_depth, depth)
    return max_depth


def _check_suspicious_patterns(expressions: list[exp.Expression]) -> list[str]:
    """Warn on CROSS JOIN, deep subquery nesting, UNION column mismatch."""
    warnings: list[str] = []
    for expression in expressions:
        for join in expression.find_all(exp.Join):
            if join.kind and join.kind.upper() == "CROSS":
                warnings.append("CROSS JOIN detected — may produce very large result set")

        depth = _count_subquery_depth(expression)
        if depth > 3:
            warnings.append(f"Subquery nesting depth of {depth} — consider simplifying")

        for union in expression.find_all(exp.Union):
            left = union.left
            right = union.right
            if isinstance(left, exp.Select) and isinstance(right, exp.Select):
                left_cols = len(left.expressions)
                right_cols = len(right.expressions)
                if left_cols and right_cols and left_cols != right_cols:
                    warnings.append(
                        f"UNION column count mismatch: {left_cols} vs {right_cols}"
                    )

    return warnings


def _has_aggregation(expression: exp.Expression) -> bool:
    """Check whether the expression contains aggregate functions or GROUP BY."""
    if expression.find(exp.Group):
        return True
    agg_types = (exp.Count, exp.Sum, exp.Avg, exp.Min, exp.Max)
    return any(expression.find(agg_type) for agg_type in agg_types)


def _check_large_result_risk(expressions: list[exp.Expression]) -> list[str]:
    """Warn if SELECT has no LIMIT and no aggregation."""
    warnings: list[str] = []
    for expression in expressions:
        if not isinstance(expression, exp.Select) and not expression.find(exp.Select):
            continue
        top_select = expression if isinstance(expression, exp.Select) else expression.find(exp.Select)
        if top_select is None:
            continue
        has_limit = top_select.find(exp.Limit) is not None
        has_agg = _has_aggregation(top_select)
        if not has_limit and not has_agg:
            warnings.append("No LIMIT and no aggregation — result set may be very large")
    return warnings


def check_sql_safety(
    sql: str,
    available_tables: list[str] | None = None,
    available_columns: dict[str, list[str]] | None = None,
) -> SafetyCheckResult:
    """Run all safety checks on a SQL string."""
    issues: list[str] = []
    warnings: list[str] = []

    try:
        expressions = sqlglot.parse(sql, dialect=DIALECT)
    except sqlglot.errors.ParseError as exc:
        return SafetyCheckResult(
            level=SafetyLevel.BLOCKED,
            passed=False,
            issues=[f"SQL parse error: {exc}"],
        )

    expressions = [e for e in expressions if e is not None]
    if not expressions:
        return SafetyCheckResult(
            level=SafetyLevel.BLOCKED,
            passed=False,
            issues=["Empty or unparseable SQL"],
        )

    issues.extend(_check_write_operations(expressions))
    issues.extend(_check_multiple_statements(sql, expressions))

    if available_tables is not None:
        issues.extend(_check_table_existence(expressions, available_tables))

    if available_columns is not None:
        issues.extend(_check_column_existence(expressions, available_columns))

    warnings.extend(_check_missing_where(expressions))
    warnings.extend(_check_suspicious_patterns(expressions))
    warnings.extend(_check_large_result_risk(expressions))

    if issues:
        level = SafetyLevel.BLOCKED
        passed = False
    elif warnings:
        level = SafetyLevel.WARNING
        passed = True
    else:
        level = SafetyLevel.SAFE
        passed = True

    return SafetyCheckResult(level=level, passed=passed, issues=issues, warnings=warnings)
