"""
Tests for the /query/local_duckdb endpoint
"""
import pytest
from httpx import AsyncClient, ASGITransport
from main import app


@pytest.mark.asyncio
async def test_query_local_duckdb_simple_select():
    """Test that /query/local_duckdb executes a simple SQL query"""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post(
            "/query/local_duckdb",
            json={"sql": "SELECT 1 as value, 'test' as name"}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert "columns" in data
        assert "rows" in data
        assert "row_count" in data
        assert data["row_count"] == 1
        assert len(data["columns"]) == 2
        assert len(data["rows"]) == 1


@pytest.mark.asyncio
async def test_query_local_duckdb_invalid_sql():
    """Test that /query/local_duckdb handles invalid SQL gracefully"""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post(
            "/query/local_duckdb",
            json={"sql": "SELECT * FROM nonexistent_table"}
        )
        
        # Should return an error response (400 for SQL errors)
        assert response.status_code == 400
        data = response.json()
        assert "detail" in data

