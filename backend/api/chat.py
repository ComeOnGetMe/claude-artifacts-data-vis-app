"""
Chat endpoint for streaming responses
"""
import asyncio
import json
from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import List, Any

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
    Chat endpoint that streams events based on word-matching rules.
    This is a test endpoint to verify event handling works.
    """
    async def generate_chunks():
        """Generator function that yields SSE events"""
        user_message = message.message.lower()
        
        # Word-matching rules to trigger events
        # If message contains "show data" or "data", send a data event
        if "show data" in user_message or "data" in user_message:
            # Send a thought event first
            thought_event = {
                "type": "thought",
                "content": "I'll show you some sample data."
            }
            yield f"event: thought\ndata: {json.dumps(thought_event)}\n\n"
            await asyncio.sleep(0.1)
            
            # Send a data event with mock data
            mock_data = QueryResult(
                columns=["region", "sales", "date"],
                rows=[
                    ["North", "1000", "2024-01-01"],
                    ["South", "2000", "2024-01-02"],
                    ["East", "1500", "2024-01-03"],
                    ["West", "1800", "2024-01-04"]
                ],
                row_count=4
            )
            data_event = {
                "type": "data",
                "payload": mock_data.model_dump()
            }
            yield f"event: data\ndata: {json.dumps(data_event)}\n\n"
            await asyncio.sleep(0.1)
        
        # If message contains "show code" or "code", send a code event
        if "show code" in user_message or "code" in user_message:
            # Send a thought event first
            thought_event = {
                "type": "thought",
                "content": "I'll generate some UI code for you."
            }
            yield f"event: thought\ndata: {json.dumps(thought_event)}\n\n"
            await asyncio.sleep(0.1)
            
            # Send code chunks (simulating streaming)
            sample_code = """export default function Visualization({ data }) {
  return (
    <div className="p-4">
      <h2 className="text-2xl font-bold mb-4">Data Visualization</h2>
      <p>This is a sample visualization component.</p>
    </div>
  );
}"""
            
            # Split code into chunks to simulate streaming
            chunk_size = 20
            for i in range(0, len(sample_code), chunk_size):
                chunk = sample_code[i:i + chunk_size]
                code_event = {
                    "type": "code",
                    "language": "tsx",
                    "content": chunk
                }
                yield f"event: code\ndata: {json.dumps(code_event)}\n\n"
                await asyncio.sleep(0.05)
        
        # If message contains both "data" and "code", send both events
        if ("show data" in user_message or "data" in user_message) and \
           ("show code" in user_message or "code" in user_message):
            # Already handled above, but ensure both are sent
            pass
        
        # Default: send a thought event if no specific keywords matched
        if "show data" not in user_message and "data" not in user_message and \
           "show code" not in user_message and "code" not in user_message:
            thought_event = {
                "type": "thought",
                "content": f"Received: {message.message}"
            }
            yield f"event: thought\ndata: {json.dumps(thought_event)}\n\n"
    
    return StreamingResponse(
        generate_chunks(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        }
    )

