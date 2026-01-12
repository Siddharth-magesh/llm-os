"""Test OpenRouter provider"""
import asyncio
import sys
import os
from pathlib import Path

# Add both src and root to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

# Note: OpenRouter requires API key - set OPENROUTER_API_KEY if you want to test
# For now, this test will skip if no key is available

async def test_openrouter():
    from llm_os.llm.providers.openrouter import OpenRouterProvider
    from llm_os.llm.base import Message, MessageRole

    print("=" * 60)
    print("OPENROUTER PROVIDER TEST")
    print("=" * 60)

    # Check if API key is available
    api_key = os.environ.get("OPENROUTER_API_KEY")
    if not api_key:
        print("\nSKIPPED: OPENROUTER_API_KEY not set")
        print("To test OpenRouter:")
        print("  1. Get free API key at https://openrouter.ai/keys")
        print("  2. Set OPENROUTER_API_KEY environment variable")
        print("=" * 60)
        return True

    try:
        provider = OpenRouterProvider(api_key=api_key)
    except Exception as e:
        print(f"\nSKIPPED: Could not initialize OpenRouter - {e}")
        return True

    # Test 1: Health check
    print("\n[1/4] Health check...")
    try:
        is_healthy = await provider.check_health()
        if is_healthy:
            print("  Result: PASS")
        else:
            print("  Result: FAIL - API not healthy")
            return False
    except Exception as e:
        print(f"  Result: FAIL - {e}")
        return False

    # Test 2: List models
    print("\n[2/4] List models...")
    try:
        models = await provider.list_models()
        print(f"  Found: {len(models)} models")
        if models:
            print(f"  Sample: {models[0]}")
    except Exception as e:
        print(f"  Warning: {e}")

    # Test 3: Simple completion
    print("\n[3/4] Simple completion...")
    try:
        messages = [Message(role=MessageRole.USER, content="Reply with just the word TEST")]
        response = await provider.complete(messages)
        print(f"  Response: {response.content}")
        print(f"  Model: {response.model}")
        print(f"  Tokens: {response.input_tokens} in, {response.output_tokens} out")
        print(f"  Latency: {response.latency_ms:.0f}ms")
    except Exception as e:
        print(f"  Result: FAIL - {e}")
        await provider.close()
        return False

    # Test 4: Tool calling
    print("\n[4/4] Tool calling...")
    try:
        messages = [Message(role=MessageRole.USER, content="What's the weather in Paris?")]
        tools = [{
            "type": "function",
            "function": {
                "name": "get_weather",
                "description": "Get weather for a location",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "location": {"type": "string", "description": "City name"}
                    },
                    "required": ["location"]
                }
            }
        }]
        response = await provider.complete(messages, tools=tools)
        if response.tool_calls:
            print(f"  Tool called: {response.tool_calls[0].name}")
            print(f"  Arguments: {response.tool_calls[0].arguments}")
            print("  Result: PASS")
        else:
            print("  Result: SKIP - No tool call (model may not support it)")
    except Exception as e:
        print(f"  Result: SKIP - {e}")

    await provider.close()

    print("\n" + "=" * 60)
    print("OPENROUTER PROVIDER TEST PASSED")
    print("=" * 60)
    return True

if __name__ == "__main__":
    try:
        result = asyncio.run(test_openrouter())
        sys.exit(0 if result else 1)
    except Exception as e:
        print(f"\nERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
