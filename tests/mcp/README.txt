OSSARTH MCP Server Testing
===========================

This folder contains tests for MCP (Model Context Protocol) servers.

Structure:
----------
custom_servers/     - Custom Python MCP servers for testing
test_internal_*.py  - Tests for internal (Python) MCP servers
test_external_*.py  - Tests for external (Node.js) MCP servers
run_tests.bat       - Run all MCP tests

Types of Servers:
-----------------
1. Internal Servers (Python):
   - Run in-process
   - Located in: src/llm_os/mcp/servers/
   - Examples: system.py, process.py, git.py

2. External Servers (Node.js/other):
   - Run as separate processes
   - Communicate via JSON-RPC over stdio
   - Official servers from @modelcontextprotocol npm packages

Testing Approach:
-----------------
1. Test internal servers: Direct Python import and call
2. Test external servers: Spawn process and use StdioMCPClient
3. Verify tools list, tool calls, and responses

Official Servers Available (no API key):
-----------------------------------------
- time: Time and timezone operations
- filesystem: File operations (read, write, list)
- memory: Knowledge graph storage
- sequential-thinking: Structured reasoning

Official Servers (require API keys):
-------------------------------------
- brave-search: Brave web search
- google-maps: Google Maps API
- github: GitHub API
- slack: Slack integration
