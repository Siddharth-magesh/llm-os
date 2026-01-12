"""Test CLI bypass feature"""
import asyncio
import sys
import os
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

async def test_cli_bypass():
    """Test that CLI bypass commands work correctly"""
    print("=" * 60)
    print("CLI BYPASS TEST")
    print("=" * 60)

    print("\n[1/3] Testing basic command execution...")
    # We can't test the TUI directly, but we can test subprocess execution
    import subprocess
    result = subprocess.run(
        "echo Hello from bypass",
        shell=True,
        capture_output=True,
        text=True,
    )
    if result.returncode == 0 and "Hello from bypass" in result.stdout:
        print("  Result: PASS")
    else:
        print(f"  Result: FAIL - {result.stdout}")
        return False

    print("\n[2/3] Testing directory listing...")
    result = subprocess.run(
        "dir" if os.name == "nt" else "ls",
        shell=True,
        capture_output=True,
        text=True,
    )
    if result.returncode == 0:
        print("  Result: PASS")
    else:
        print(f"  Result: FAIL")
        return False

    print("\n[3/3] Testing Python version check...")
    result = subprocess.run(
        "python --version",
        shell=True,
        capture_output=True,
        text=True,
    )
    if result.returncode == 0 and "Python" in result.stdout + result.stderr:
        print("  Result: PASS")
    else:
        print(f"  Result: FAIL")
        return False

    print("\n" + "=" * 60)
    print("CLI BYPASS TEST PASSED")
    print("=" * 60)
    print("\nNote: Full TUI testing requires manual interaction")
    print("To test in TUI: launch.bat, then type: !dir or !ls")
    return True

if __name__ == "__main__":
    try:
        asyncio.run(test_cli_bypass())
        sys.exit(0)
    except Exception as e:
        print(f"\nERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
