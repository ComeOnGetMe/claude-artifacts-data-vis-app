"""
Query endpoint for local DuckDB execution
"""
import asyncio
import duckdb
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Any

router = APIRouter(prefix="/query", tags=["query"])


class QueryRequest(BaseModel):
    """Query request model"""
    sql: str


class QueryResult(BaseModel):
    """Query result model"""
    columns: List[str]
    rows: List[List[Any]]
    row_count: int


def _execute_duckdb_query(sql: str) -> dict:
    """
    Synchronous helper function to execute DuckDB query.
    This will be run in a thread pool to avoid blocking the event loop.
    """
    try:
        conn = duckdb.connect()
        result = conn.execute(sql).fetchall()
        columns = [desc[0] for desc in conn.description] if conn.description else []
        
        # Convert to JSON-serializable format
        rows = [[str(cell) if cell is not None else None for cell in row] for row in result]
        
        return {
            "columns": columns,
            "rows": rows,
            "row_count": len(rows)
        }
    except Exception as e:
        raise ValueError(f"SQL execution error: {str(e)}")


@router.post("/local_duckdb")
async def query_local_duckdb(request: QueryRequest):
    """
    Execute SQL query against local DuckDB directly.
    This is for debugging purposes.
    """
    try:
        # Run the synchronous DuckDB operation in a thread pool
        result_data = await asyncio.to_thread(_execute_duckdb_query, request.sql)
        return QueryResult(**result_data)
    
    except ValueError as e:
        # SQL execution errors (invalid SQL, table not found, etc.)
        raise HTTPException(
            status_code=400,
            detail=str(e)
        )
    except Exception as e:
        # Unexpected errors
        raise HTTPException(
            status_code=500,
            detail=f"Unexpected error: {str(e)}"
        )

