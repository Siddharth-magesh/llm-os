"""Test dynamic configuration system"""
import asyncio
import sys
import os
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
os.environ["GROQ_API_KEY"] = "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"

async def test_config_loading():
    """Test that configuration loads from new structure"""
    print("=" * 60)
    print("DYNAMIC CONFIGURATION TEST")
    print("=" * 60)

    print("\n[1/5] Testing config module loading...")
    try:
        from config import Config, load_config, get_config, save_config
        print("  Result: PASS")
    except Exception as e:
        print(f"  Result: FAIL - {e}")
        return False

    print("\n[2/5] Testing config creation...")
    try:
        config = Config()
        assert config.default_provider in ["groq", "ollama"]
        assert config.groq.api_key != ""
        print(f"  Provider: {config.default_provider}")
        print(f"  Groq API Key: ***{config.groq.api_key[-8:]}")
        print("  Result: PASS")
    except Exception as e:
        print(f"  Result: FAIL - {e}")
        return False

    print("\n[3/5] Testing provider configs...")
    try:
        assert config.groq.default_model == "llama-3.3-70b-versatile"
        assert config.ollama.default_model == "qwen2.5:7b"
        assert config.ollama.base_url == "http://localhost:11434"
        print(f"  Groq model: {config.groq.default_model}")
        print(f"  Ollama model: {config.ollama.default_model}")
        print("  Result: PASS")
    except Exception as e:
        print(f"  Result: FAIL - {e}")
        return False

    print("\n[4/5] Testing config save/load...")
    try:
        # Save config
        test_config_path = Path.home() / ".llm-os" / "test_config.yaml"
        save_config(config, test_config_path)

        # Load config
        loaded_config = load_config(test_config_path)
        assert loaded_config.default_provider == config.default_provider

        # Cleanup
        test_config_path.unlink(missing_ok=True)
        print("  Result: PASS")
    except Exception as e:
        print(f"  Result: FAIL - {e}")
        return False

    print("\n[5/5] Testing config modification...")
    try:
        config.default_provider = "ollama"
        assert config.default_provider == "ollama"

        config.default_provider = "groq"
        assert config.default_provider == "groq"
        print("  Result: PASS")
    except Exception as e:
        print(f"  Result: FAIL - {e}")
        return False

    print("\n" + "=" * 60)
    print("DYNAMIC CONFIGURATION TEST PASSED")
    print("=" * 60)
    print("\nNote: To test in TUI, use:")
    print("  /config          - Show configuration")
    print("  /provider groq   - Switch to Groq")
    print("  /provider ollama - Switch to Ollama")
    print("  /model <name>    - Switch model")
    return True

if __name__ == "__main__":
    try:
        asyncio.run(test_config_loading())
        sys.exit(0)
    except Exception as e:
        print(f"\nERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
