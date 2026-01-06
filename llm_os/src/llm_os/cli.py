"""
LLM-OS Command Line Interface

Main entry point for the LLM-OS natural language shell.
"""

from __future__ import annotations

import argparse
import asyncio
import logging
import sys
from pathlib import Path
from typing import Any

from llm_os.config import load_config, Config
from llm_os.core import LLMOS, LLMOSConfig
from llm_os.ui import NLShellApp


# Configure logging
def setup_logging(
    level: str = "INFO",
    log_file: Path | None = None,
) -> None:
    """Configure logging for the application."""
    log_level = getattr(logging, level.upper(), logging.INFO)

    handlers: list[logging.Handler] = [logging.StreamHandler()]

    if log_file:
        log_file.parent.mkdir(parents=True, exist_ok=True)
        handlers.append(logging.FileHandler(log_file))

    logging.basicConfig(
        level=log_level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=handlers,
    )

    # Quiet down some noisy loggers
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)


def create_parser() -> argparse.ArgumentParser:
    """Create the argument parser."""
    parser = argparse.ArgumentParser(
        prog="llm-os",
        description="LLM-OS - Natural Language Operating System Shell",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  llm-os                    Start the interactive shell
  llm-os -c "list files"    Execute a single command
  llm-os --provider ollama  Use a specific LLM provider
  llm-os --model llama3.2   Use a specific model
  llm-os --no-ui            Run in CLI mode without TUI

For more information, visit: https://github.com/llm-os/llm-os
""",
    )

    # Command modes
    parser.add_argument(
        "-c", "--command",
        type=str,
        help="Execute a single command and exit",
    )

    parser.add_argument(
        "--interactive",
        action="store_true",
        help="Force interactive mode even with -c",
    )

    # LLM options
    parser.add_argument(
        "-p", "--provider",
        type=str,
        choices=["ollama", "anthropic", "openai"],
        help="LLM provider to use",
    )

    parser.add_argument(
        "-m", "--model",
        type=str,
        help="Specific model to use",
    )

    parser.add_argument(
        "--local-only",
        action="store_true",
        help="Only use local models (Ollama)",
    )

    # UI options
    parser.add_argument(
        "--no-ui",
        action="store_true",
        help="Run in CLI mode without the TUI",
    )

    parser.add_argument(
        "--no-stream",
        action="store_true",
        help="Disable response streaming",
    )

    # Configuration
    parser.add_argument(
        "--config",
        type=Path,
        help="Path to configuration file",
    )

    # Debugging
    parser.add_argument(
        "-v", "--verbose",
        action="count",
        default=0,
        help="Increase verbosity (-v for INFO, -vv for DEBUG)",
    )

    parser.add_argument(
        "--log-file",
        type=Path,
        help="Write logs to file",
    )

    # Version
    parser.add_argument(
        "--version",
        action="version",
        version="%(prog)s 0.1.0",
    )

    return parser


async def run_single_command(
    llmos: LLMOS,
    command: str,
    stream: bool = True,
) -> None:
    """Run a single command and print the result."""
    if stream:
        async for chunk in llmos.stream_message(command):
            print(chunk, end="", flush=True)
        print()  # Final newline
    else:
        response = await llmos.process_message(command)
        print(response)


async def run_cli_loop(llmos: LLMOS) -> None:
    """Run the CLI interactive loop (without TUI)."""
    print("LLM-OS - Natural Language Shell")
    print("Type 'exit' or 'quit' to exit, 'help' for help")
    print()

    while True:
        try:
            user_input = input("❯ ").strip()

            if not user_input:
                continue

            if user_input.lower() in ("exit", "quit", "/exit", "/quit"):
                print("Goodbye!")
                break

            if user_input.lower() in ("help", "/help"):
                print_cli_help()
                continue

            if user_input.lower() in ("status", "/status"):
                status = llmos.get_status()
                print(f"Provider: {status.get('provider', 'N/A')}")
                print(f"Model: {status.get('model', 'N/A')}")
                continue

            if user_input.lower() in ("clear", "/clear"):
                llmos.clear_context()
                print("Context cleared.")
                continue

            # Process message
            response = await llmos.process_message(user_input)
            print()
            print(response)
            print()

        except KeyboardInterrupt:
            print("\nUse 'exit' to quit")

        except EOFError:
            print("\nGoodbye!")
            break

        except Exception as e:
            print(f"Error: {e}")


def print_cli_help() -> None:
    """Print CLI help."""
    print("""
Commands:
  help, /help      Show this help
  exit, /exit      Exit the shell
  quit, /quit      Exit the shell
  status, /status  Show system status
  clear, /clear    Clear conversation context

Just type naturally to interact with your system!

Examples:
  "list files in the current directory"
  "show system information"
  "open firefox"
  "create a folder called projects"
""")


def run_tui(
    llmos: LLMOS,
    config: Config,
) -> None:
    """Run the TUI application."""
    async def message_handler(message: str) -> str:
        """Handle user messages."""
        return await llmos.process_message(message)

    async def confirmation_handler(title: str, message: str) -> bool:
        """Handle confirmations."""
        # In TUI mode, this is handled by the app
        return True

    # Create and configure app
    app = NLShellApp(
        message_handler=message_handler,
        confirmation_handler=confirmation_handler,
    )

    # Set up tool callback
    async def tool_callback(name: str, status: str, success: bool = True) -> None:
        if status == "starting":
            app.show_tool_progress(name)
        else:
            app.hide_tool_progress(success)

    llmos.set_tool_callback(tool_callback)

    # Update status when initialized
    async def update_status() -> None:
        await asyncio.sleep(1)  # Wait for initialization
        status = llmos.get_status()
        app.update_status(
            provider=status.get("provider", "Unknown"),
            model=status.get("model", ""),
            tool_count=len(llmos.available_tools),
        )

    # Initialize and run
    async def init_and_run() -> None:
        await llmos.initialize()
        await update_status()

    # Run the app with proper initialization
    app.run()


async def async_main(args: argparse.Namespace) -> int:
    """Async main function."""
    # Load configuration
    config = load_config(args.config)

    # Apply CLI overrides
    if args.provider:
        config.default_provider = args.provider

    if args.local_only:
        config.anthropic.enabled = False
        config.openai.enabled = False
        config.default_provider = "ollama"

    # Create LLM-OS config
    llmos_config = LLMOSConfig(
        default_provider=config.default_provider,
        default_model=args.model,
        stream_responses=not args.no_stream,
    )

    # Create LLM-OS instance
    llmos = LLMOS(config=llmos_config, system_config=config)

    try:
        # Single command mode
        if args.command and not args.interactive:
            await llmos.initialize()
            await run_single_command(llmos, args.command, not args.no_stream)
            return 0

        # Interactive mode
        if args.no_ui:
            await llmos.initialize()
            await run_cli_loop(llmos)
        else:
            # TUI mode - initialization happens inside
            run_tui(llmos, config)

        return 0

    except KeyboardInterrupt:
        print("\nInterrupted")
        return 130

    except Exception as e:
        logging.error(f"Fatal error: {e}", exc_info=True)
        print(f"Error: {e}", file=sys.stderr)
        return 1

    finally:
        await llmos.shutdown()


def main() -> int:
    """Main entry point."""
    parser = create_parser()
    args = parser.parse_args()

    # Setup logging
    log_levels = {0: "WARNING", 1: "INFO", 2: "DEBUG"}
    log_level = log_levels.get(args.verbose, "DEBUG")
    setup_logging(level=log_level, log_file=args.log_file)

    # Run async main
    return asyncio.run(async_main(args))


if __name__ == "__main__":
    sys.exit(main())
