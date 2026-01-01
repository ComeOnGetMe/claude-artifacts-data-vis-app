#!/usr/bin/env python3
"""
Debug script to test the /chat endpoint with a hello world prompt.
"""
import asyncio
import sys
import httpx

async def test_chat_endpoint():
    """Test the /chat endpoint with a hello world prompt"""
    base_url = "http://localhost:8000"
    endpoint = f"{base_url}/chat"

    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            print("\n2. Sending POST request with message: 'hello world'")
            
            response = await client.post(
                endpoint,
                json={"message": "hello world"},
                headers={"Accept": "text/event-stream"},
            )
            
            print(f"\n3. Response Status: {response.status_code}")
            print(f"   Content-Type: {response.headers.get('content-type', 'N/A')}")
            
            if response.status_code != 200:
                print(f"\n✗ Error: Received status code {response.status_code}")
                print(f"   Response: {response.text}")
                return False
            
            print("\n4. Raw Response:")
            print("-" * 80)
            
            # Print response as-is, line by line
            async for line in response.aiter_lines():
                print(line)
            
            print("-" * 80)
            print("\n✓ Response received successfully")
            return True
                
    except httpx.ConnectError:
        print(f"\n✗ Error: Could not connect to {base_url}")
        print("   Make sure the backend server is running:")
        print("   cd backend && uv run uvicorn main:app --reload")
        return False
    except httpx.TimeoutException:
        print("\n✗ Error: Request timed out")
        return False
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """Main function"""
    print("\n" + "=" * 80)
    print("Chat Endpoint Debugging Script")
    print("=" * 80)
    print("\nThis script tests the /chat endpoint with a 'hello world' prompt.")
    print("Make sure the backend server is running on http://localhost:8000")
    print("=" * 80)
    
    success = await test_chat_endpoint()
    
    print("\n" + "=" * 80)
    print("Summary")
    print("=" * 80)
    if success:
        print("✓ Test passed!")
        return 0
    else:
        print("✗ Test failed")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)

