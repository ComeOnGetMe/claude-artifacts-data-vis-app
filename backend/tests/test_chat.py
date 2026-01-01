"""
Tests for the /chat endpoint
"""
import asyncio
import json
import pytest
from unittest.mock import patch, MagicMock

from httpx import AsyncClient, ASGITransport
from main import app


async def mock_stream_agent_response(agent, user_message: str):
    """
    Mock function that mimics stream_agent_response behavior for testing.
    Uses word-matching logic to simulate LLM responses.
    """
    user_message_lower = user_message.lower()
    
    # If message contains "show data" or "data", send a data event
    if "show data" in user_message_lower or "data" in user_message_lower:
        yield {
            "type": "thought",
            "content": "I'll show you some sample data."
        }
        await asyncio.sleep(0.01)
        
        yield {
            "type": "data",
            "payload": {
                "columns": ["region", "sales"],
                "rows": [
                    ["North", 1000],
                    ["South", 2000],
                    ["East", 1500],
                    ["West", 1800]
                ],
                "row_count": 4
            }
        }
        await asyncio.sleep(0.01)
    
    # If message contains "show code" or "code", send a code event
    if "show code" in user_message_lower or "code" in user_message_lower:
        yield {
            "type": "thought",
            "content": "I'll generate some UI code for you."
        }
        await asyncio.sleep(0.01)
        
        sample_code = """import React from 'react';
import { ResponsiveContainer, BarChart, Bar, XAxis, YAxis, Tooltip, CartesianGrid } from 'recharts';

export default function Visualization({ data }) {
  if (!data || data.length === 0) {
    return (
      <div className="p-4 text-center text-gray-500">
        No data available to visualize.
      </div>
    );
  }

  return (
    <div className="p-4 w-full h-full">
      <h2 className="text-2xl font-bold mb-4">Sales by Region</h2>
      <div className="w-full" style={{ height: '400px' }}>
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={data}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis 
              dataKey="region" 
              tick={{ fill: '#666' }}
            />
            <YAxis 
              tick={{ fill: '#666' }}
            />
            <Tooltip />
            <Bar dataKey="sales" fill="#3b82f6" />
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}"""
        
        # Split code into chunks to simulate streaming
        chunk_size = 20
        for i in range(0, len(sample_code), chunk_size):
            chunk = sample_code[i:i + chunk_size]
            yield {
                "type": "code",
                "language": "tsx",
                "content": chunk
            }
            await asyncio.sleep(0.01)
    
    # Default: send a thought event if no specific keywords matched
    if ("show data" not in user_message_lower and "data" not in user_message_lower and
        "show code" not in user_message_lower and "code" not in user_message_lower):
        yield {
            "type": "thought",
            "content": f"Received: {user_message}"
        }


@pytest.mark.asyncio
@patch('api.chat.stream_agent_response', side_effect=mock_stream_agent_response)
@patch('api.chat._llm_agent', new_callable=MagicMock)
async def test_chat_endpoint_streams_thought_event(mock_agent, mock_stream):
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
@patch('api.chat.stream_agent_response', side_effect=mock_stream_agent_response)
@patch('api.chat._llm_agent', new_callable=MagicMock)
async def test_chat_endpoint_streams_data_event(mock_agent, mock_stream):
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
@patch('api.chat.stream_agent_response', side_effect=mock_stream_agent_response)
@patch('api.chat._llm_agent', new_callable=MagicMock)
async def test_chat_endpoint_streams_code_event(mock_agent, mock_stream):
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
@patch('api.chat.stream_agent_response', side_effect=mock_stream_agent_response)
@patch('api.chat._llm_agent', new_callable=MagicMock)
async def test_chat_endpoint_with_different_messages(mock_agent, mock_stream):
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
