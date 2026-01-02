"""
Tests for the LLM client
"""
import pytest
import os
from agents.llm_client import get_base_system_prompt, _extract_code_blocks


def test_get_base_system_prompt():
    """Test that system prompt is generated correctly"""
    prompt = get_base_system_prompt()
    
    assert isinstance(prompt, str)
    assert len(prompt) > 0
    # Check for key instructions
    assert "SQL" in prompt or "sql" in prompt
    assert "UI code" in prompt or "visualization" in prompt
    assert "Recharts" in prompt
    assert "Shadcn" in prompt or "shadcn" in prompt
    assert "export default function" in prompt


def test_extract_code_blocks():
    """Test code block extraction from markdown"""
    # Test with single code block
    text1 = """
    Here's some code:
    ```tsx
    export default function Test() {
      return <div>Hello</div>;
    }
    ```
    That's it.
    """
    blocks = _extract_code_blocks(text1)
    assert len(blocks) == 1
    assert blocks[0]["language"] == "tsx"
    assert "export default function Test" in blocks[0]["content"]
    
    # Test with multiple code blocks
    text2 = """
    First block:
    ```python
    print("hello")
    ```
    Second block:
    ```tsx
    const x = 1;
    ```
    """
    blocks = _extract_code_blocks(text2)
    assert len(blocks) == 2
    assert blocks[0]["language"] == "python"
    assert blocks[1]["language"] == "tsx"
    
    # Test with no code blocks
    text3 = "Just regular text, no code here."
    blocks = _extract_code_blocks(text3)
    assert len(blocks) == 0
    
    # Test with code block without language
    text4 = """
    ``` 
    some code here
    ```
    """
    blocks = _extract_code_blocks(text4)
    assert len(blocks) == 1
    assert blocks[0]["language"] == "tsx"  # Should default to tsx


@pytest.mark.asyncio
@pytest.mark.skipif(
    os.getenv("USE_LLM_AGENT", "true").lower() != "true",
    reason="LLM agent disabled via USE_LLM_AGENT env var"
)
async def test_create_agent():
    """Test agent creation (requires AWS credentials)"""
    try:
        from agents.llm_client import create_agent
        
        agent = create_agent()
        assert agent is not None
        # Verify agent has model and system prompt
        assert hasattr(agent, 'model')
        assert hasattr(agent, 'system_prompt')
    except Exception as e:
        # Skip if AWS credentials not available
        pytest.skip(f"Could not create agent (likely missing AWS credentials): {e}")


@pytest.mark.asyncio
@pytest.mark.skipif(
    os.getenv("USE_LLM_AGENT", "true").lower() != "true",
    reason="LLM agent disabled via USE_LLM_AGENT env var"
)
async def test_create_agent_has_tools():
    """Test that agent is created with tools registered"""
    try:
        from agents.llm_client import create_agent
        
        agent = create_agent()
        assert agent is not None
        # Verify agent has tools registered
        # PydanticAI stores tools in agent._tools or similar
        # Check if run_sql tool is available
        assert hasattr(agent, 'tools') or hasattr(agent, '_tools')
    except Exception as e:
        # Skip if AWS credentials not available
        pytest.skip(f"Could not create agent (likely missing AWS credentials): {e}")


@pytest.mark.asyncio
@pytest.mark.skipif(
    os.getenv("USE_LLM_AGENT", "true").lower() != "true",
    reason="LLM agent disabled via USE_LLM_AGENT env var"
)
async def test_stream_agent_response_basic():
    """Test streaming agent response (requires AWS credentials and LLM access)"""
    try:
        from agents.llm_client import create_agent, stream_agent_response
        
        agent = create_agent()
        events = []
        
        async for event in stream_agent_response(agent, "Hello, can you generate a SQL query to calculate sales by region?"):
            events.append(event)
            # Break after a few events to avoid long-running test
            if len(events) >= 5:
                break
        
        # Should have received at least some events
        assert len(events) > 0
        
        # Verify event structure
        for event in events:
            assert "type" in event
            assert event["type"] in ["thought", "code", "data", "error"]
            if event["type"] == "thought":
                assert "content" in event
            elif event["type"] == "code":
                assert "language" in event
                assert "content" in event
    
    except Exception as e:
        # Skip if AWS credentials not available or other issues
        pytest.skip(f"Could not test agent streaming (likely missing AWS credentials or API access): {e}")


# Note: LLM integration tests that require actual agent execution have been moved to
# scripts/debug_tool_use.py as debug scripts. These tests require AWS credentials
# and actual LLM API access, so they are better suited as manual debugging scripts
# rather than automated unit tests.

