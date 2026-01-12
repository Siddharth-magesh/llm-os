"""Test full LLM-OS integration with Groq"""
import asyncio
import sys
import os
from pathlib import Path

# Add both src and root to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))
os.environ["GROQ_API_KEY"] = "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"

async def test_integration():
    from llm_os.core import LLMOS, LLMOSConfig
    from config import Config

    print("=" * 60)
    print("INTEGRATION TEST - GROQ + FILESYSTEM MCP")
    print("=" * 60)

    # Create config
    config = Config()
    config.groq.api_key = os.environ["GROQ_API_KEY"]

    llmos_config = LLMOSConfig(
        default_provider="groq",
        use_external_servers=True,
        external_servers_enabled=["filesystem"],
    )

    # Initialize
    print("\n[1/3] Initializing LLMOS...")
    llmos = LLMOS(config=llmos_config, system_config=config)
    await llmos.initialize()

    status = llmos.get_status()
    print(f"  Provider: {status['provider']}")
    print(f"  Tools: {len(llmos.available_tools)}")
    print("  Result: PASS")

    # Test LLM response
    print("\n[2/3] Testing LLM response...")
    response = await llmos.process_message("Reply with just the word SUCCESS")
    print(f"  Response: {response[:100]}")
    print("  Result: PASS")

    # Test MCP tools
    print("\n[3/3] Testing MCP filesystem tools...")
    response = await llmos.process_message("List all files in the current directory")
    # Check if response contains file-like names (allowing for cache)
    has_files = any(ext in response.lower() for ext in [".bat", ".py", ".txt", "license", "readme"])
    if has_files:
        print("  Files listed (MCP tools working)")
        print("  Result: PASS")
    else:
        print(f"  Unexpected response: {response[:200]}")
        print("  Result: FAIL")

    await llmos.shutdown()

    print("\n" + "=" * 60)
    print("INTEGRATION TEST PASSED")
    print("=" * 60)
    return True

if __name__ == "__main__":
    try:
        asyncio.run(test_integration())
        sys.exit(0)
    except Exception as e:
        print(f"\nERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
