"""
Tests for the /chat endpoint
"""
import pytest
import json
from httpx import AsyncClient, ASGITransport
from main import app


@pytest.mark.asyncio
async def test_chat_endpoint_streams_thought_event():
    """Test that /chat endpoint streams thought events for regular messages"""
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
        
        # Verify we received SSE events
        assert len(content) > 0
        assert "event: thought" in content
        assert "data:" in content
        
        # Parse and verify thought event
        lines = content.split("\n")
        found_thought = False
        for i, line in enumerate(lines):
            if line.startswith("event: thought"):
                # Next non-empty line should be data
                for j in range(i + 1, min(i + 3, len(lines))):
                    if lines[j].startswith("data: "):
                        data_str = lines[j][6:]  # Remove "data: " prefix
                        data = json.loads(data_str)
                        assert data["type"] == "thought"
                        assert "test message" in data["content"] or "Received:" in data["content"]
                        found_thought = True
                        break
                break
        
        assert found_thought, "Should have found a thought event"


@pytest.mark.asyncio
async def test_chat_endpoint_streams_data_event():
    """Test that /chat endpoint streams data events when message contains 'data'"""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post(
            "/chat",
            json={"message": "show data"}
        )
        
        assert response.status_code == 200
        
        # Read the stream
        content = ""
        async for chunk in response.aiter_text():
            content += chunk
        
        # Verify we received data event (should have both thought and data)
        assert "event: data" in content
        assert "event: thought" in content
        
        # Parse and verify data event
        lines = content.split("\n")
        found_data = False
        for i, line in enumerate(lines):
            if line.startswith("event: data"):
                # Next non-empty line should be data
                for j in range(i + 1, min(i + 3, len(lines))):
                    if lines[j].startswith("data: "):
                        data_str = lines[j][6:]  # Remove "data: " prefix
                        data = json.loads(data_str)
                        assert data["type"] == "data"
                        assert "payload" in data
                        assert "columns" in data["payload"]
                        assert "rows" in data["payload"]
                        assert len(data["payload"]["columns"]) > 0
                        assert len(data["payload"]["rows"]) > 0
                        found_data = True
                        break
                break
        
        assert found_data, "Should have found a data event"


@pytest.mark.asyncio
async def test_chat_endpoint_streams_code_event():
    """Test that /chat endpoint streams code events when message contains 'code'"""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post(
            "/chat",
            json={"message": "show code"}
        )
        
        assert response.status_code == 200
        
        # Read the stream
        content = ""
        async for chunk in response.aiter_text():
            content += chunk
        
        # Verify we received code events (should have both thought and code)
        assert "event: code" in content
        assert "event: thought" in content
        
        # Parse and verify code event (there should be multiple code chunks)
        lines = content.split("\n")
        found_code_events = []
        for i, line in enumerate(lines):
            if line.startswith("event: code"):
                # Next non-empty line should be data
                for j in range(i + 1, min(i + 3, len(lines))):
                    if lines[j].startswith("data: "):
                        data_str = lines[j][6:]  # Remove "data: " prefix
                        data = json.loads(data_str)
                        assert data["type"] == "code"
                        assert "language" in data
                        assert data["language"] == "tsx"
                        assert "content" in data
                        found_code_events.append(data)
                        break
        
        assert len(found_code_events) > 0, "Should have found at least one code event"


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
            
            # Should receive at least a thought event
            assert "event:" in content
            assert "data:" in content

