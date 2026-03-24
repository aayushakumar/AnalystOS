from enum import Enum

from pydantic import BaseModel, Field

from app.schemas.chart_spec import ChartSpec


class Confidence(str, Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class FinalAnswer(BaseModel):
    """The end-to-end response delivered to the user."""

    answer_text: str = Field(description="Natural-language answer to the user's question.")
    insights: list[str] = Field(
        default_factory=list, description="Bullet-point analytical insights."
    )
    chart_spec: ChartSpec | None = Field(
        default=None, description="Optional visualization specification."
    )
    sql_used: str = Field(default="", description="The SQL query that produced the underlying data.")
    evidence: list[str] = Field(
        default_factory=list,
        description="Citations from schema docs or data dictionary supporting the answer.",
    )
    confidence: Confidence = Field(default=Confidence.MEDIUM, description="Assessed confidence level of the answer.")
    limitations: list[str] = Field(
        default_factory=list,
        description="Known caveats, gaps, or assumptions in the analysis.",
    )
    trace_id: str = Field(default="", description="Unique trace identifier for observability.")
