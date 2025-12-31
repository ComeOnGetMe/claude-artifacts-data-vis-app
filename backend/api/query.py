"""
Query endpoint for local DuckDB execution
"""
import subprocess
import json
import tempfile
import os
import sys
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


@router.post("/local_duckdb")
async def query_local_duckdb(request: QueryRequest):
    """
    Execute SQL query against local DuckDB using a Python subprocess.
    This is for debugging purposes.
    """
    # Create a temporary Python script file to avoid shell escaping issues
    script_content = """
import duckdb
import json
import sys

sql_query = sys.argv[1]

try:
    conn = duckdb.connect()
    result = conn.execute(sql_query).fetchall()
    columns = [desc[0] for desc in conn.description] if conn.description else []
    
    # Convert to JSON-serializable format
    rows = [[str(cell) if cell is not None else None for cell in row] for row in result]
    
    output = {
        "columns": columns,
        "rows": rows,
        "row_count": len(rows)
    }
    print(json.dumps(output))
except Exception as e:
    error_output = {
        "error": str(e),
        "columns": [],
        "rows": [],
        "row_count": 0
    }
    print(json.dumps(error_output))
    sys.exit(1)
"""
    
    try:
        # Write script to temporary file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(script_content)
            script_path = f.name
        
        try:
            # Execute the script using the current Python interpreter (venv's Python)
            python_executable = sys.executable
            process = subprocess.run(
                [python_executable, script_path, request.sql],
                capture_output=True,
                text=True,
                timeout=30  # 30 second timeout
            )
            
            # Try to parse JSON output even if return code is non-zero
            # (the script may output error JSON before exiting)
            try:
                result_data = json.loads(process.stdout.strip())
                
                if "error" in result_data:
                    raise HTTPException(
                        status_code=400,
                        detail=f"SQL execution error: {result_data['error']}"
                    )
            except json.JSONDecodeError:
                # If we can't parse JSON and return code is non-zero, it's a real error
                if process.returncode != 0:
                    raise HTTPException(
                        status_code=500,
                        detail=f"DuckDB execution failed: {process.stderr or 'Unknown error'}"
                    )
                raise
            
            return QueryResult(**result_data)
        
        finally:
            # Clean up temporary file
            if os.path.exists(script_path):
                os.unlink(script_path)
    
    except HTTPException:
        # Re-raise HTTPExceptions (like 400 for SQL errors) without wrapping
        raise
    except subprocess.TimeoutExpired:
        raise HTTPException(
            status_code=504,
            detail="Query execution timed out"
        )
    except json.JSONDecodeError as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to parse DuckDB output: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Unexpected error: {str(e)}"
        )

