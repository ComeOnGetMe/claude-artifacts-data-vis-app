"""
Chat endpoint for streaming responses
"""
import asyncio
from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

router = APIRouter(prefix="/chat", tags=["chat"])


class ChatMessage(BaseModel):
    """Chat message model"""
    message: str


@router.post("")
async def chat(message: ChatMessage):
    """
    Chat endpoint that streams "Hello World" chunks.
    This is a simple test endpoint to verify streaming works.
    """
    async def generate_chunks():
        """Generator function that yields chunks"""
        text = f"Hello World: {message.message}"
        # Split into chunks to simulate streaming
        chunk_size = 5
        for i in range(0, len(text), chunk_size):
            chunk = text[i:i + chunk_size]
            yield f"data: {chunk}\n\n"
            await asyncio.sleep(0.1)  # Small delay to simulate streaming
    
    return StreamingResponse(
        generate_chunks(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        }
    )

