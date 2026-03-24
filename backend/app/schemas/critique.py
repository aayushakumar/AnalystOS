from enum import Enum

from pydantic import BaseModel, Field


class Verdict(str, Enum):
    ACCEPT = "accept"
    RETRY = "retry"
    REFUSE = "refuse"


class CritiqueVerdict(BaseModel):
    """Structured output from the critique / quality-gate agent."""

    verdict: Verdict = Field(description="Final verdict on the analysis quality.")
    issues: list[str] = Field(
        default_factory=list, description="Specific problems found in the analysis."
    )
    confidence_score: float = Field(
        ge=0.0, le=1.0, description="Overall confidence in the analysis (0.0–1.0)."
    )
    addresses_question: bool = Field(
        default=True, description="Whether the analysis actually answers the user's original question."
    )
    evidence_sufficient: bool = Field(
        default=True, description="Whether there is enough data evidence to support the conclusions."
    )
    retry_recommended: bool = Field(
        default=False, description="Whether a retry with adjusted parameters is likely to improve results."
    )
    retry_reason: str | None = Field(
        default=None, description="Explanation of why a retry is recommended, if applicable."
    )
