"""
Chat endpoint for streaming responses
"""
import asyncio
import json
from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import List, Any
from agents.llm_client import create_agent, stream_agent_response
router = APIRouter(prefix="/chat", tags=["chat"])

class ChatMessage(BaseModel):
    """Chat message model"""
    message: str


class QueryResult(BaseModel):
    """Query result model for data events"""
    columns: List[str]
    rows: List[List[Any]]
    row_count: int


@router.post("")
async def chat(message: ChatMessage):
    """
    Chat endpoint that streams events using LLM agent.
    Creates a fresh agent on each request to ensure AWS credentials are current.
    """
    async def generate_chunks():
        """Generator function that yields SSE events"""
        # Create a fresh agent on each request to ensure credentials are current
        # This prevents issues with expired AWS tokens when the server runs for extended periods
        agent = create_agent()

        async for event in stream_agent_response(agent, message.message):
            yield f"event: {event['type']}\ndata: {json.dumps(event)}\n\n"
            await asyncio.sleep(0.01)

    return StreamingResponse(
        generate_chunks(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        }
    )

