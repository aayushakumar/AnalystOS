from enum import Enum

from pydantic import BaseModel, Field


class IntentType(str, Enum):
    DESCRIPTIVE = "descriptive"
    COMPARATIVE = "comparative"
    DIAGNOSTIC = "diagnostic"
    VISUALIZATION = "visualization"
    AMBIGUOUS = "ambiguous"
    UNSUPPORTED = "unsupported"
    UNSAFE = "unsafe"


class RiskLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class IntentClassification(BaseModel):
    """Structured output from the intent-classification agent."""

    intent: IntentType = Field(description="Detected analytical intent category.")
    risk_level: RiskLevel = Field(default=RiskLevel.LOW, description="Assessed risk level of the query.")
    requires_clarification: bool = Field(
        default=False, description="Whether the query is too ambiguous to proceed without follow-up."
    )
    route: str = Field(
        default="schema_discovery",
        description="Next routing step: 'schema_discovery', 'clarify', or 'refuse'.",
    )
    reasoning: str = Field(default="", description="Brief explanation of the classification decision.")
