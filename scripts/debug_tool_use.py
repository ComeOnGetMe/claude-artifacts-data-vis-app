"""
Debug script to test LLM agent tool use (run_sql)
This requires AWS credentials and actual LLM access.
"""
import asyncio
import sys

from agents.llm_client import create_agent, stream_agent_response


async def test_tool_use_schema_description():
    """
    Test that the agent can use the run_sql tool to describe a table schema.
    This is the test case from implementation plan Step 4.1.
    """
    print("\n" + "=" * 80)
    print("Testing LLM Agent Tool Use - Schema Description")
    print("=" * 80)
    
    print("\n1. Creating agent with run_sql tool...")
    agent = create_agent()
    print("   ✓ Agent created successfully")
    
    prompt = "describe schema of table 's3://disco-feature-store/features-main/lean_and_long/train/version_timestamp=2025-11-16Z0010/*.parquet'"
    print(f"\n2. Sending prompt: {prompt!r}")
    print("-" * 80)
    
    event_count = 0
    found_data_event = False
    found_code_event = False
    
    async for event in stream_agent_response(agent, prompt):
        print(event)
        if event.get('type') == 'data':
            found_data_event = True
        if event.get('type') == 'code':
            found_code_event = True
    
    print("-" * 80)
    print("\n3. Summary:")
    print(f"   Total events: {event_count}")
    print(f"   Data event found: {found_data_event}")
    print(f"   Code event found: {found_code_event}")
    
    if found_data_event:
        print("\n✓ SUCCESS: Tool was called and returned data!")
    else:
        print("\n⚠ WARNING: No data event found - tool may not have been called")
    
    return found_data_event


async def test_tool_use_simple_query():
    """
    Test that the agent can use the run_sql tool with a simple query.
    """
    print("\n" + "=" * 80)
    print("Testing LLM Agent Tool Use - Simple Query")
    print("=" * 80)
    
    print("\n1. Creating agent with run_sql tool...")
    agent = create_agent()
    print("   ✓ Agent created successfully")
    
    prompt = "Show me the top 5 rows from a table. Use SELECT 1 as id, 'test' as name LIMIT 5"
    print(f"\n2. Sending prompt: {prompt!r}")
    print("-" * 80)

    found_data_event = False
    
    async for event in stream_agent_response(agent, prompt):
        print(event)
        if event.get('type') == 'data':
            found_data_event = True
    
    print("-" * 80)
    if found_data_event:
        print("\n✓ SUCCESS: Tool was called and returned data!")
    else:
        print("\n⚠ WARNING: No data event found")
    
    return found_data_event


async def test_direct_agent_run():
    """Test agent.run() directly (non-streaming) to see if tools work"""
    print("\n" + "=" * 80)
    print("Testing LLM Agent - Direct Run (Non-Streaming)")
    print("=" * 80)
    
    print("\n1. Creating agent...")
    agent = create_agent()
    print("   ✓ Agent created")
    
    # Check tool registration
    print("\n2. Checking tool registration...")
    if hasattr(agent, 'tools'):
        print(f"   Tools: {agent.tools}")
    if hasattr(agent, '_tools'):
        print(f"   _tools: {agent._tools}")
    
    prompt = "Call the run_sql tool with query='SELECT 1 as test_value'"
    print(f"\n3. Running agent with prompt: {prompt!r}")
    print("-" * 80)
    
    result = await agent.run(prompt)
    
    print(f"\n4. Result type: {type(result)}")
    print(f"   Result: {result}")
    
    return True


async def main():
    """Run all tool use tests"""
    print("=" * 80)
    print("LLM Agent Tool Use Debug Script")
    print("=" * 80)
    print("\nThis script tests that the LLM agent can successfully call the run_sql tool.")
    print("It requires AWS credentials and actual LLM API access.")
    print("\nNote: These are integration tests, not unit tests.")
    
    results = []
    
    # Test 0: Direct run (non-streaming) to debug tool registration
    # result0 = await test_direct_agent_run()
    # results.append(("Direct Run", result0))
    
    # Test 1: Simple query
    print("\n" + "=" * 80)
    result1 = await test_tool_use_simple_query()
    results.append(("Simple Query", result1))
    
    # Test 2: Schema description (may fail if S3 not configured)
    print("\n" + "=" * 80)
    result2 = await test_tool_use_schema_description()
    results.append(("Schema Description", result2))
    
    # Summary
    print("\n" + "=" * 80)
    print("Test Summary")
    print("=" * 80)
    for test_name, passed in results:
        status = "✓ PASSED" if passed else "✗ FAILED"
        print(f"{test_name}: {status}")
    
    all_passed = all(result[1] for result in results)
    return all_passed


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)

