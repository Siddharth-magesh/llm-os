"""
Test UI Standalone - Launch OSSARTH UI with dummy backend for testing
"""
import asyncio
import sys
from pathlib import Path

# Add src to path
root_path = Path(__file__).parent.parent
sys.path.insert(0, str(root_path / "src"))

from llm_os.ui.app import NLShellApp


async def dummy_backend(message: str) -> str:
    """Dummy backend that echoes the message."""
    await asyncio.sleep(0.5)  # Simulate processing
    return f"**Response:** {message}\n\nThis is a test response from the dummy backend."


async def dummy_stream_backend(message: str):
    """Dummy streaming backend that echoes with streaming."""
    response = f"**Streaming Response:**\n\nYou said: *{message}*\n\nThis is a test streaming response. "
    response += "Each word appears one at a time to simulate real LLM streaming behavior. "
    response += "The backend is working correctly!"

    words = response.split()
    for word in words:
        await asyncio.sleep(0.03)
        yield word + " "


if __name__ == "__main__":
    print("Starting OSSARTH UI with dummy backend...")
    print("Provider: Test Backend")
    print("Model: Echo v1.0")
    print("-" * 60)

    app = NLShellApp(
        message_handler=dummy_backend,
        stream_handler=dummy_stream_backend,
        provider="Test Backend",
        model="Echo v1.0",
    )
    app.run()
