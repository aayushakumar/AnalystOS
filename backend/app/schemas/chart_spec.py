from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class ChartType(str, Enum):
    BAR = "bar"
    LINE = "line"
    PIE = "pie"
    SCATTER = "scatter"
    TABLE = "table"
    HISTOGRAM = "histogram"
    STACKED_BAR = "stacked_bar"
    AREA = "area"


class ChartSpec(BaseModel):
    """Visualization specification produced by the chart-selection agent."""

    chart_type: ChartType = Field(description="Type of chart to render.")
    title: str = Field(description="Human-readable chart title.")
    x_field: str = Field(description="Column mapped to the x-axis.")
    y_field: str = Field(description="Column mapped to the y-axis.")
    color_field: str | None = Field(
        default=None, description="Optional column for color encoding / series split."
    )
    annotations: list[str] = Field(
        default_factory=list, description="Textual annotations to overlay on the chart."
    )
    data: list[dict[str, Any]] = Field(
        default_factory=list, description="Row-oriented data points for the chart."
    )
