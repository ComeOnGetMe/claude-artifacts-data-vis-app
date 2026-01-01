from agents.llm_client import create_agent, stream_agent_response


async def test_agent_streaming():
    """Test the agent with a simple prompt (streaming)"""
    print("\n" + "=" * 80)
    print("Testing LLM Agent - Simple Prompt (Streaming)")
    print("=" * 80)
    
    try:
        print("\n1. Creating agent...")
        agent = create_agent()
        print("   ✓ Agent created successfully")
        
        print("\n2. Streaming agent response with prompt: 'Generate a bar chart for sales data'")
        print("-" * 80)
        
        async with agent.run_stream("Generate a bar chart for sales data") as stream_result:
            print("\n3. Streaming Response:")
            print("-" * 80)
            
            # Stream text chunks
            async for chunk in stream_result.stream_text():
                print(chunk, end='', flush=True)
            
            print("\n" + "-" * 80)
            
            # Get final output
            final_output = await stream_result.get_output()
            print("\n4. Final Output:")
            print("-" * 80)
            print(final_output)
            print("-" * 80)
            
            print(f"\n5. Usage: {stream_result.usage}")
            model_name = stream_result.model_name if hasattr(stream_result, 'model_name') else 'N/A'
            print(f"6. Model: {model_name}")
        
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True


async def test_agent_with_stream_agent_response():
    """Test using the stream_agent_response utility function"""
    print("\n" + "=" * 80)
    print("Testing LLM Agent - Using stream_agent_response utility")
    print("=" * 80)
    
    try:
        print("\n1. Creating agent...")
        agent = create_agent()
        print("   ✓ Agent created successfully")
        
        print("\n2. Streaming events with prompt: 'Create a visualization for sales data'")
        print("-" * 80)
        
        event_count = 0
        async for event in stream_agent_response(agent, "Create a visualization for sales data"):
            event_count += 1
            event_type = event.get('type', 'unknown')
            
            if event_type == 'thought':
                print(f"[THOUGHT] {event.get('content', '')[:100]}...")
            elif event_type == 'code':
                lang = event.get('language', 'unknown')
                content_preview = event.get('content', '')[:50]
                print(f"[CODE ({lang})] {content_preview}...")
            elif event_type == 'data':
                payload = event.get('payload', {})
                columns = payload.get('columns', [])
                print(f"[DATA] Columns: {columns}, Rows: {payload.get('row_count', 0)}")
            elif event_type == 'error':
                print(f"[ERROR] {event.get('message', 'Unknown error')}")
            
            if event_count >= 20:  # Limit output for debugging
                print("\n... (truncated after 20 events)")
                break
        
        print("-" * 80)
        print(f"\n3. Total events received: {event_count}")
        
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True