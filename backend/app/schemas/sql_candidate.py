from pydantic import BaseModel, Field


class SQLCandidate(BaseModel):
    """Structured output from the SQL-generation agent."""

    sql: str = Field(description="Generated SQL query string.")
    rationale: str = Field(description="Explanation of the query strategy and key decisions.")
    tables_used: list[str] = Field(default_factory=list)
    metrics_computed: list[str] = Field(
        default_factory=list, description="Metrics this query produces."
    )
    time_range: str | None = Field(
        default=None, description="Human-readable time range covered, if any."
    )
    estimated_complexity: str = Field(
        default="moderate", description="Rough complexity label: 'simple', 'moderate', or 'complex'."
    )
