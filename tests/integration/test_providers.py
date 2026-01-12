"""Test provider configuration and selection"""
import asyncio
import sys
import os
from pathlib import Path

# Add both src and root to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))
os.environ["GROQ_API_KEY"] = "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"

async def test_providers():
    from llm_os.llm.router import LLMRouter, RouterConfig
    from llm_os.llm.base import Message, MessageRole

    print("=" * 60)
    print("PROVIDER CONFIGURATION TEST")
    print("=" * 60)

    # Test 1: Router initialization
    print("\n[1/3] Initialize router with Groq...")
    router_config = RouterConfig(
        default_provider="groq",
        groq_api_key=os.environ["GROQ_API_KEY"],
        fallback_chain=["ollama", "groq"]
    )
    router = LLMRouter(config=router_config)
    await router.initialize()

    print(f"  Available: {router.available_providers}")
    print("  Result: PASS")

    # Test 2: Check provider health
    print("\n[2/3] Check provider health...")
    health = await router.check_all_providers()
    for provider, status in health.items():
        print(f"  {provider}: {'OK' if status else 'UNAVAILABLE'}")
    print("  Result: PASS")

    # Test 3: Test completion with explicit provider
    print("\n[3/3] Test completion with Groq...")
    messages = [Message(role=MessageRole.USER, content="Say OK")]
    response = await router.complete(
        messages=messages,
        preferred_provider="groq",
        max_tokens=10
    )
    print(f"  Provider used: {response.provider}")
    print(f"  Model: {response.model}")
    print(f"  Response: {response.content}")
    print("  Result: PASS")

    await router.close()

    print("\n" + "=" * 60)
    print("PROVIDER TESTS PASSED")
    print("=" * 60)
    return True

if __name__ == "__main__":
    try:
        asyncio.run(test_providers())
        sys.exit(0)
    except Exception as e:
        print(f"\nERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
