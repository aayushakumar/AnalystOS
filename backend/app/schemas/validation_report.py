from enum import Enum

from pydantic import BaseModel, Field


class Severity(str, Enum):
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


class ValidationIssue(BaseModel):
    severity: Severity = Field(default=Severity.INFO)
    message: str = Field(default="")
    location: str = Field(default="", description="SQL fragment or column reference where the issue was found.")


class ValidationReport(BaseModel):
    """Structured output from the SQL-validation agent."""

    valid: bool = Field(description="Whether the SQL passed all validation checks.")
    issues: list[ValidationIssue] = Field(default_factory=list)
    requires_retry: bool = Field(
        default=False, description="Whether the issues are severe enough to warrant re-generation."
    )
    risk_notes: list[str] = Field(
        default_factory=list,
        description="Potential risks that passed validation but deserve attention.",
    )
    tables_verified: list[str] = Field(
        default_factory=list, description="Tables confirmed to exist in the schema."
    )
    columns_verified: list[str] = Field(
        default_factory=list, description="Columns confirmed to exist in the schema."
    )
