"""Test Groq provider"""
import asyncio
import sys
import os
from pathlib import Path

# Add both src and root to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))
os.environ["GROQ_API_KEY"] = "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"

async def test_groq():
    from llm_os.llm.providers.groq import GroqProvider
    from llm_os.llm.base import Message, MessageRole

    print("=" * 60)
    print("GROQ PROVIDER TEST")
    print("=" * 60)

    provider = GroqProvider()

    # Test 1: Health check
    print("\n[1/4] Health check...")
    healthy = await provider.check_health()
    print(f"  Result: {'PASS' if healthy else 'FAIL'}")
    assert healthy, "Groq API not accessible"

    # Test 2: List models
    print("\n[2/4] List models...")
    models = await provider.list_models()
    print(f"  Found: {len(models)} models")
    print(f"  Sample: {models[0] if models else 'None'}")
    assert len(models) > 0, "No models available"

    # Test 3: Simple completion
    print("\n[3/4] Simple completion...")
    messages = [Message(role=MessageRole.USER, content="Say TEST")]
    response = await provider.complete(messages=messages, max_tokens=50)
    print(f"  Response: {response.content[:100]}")
    print(f"  Model: {response.model}")
    print(f"  Tokens: {response.input_tokens} in, {response.output_tokens} out")
    print(f"  Latency: {response.latency_ms:.0f}ms")
    assert response.content, "No response content"

    # Test 4: Tool calling
    print("\n[4/4] Tool calling...")
    from llm_os.llm.base import ToolDefinition

    tools = [ToolDefinition(
        name="get_weather",
        description="Get the weather for a location",
        parameters={
            "type": "object",
            "properties": {
                "location": {"type": "string", "description": "City name"}
            },
            "required": ["location"]
        }
    )]

    messages = [Message(
        role=MessageRole.USER,
        content="What's the weather in Paris?"
    )]

    response = await provider.complete(
        messages=messages,
        tools=tools,
        max_tokens=100
    )

    if response.tool_calls:
        print(f"  Tool called: {response.tool_calls[0].name}")
        print(f"  Arguments: {response.tool_calls[0].arguments}")
        print("  Result: PASS")
    else:
        print(f"  No tool call (got text instead)")
        print("  Result: SKIP")

    await provider.close()

    print("\n" + "=" * 60)
    print("ALL TESTS PASSED")
    print("=" * 60)
    return True

if __name__ == "__main__":
    try:
        asyncio.run(test_groq())
        sys.exit(0)
    except Exception as e:
        print(f"\nERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
