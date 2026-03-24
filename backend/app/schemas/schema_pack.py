from pydantic import BaseModel, Field


class TableInfo(BaseModel):
    table_name: str
    description: str = Field(default="")
    row_count_estimate: int = Field(default=0, ge=0, description="Estimated number of rows in the table.")


class ColumnInfo(BaseModel):
    table_name: str
    column_name: str
    data_type: str = Field(default="")
    description: str = Field(default="")
    sample_values: list[str] = Field(
        default_factory=list, description="Representative sample values for the column."
    )


class JoinInfo(BaseModel):
    left_table: str
    left_column: str
    right_table: str
    right_column: str
    join_type: str = Field(default="inner", description="E.g. 'inner', 'left', 'right', 'full'.")
    description: str = Field(default="")


class SchemaPack(BaseModel):
    """Structured context package describing the relevant DB schema for a query."""

    tables: list[TableInfo] = Field(default_factory=list)
    columns: list[ColumnInfo] = Field(default_factory=list)
    joins: list[JoinInfo] = Field(default_factory=list)
    relevant_metrics: list[str] = Field(
        default_factory=list, description="Business metrics relevant to the query."
    )
    data_freshness: str = Field(
        default="", description="Human-readable description of data recency."
    )
