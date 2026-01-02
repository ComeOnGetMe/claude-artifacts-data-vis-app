# Models package
from typing import List, Any, Literal
from pydantic import BaseModel


class QueryResult(BaseModel):
    """Query result model for data events"""
    columns: List[str]
    rows: List[List[Any]]
    row_count: int


class RunSQLTool(BaseModel):
    """Tool model for running SQL queries"""
    query: str
    limit: int = 1000
    data_source: Literal["duckdb"] = "duckdb"
