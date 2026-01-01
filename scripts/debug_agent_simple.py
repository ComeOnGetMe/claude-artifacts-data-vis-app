#!/usr/bin/env python3
"""
Debug script to test the LLM agent with simple prompts.
"""
import asyncio

from agents.llm_client import create_agent


async def test_agent_simple():
    """Test the agent with a simple prompt (non-streaming)"""
    print("=" * 80)
    print("Testing LLM Agent - Simple Prompt (Non-Streaming)")
    print("=" * 80)
    
    try:
        print("\n1. Creating agent...")
        agent = create_agent()
        print("   ✓ Agent created successfully")
        
        print("\n2. Running agent with prompt: 'Show me sales by region'")
        result = await agent.run("Show me sales by region")
        
        print("\n3. Agent Response:")
        print("-" * 80)
        print(result.output)
        print("-" * 80)
        
        print("\n4. Usage Information:")
        print(result.usage())
        
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True


async def main():
    """Main function to run all tests"""
    print("\n" + "=" * 80)
    print("LLM Agent Debugging Script")
    print("=" * 80)
    print("\nThis script tests the LLM agent with various prompts.")
    print("Make sure AWS credentials are configured (AWS_REGION, AWS_ACCESS_KEY_ID, etc.)")
    print("=" * 80)
    
    results = []
    
    # Test 1: Simple non-streaming
    results.append(await test_agent_simple())
    
    # Summary
    print("\n" + "=" * 80)
    print("Summary")
    print("=" * 80)
    passed = sum(results)
    total = len(results)
    print(f"Tests passed: {passed}/{total}")
    
    if passed == total:
        print("✓ All tests passed!")
        return 0
    else:
        print("✗ Some tests failed")
        return 1


if __name__ == "__main__":
    asyncio.run(main())
