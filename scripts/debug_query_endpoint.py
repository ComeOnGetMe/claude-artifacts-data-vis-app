#!/usr/bin/env python3
"""
Debug script to test the /query/local_duckdb endpoint.
These are integration tests that require a running backend server.
"""
import asyncio
import sys
import httpx


async def test_query_simple_select():
    """Test that /query/local_duckdb executes a simple SQL query"""
    base_url = "http://localhost:8000"
    endpoint = f"{base_url}/query/local_duckdb"
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            print("\n2. Sending POST request with SQL: SELECT 1 as value, 'test' as name")
            
            response = await client.post(
                endpoint,
                json={"sql": "SELECT * FROM read_parquet('test.parquet') limit 0;"}
            )
            
            print(f"\n3. Response Status: {response.status_code}")
            
            if response.status_code != 200:
                print(f"\n✗ Error: Received status code {response.status_code}")
                print(f"   Response: {response.text}")
                return False
            
            data = response.json()
            
            # Validate response structure
            assert "columns" in data, "Response missing 'columns' field"
            assert "rows" in data, "Response missing 'rows' field"
            assert "row_count" in data, "Response missing 'row_count' field"
            assert data["row_count"] == 1, f"Expected 1 row, got {data['row_count']}"
            assert len(data["columns"]) == 2, f"Expected 2 columns, got {len(data['columns'])}"
            assert len(data["rows"]) == 1, f"Expected 1 row, got {len(data['rows'])}"
            
            print("   ✓ Response structure valid")
            print(f"   ✓ Row count: {data['row_count']}")
            print(f"   ✓ Columns: {data['columns']}")
            print(f"   ✓ Rows: {data['rows']}")
            return True
            
    except httpx.ConnectError:
        print(f"\n✗ Error: Could not connect to {base_url}")
        print("   Make sure the backend server is running:")
        print("   cd backend && uv run uvicorn main:app --reload")
        return False
    except httpx.TimeoutException:
        print("\n✗ Error: Request timed out")
        return False
    except AssertionError as e:
        print(f"\n✗ Assertion Error: {e}")
        return False
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_query_invalid_sql():
    """Test that /query/local_duckdb handles invalid SQL gracefully"""
    base_url = "http://localhost:8000"
    endpoint = f"{base_url}/query/local_duckdb"
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            print("\n2. Sending POST request with invalid SQL: SELECT * FROM nonexistent_table")
            
            response = await client.post(
                endpoint,
                json={"sql": "SELECT * FROM nonexistent_table"}
            )
            
            print(f"\n3. Response Status: {response.status_code}")
            
            if response.status_code != 400:
                print(f"\n✗ Error: Expected status code 400, got {response.status_code}")
                print(f"   Response: {response.text}")
                return False
            
            data = response.json()
            
            # Validate error response structure
            assert "detail" in data, "Error response missing 'detail' field"
            
            print("   ✓ Error response structure valid")
            print(f"   ✓ Error detail: {data['detail']}")
            return True
            
    except httpx.ConnectError:
        print(f"\n✗ Error: Could not connect to {base_url}")
        print("   Make sure the backend server is running:")
        print("   cd backend && uv run uvicorn main:app --reload")
        return False
    except httpx.TimeoutException:
        print("\n✗ Error: Request timed out")
        return False
    except AssertionError as e:
        print(f"\n✗ Assertion Error: {e}")
        return False
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """Main function"""
    print("\n" + "=" * 80)
    print("Query Endpoint Debugging Script")
    print("=" * 80)
    print("\nThis script tests the /query/local_duckdb endpoint.")
    print("Make sure the backend server is running on http://localhost:8000")
    print("=" * 80)
    
    print("\n" + "=" * 80)
    print("Testing Simple SELECT Query")
    print("=" * 80)
    success1 = await test_query_simple_select()
    
    print("\n" + "=" * 80)
    print("Testing Invalid SQL Handling")
    print("=" * 80)
    success2 = await test_query_invalid_sql()
    
    print("\n" + "=" * 80)
    print("Test Summary")
    print("=" * 80)
    if success1 and success2:
        print("✓ All tests passed!")
        return 0
    else:
        print("✗ Some tests failed")
        if not success1:
            print("  - Simple SELECT query test failed")
        if not success2:
            print("  - Invalid SQL handling test failed")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)

