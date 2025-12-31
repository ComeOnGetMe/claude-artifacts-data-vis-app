"""
Tests for the /chat endpoint
"""
import pytest
from httpx import AsyncClient, ASGITransport
from main import app


@pytest.mark.asyncio
async def test_chat_endpoint_streams_response():
    """Test that /chat endpoint streams chunks correctly"""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post(
            "/chat",
            json={"message": "test message"}
        )
        
        assert response.status_code == 200
        assert response.headers["content-type"] == "text/event-stream; charset=utf-8"
        
        # Read the stream
        content = ""
        async for chunk in response.aiter_text():
            content += chunk
        
        # Verify we received chunks
        assert len(content) > 0
        assert "Hello World: test message" in content.replace("\n", "").replace("data: ", "")


@pytest.mark.asyncio
async def test_chat_endpoint_with_different_messages():
    """Test that /chat endpoint handles different message inputs"""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        test_messages = [
            "hello",
            "show me sales data",
            "create a bar chart",
        ]
        
        for msg in test_messages:
            response = await client.post(
                "/chat",
                json={"message": msg}
            )
            
            assert response.status_code == 200
            
            content = ""
            async for chunk in response.aiter_text():
                content += chunk
            
            assert msg in content.replace("\n", "").replace("data: ", "")

