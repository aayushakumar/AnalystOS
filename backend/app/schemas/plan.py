from enum import Enum

from pydantic import BaseModel, Field


class Complexity(str, Enum):
    SIMPLE = "simple"
    MODERATE = "moderate"
    COMPLEX = "complex"


class TimeWindow(BaseModel):
    start: str = Field(description="ISO-8601 date or relative expression (e.g. '30d ago').")
    end: str = Field(description="ISO-8601 date or relative expression (e.g. 'now').")
    granularity: str = Field(description="Time bucket: 'day', 'week', 'month', 'quarter', 'year'.")


class FilterSpec(BaseModel):
    column: str
    operator: str = Field(description="SQL-style operator: '=', '!=', '>', '<', 'IN', 'LIKE', etc.")
    value: str


class AnalysisPlan(BaseModel):
    """Structured analysis plan produced by the planner agent."""

    business_intent: str = Field(description="Plain-language restatement of the user's goal.")
    entities: list[str] = Field(
        default_factory=list, description="Business entities involved (e.g. 'customers', 'orders')."
    )
    metrics: list[str] = Field(
        default_factory=list, description="Measures to compute (e.g. 'revenue', 'churn_rate')."
    )
    time_window: TimeWindow | None = Field(
        default=None, description="Temporal scope of the analysis, if applicable."
    )
    dimensions: list[str] = Field(
        default_factory=list, description="Grouping dimensions (e.g. 'region', 'product_category')."
    )
    filters: list[FilterSpec] = Field(
        default_factory=list, description="Row-level filters to apply."
    )
    ambiguity_flags: list[str] = Field(
        default_factory=list,
        description="Aspects of the query that are ambiguous or assumed.",
    )
    candidate_tables: list[str] = Field(
        default_factory=list, description="Tables expected to participate in the query."
    )
    complexity: Complexity = Field(default=Complexity.MODERATE, description="Estimated query complexity tier.")
    requires_clarification: bool = Field(
        default=False, description="Whether the planner recommends asking the user for clarification."
    )
    clarification_questions: list[str] = Field(
        default_factory=list,
        description="Suggested follow-up questions if clarification is needed.",
    )
