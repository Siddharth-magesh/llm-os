"""
MCP Server Test Runner
Run all MCP server tests
"""
import subprocess
import sys
from pathlib import Path


def run_test(test_name, test_file):
    """Run a test and return result."""
    print(f"\n{'='*60}")
    print(f"TEST: {test_name}")
    print(f"{'='*60}")

    try:
        result = subprocess.run(
            [sys.executable, test_file],
            cwd=Path(__file__).parent,
            capture_output=True,
            text=True,
            timeout=30
        )

        passed = result.returncode == 0
        if passed:
            print("[PASSED]")
        else:
            print("[FAILED]")
            print(result.stderr[:500])

        return passed

    except subprocess.TimeoutExpired:
        print("[TIMEOUT]")
        return False
    except Exception as e:
        print(f"[ERROR] {e}")
        return False


def main():
    print("="*60)
    print("MCP SERVER TEST SUITE")
    print("="*60)

    tests = [
        ("Internal Servers", "tests/test_internal_servers.py"),
        ("Calculator Server", "tests/test_calculator.py"),
    ]

    # Check for Node.js
    node_check = subprocess.run(
        ["node", "--version"],
        capture_output=True,
        text=True
    )

    if node_check.returncode == 0:
        print(f"\n[OK] Node.js found: {node_check.stdout.strip()}")
        tests.extend([
            ("Memory Server", "tests/test_memory_server.py"),
            ("Sequential Thinking", "tests/test_sequential_thinking.py"),
            ("Combined Servers", "tests/test_combined.py"),
        ])
    else:
        print("\n[SKIP] Node.js not found - external server tests skipped")

    # Run tests
    results = []
    for name, file in tests:
        results.append((name, run_test(name, file)))

    # Summary
    print(f"\n{'='*60}")
    print("TEST SUMMARY")
    print(f"{'='*60}\n")

    passed = sum(1 for _, r in results if r)
    total = len(results)

    for name, result in results:
        status = "PASSED" if result else "FAILED"
        print(f"[{'PASS' if result else 'FAIL'}] {name}: {status}")

    print(f"\n{'='*60}")
    print(f"TOTAL: {passed}/{total} tests passed")
    print(f"{'='*60}\n")

    return 0 if passed == total else 1


if __name__ == "__main__":
    sys.exit(main())
