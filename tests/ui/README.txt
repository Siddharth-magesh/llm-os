OSSARTH UI Testing
==================

Quick Start:
1. Double-click "test-ui-standalone.bat" to launch UI with dummy backend
2. Try typing messages and see them echo back
3. Test commands: /help, /status, /clear

Files:
- test-ui-standalone.bat  : Launch UI with dummy backend (MAIN TEST)
- test_ui_standalone.py   : Python script for UI testing
- start-dummy-api.bat     : Optional HTTP API backend (port 8000)
- dummy_api.py            : HTTP API server script

Usage:
The dummy backend will echo your messages back with streaming.
No actual LLM or MCP servers needed for UI testing.
