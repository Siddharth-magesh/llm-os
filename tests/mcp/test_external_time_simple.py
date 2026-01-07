"""
Test External MCP Server: Time (Simplified)
Direct subprocess test to verify external server connectivity
"""
import asyncio
import subprocess
import sys
import json


async def test_time_server_direct():
    """Test Time MCP server directly via subprocess."""
    print("=" * 60)
    print("Testing External MCP Server: Time (Direct)")
    print("=" * 60)
    print()

    print("Starting npx @modelcontextprotocol/server-time...")
    print()

    try:
        # Use full path to npx
        npx_path = r"C:\Program Files\nodejs\npx.cmd"

        # Start the server process
        process = await asyncio.create_subprocess_exec(
            npx_path, "-y", "@modelcontextprotocol/server-time",
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )

        print("Server process started successfully!")
        print(f"PID: {process.pid}")
        print()

        # Send initialize request
        init_request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {
                    "name": "OSSARTH Test",
                    "version": "0.1.0"
                }
            }
        }

        # Give server time to start
        await asyncio.sleep(2)

        print("Sending initialize request...")
        request_json = json.dumps(init_request) + "\n"
        process.stdin.write(request_json.encode())
        await process.stdin.drain()

        # Read response (with timeout)
        try:
            # Check stderr first
            stderr_task = asyncio.create_task(process.stderr.read(1024))
            stdout_task = asyncio.create_task(process.stdout.readline())

            done, pending = await asyncio.wait(
                [stderr_task, stdout_task],
                timeout=10.0,
                return_when=asyncio.FIRST_COMPLETED
            )

            # Cancel pending tasks
            for task in pending:
                task.cancel()

            if stderr_task in done:
                stderr_data = stderr_task.result()
                if stderr_data:
                    print(f"Server stderr: {stderr_data.decode()}")

            if stdout_task in done:
                response_data = stdout_task.result()
                if response_data:
                    print(f"Raw response: {response_data.decode().strip()}")
                    try:
                        response = json.loads(response_data.decode())
                        print("Received response!")
                        print(f"Server: {response.get('result', {}).get('serverInfo', {})}")
                        print()
                        print("SUCCESS: External MCP server Time is working!")
                    except json.JSONDecodeError as e:
                        print(f"JSON decode error: {e}")
                else:
                    print("No response data")

        except asyncio.TimeoutError:
            print("Timeout waiting for response")

        # Terminate process
        print("\nTerminating server...")
        process.terminate()
        await process.wait()
        print("Server stopped")

    except FileNotFoundError:
        print("ERROR: npx not found!")
        print("Please install Node.js from https://nodejs.org/")
        return False
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False

    print("\n" + "=" * 60)
    print("Test completed")
    print("=" * 60)
    return True


if __name__ == "__main__":
    # Check npx availability
    import shutil
    if not shutil.which("npx"):
        print("ERROR: npx not found")
        print("Please install Node.js from https://nodejs.org/")
        sys.exit(1)

    result = asyncio.run(test_time_server_direct())
    sys.exit(0 if result else 1)
