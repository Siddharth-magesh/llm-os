# LLM-OS Logging System

## Overview

LLM-OS includes a comprehensive logging system designed to track and analyze all aspects of system operation without creating massive log files. The system provides structured logging with automatic rotation, categorization, and analysis tools.

## Features

- **Multiple Log Categories**: User interactions, system health, tool executions, LLM calls, security events, and performance metrics
- **Automatic Log Rotation**: Files automatically rotate when they reach 10MB, keeping last 5 backups
- **Structured Logging**: JSON format for machine readability, human-readable format for console
- **Smart Storage**: Only stores summaries and key information, not full responses
- **Built-in Viewer**: Command-line tool for viewing and analyzing logs
- **Performance Tracking**: Built-in timers and decorators for performance monitoring

## Log Categories

### 1. User Logs (`user_interactions.log`)

Tracks user commands and interactions with the system.

**What is logged:**
- User input (full command)
- Response summary (truncated to 500 chars)
- Tools called during interaction
- Success/failure status
- Duration in milliseconds
- Error messages if failed

**Use cases:**
- Understanding user behavior
- Debugging failed commands
- Analyzing common usage patterns
- Tracking response times

### 2. System Logs (`system_health.log`)

Tracks system-level events and health.

**What is logged:**
- Component startup/shutdown events
- System errors and warnings
- Configuration changes
- Component status
- Resource availability

**Use cases:**
- System health monitoring
- Debugging initialization issues
- Tracking system stability
- Audit trail for system events

### 3. Tool Logs (`tool_executions.log`)

Tracks MCP tool executions.

**What is logged:**
- Tool name and server
- Parameters (truncated if large)
- Result summary (truncated to 500 chars)
- Success/failure status
- Duration in milliseconds
- Error messages if failed

**Use cases:**
- Understanding tool usage patterns
- Debugging tool failures
- Performance optimization
- Identifying frequently used tools

### 4. LLM Logs (`llm_calls.log`)

Tracks calls to LLM providers.

**What is logged:**
- Provider name (Groq, OpenAI, etc.)
- Model name
- Token usage (prompt, completion, total)
- Duration in milliseconds
- Success/failure status
- Streaming mode
- Error messages if failed

**Use cases:**
- Token usage tracking
- Cost estimation
- Performance monitoring
- Provider comparison
- Debugging API issues

### 5. Security Logs (`security.log`)

Tracks security-related events.

**What is logged:**
- Event type (permission check, access denied, etc.)
- Resource being accessed
- Action attempted
- Whether allowed or denied
- Reason for decision

**Use cases:**
- Security auditing
- Identifying unauthorized access attempts
- Debugging permission issues
- Compliance reporting

### 6. Performance Logs (`performance.log`)

Tracks performance metrics.

**What is logged:**
- Operation name
- Duration in milliseconds
- Memory usage (MB)
- CPU usage (%)
- Additional metrics

**Use cases:**
- Performance optimization
- Identifying bottlenecks
- Resource usage tracking
- Capacity planning

## Storage Management

### Automatic Rotation

Logs automatically rotate when they exceed 10MB:
- Current log: `user_interactions.log`
- Backup 1: `user_interactions.log.1`
- Backup 2: `user_interactions.log.2`
- ... up to 5 backups

Oldest backup is deleted when a new one is created.

### Storage Efficiency

To prevent massive log files:

1. **Response Truncation**: Full responses not stored, only 500-char summaries
2. **Parameter Truncation**: Large tool parameters truncated with note
3. **Selective Logging**: Only INFO and above to files, DEBUG only when enabled
4. **Structured Format**: JSON for efficient parsing and filtering
5. **Automatic Cleanup**: Old backups automatically deleted

**Typical storage usage:**
- Active development: ~5-10 MB/day across all logs
- Production use: ~20-50 MB/day across all logs
- With rotation: Max ~60 MB per category (10MB × 6 files)
- Total max: ~360 MB across all categories

## Using the Logging System

### Initialization

The logging system is automatically initialized when LLM-OS starts:

```python
from llm_os.utils.logging import setup_logging

# Initialize logging (done automatically in cli.py)
setup_logging()  # Uses default directory: ~/.llm_os/logs
```

### Getting Loggers

```python
from llm_os.utils.logging import get_logger

# Get specific category logger
user_logger = get_logger("user")
system_logger = get_logger("system")
tool_logger = get_logger("tool")
llm_logger = get_logger("llm")
security_logger = get_logger("security")
performance_logger = get_logger("performance")
```

### Logging User Interactions

```python
import time
from llm_os.utils.logging import get_logger

user_logger = get_logger("user")

# Log a user interaction
start_time = time.time()

# ... process user message ...

duration_ms = (time.time() - start_time) * 1000

user_logger.log_interaction(
    user_input="list files in current directory",
    response="Here are the files: file1.txt, file2.txt, ...",  # Will be truncated
    tool_calls=["list_directory", "get_file_info"],
    success=True,
    duration_ms=duration_ms,
)

# Log a failed interaction
user_logger.log_interaction(
    user_input="read secret.txt",
    response="",
    success=False,
    error="Permission denied",
    duration_ms=123.4,
)
```

### Logging System Events

```python
from llm_os.utils.logging import get_logger

system_logger = get_logger("system")

# Log startup
system_logger.log_startup(
    "llm_router",
    details={"default_provider": "groq", "model": "llama3-70b"}
)

# Log shutdown
system_logger.log_shutdown("llm_router")

# Log error
system_logger.log_error(
    "mcp_orchestrator",
    "Failed to start MCP server",
    details={"server": "git", "error": "Connection refused"}
)

# Log warning
system_logger.log_warning(
    "llm_router",
    "Provider switched due to rate limit",
    details={"from": "groq", "to": "ollama"}
)
```

### Logging Tool Executions

```python
import time
from llm_os.utils.logging import get_logger

tool_logger = get_logger("tool")

start_time = time.time()

# Execute tool...
result = {"files": ["file1.txt", "file2.txt"]}

duration_ms = (time.time() - start_time) * 1000

tool_logger.log_execution(
    tool_name="list_directory",
    tool_server="filesystem",
    parameters={"path": "/home/user", "recursive": False},
    result=result,  # Will be summarized if large
    success=True,
    duration_ms=duration_ms,
)
```

### Logging LLM Calls

```python
import time
from llm_os.utils.logging import get_logger

llm_logger = get_logger("llm")

start_time = time.time()

# Make LLM call...

duration_ms = (time.time() - start_time) * 1000

llm_logger.log_call(
    provider="groq",
    model="llama3-70b-8192",
    prompt_tokens=150,
    completion_tokens=80,
    duration_ms=duration_ms,
    success=True,
    streaming=False,
)
```

### Logging Security Events

```python
from llm_os.utils.logging import get_logger

security_logger = get_logger("security")

security_logger.log_event(
    event_type="permission_check",
    resource="/etc/passwd",
    action="read",
    allowed=False,
    reason="Outside allowed directories",
)

security_logger.log_event(
    event_type="file_access",
    resource="/home/user/document.txt",
    action="read",
    allowed=True,
    reason="Within user directory",
)
```

### Performance Monitoring

```python
from llm_os.utils.logging import get_logger, PerformanceTimer

performance_logger = get_logger("performance")

# Using context manager (automatic timing)
with PerformanceTimer(performance_logger, "process_message"):
    # ... operation to time ...
    pass

# Manual logging
performance_logger.log_metric(
    operation="initialize_router",
    duration_ms=1234.5,
    memory_mb=45.2,
    cpu_percent=12.5,
    details={"providers": 3},
)
```

### Using Decorators

For automatic logging, use the provided decorators:

```python
from llm_os.utils.logging_integration import (
    log_user_interaction,
    log_llm_call,
    log_tool_execution,
    log_performance,
)

# Automatically log user interactions
@log_user_interaction
async def process_message(self, user_input: str) -> str:
    # ... implementation ...
    return response

# Automatically log LLM calls
@log_llm_call
async def complete(self, messages: list) -> LLMResponse:
    # ... implementation ...
    return response

# Automatically log tool executions
@log_tool_execution
async def execute_tool(self, tool_name: str, parameters: dict):
    # ... implementation ...
    return result

# Automatically log performance
@log_performance("initialize_system")
async def initialize(self):
    # ... implementation ...
    pass
```

### Using Logging Helper

For simplified logging, use the LoggingHelper class:

```python
from llm_os.utils.logging_integration import get_logging_helper

logger = get_logging_helper()

# Log user message
logger.log_user_message(
    user_input="list files",
    response="Here are the files...",
    tool_calls=["list_directory"],
    success=True,
    duration_ms=123.4,
)

# Log LLM request
logger.log_llm_request(
    provider="groq",
    model="llama3-70b",
    prompt_tokens=150,
    completion_tokens=80,
    duration_ms=1234.5,
)

# Log startup
logger.log_startup("core_system", {"version": "0.1.0"})
```

## Viewing Logs

### Command-Line Viewer

LLM-OS includes a built-in log viewer:

```bash
# View all logs
python -m llm_os.utils.log_viewer

# View specific category
python -m llm_os.utils.log_viewer --category user
python -m llm_os.utils.log_viewer --category llm

# Filter by level
python -m llm_os.utils.log_viewer --level ERROR

# Filter by time
python -m llm_os.utils.log_viewer --since "2024-01-12 10:00"
python -m llm_os.utils.log_viewer --since 30m  # Last 30 minutes
python -m llm_os.utils.log_viewer --since 2h   # Last 2 hours
python -m llm_os.utils.log_viewer --since 1d   # Last 1 day

# Search by keyword
python -m llm_os.utils.log_viewer --keyword "error"

# Show last N entries
python -m llm_os.utils.log_viewer --tail 50

# Combine filters
python -m llm_os.utils.log_viewer --category user --level ERROR --since 1h

# Disable colors
python -m llm_os.utils.log_viewer --no-color

# List available log files
python -m llm_os.utils.log_viewer --list
```

### Statistics

Generate statistics from logs:

```bash
# Overall statistics
python -m llm_os.utils.log_viewer --stats

# Statistics for specific category
python -m llm_os.utils.log_viewer --category llm --stats

# Statistics for time range
python -m llm_os.utils.log_viewer --stats --since "2024-01-12 00:00" --until "2024-01-12 23:59"
```

**Example output:**
```
=== Log Statistics ===

Overall:
  Total Entries: 1,234
  By Level: {'INFO': 1100, 'WARNING': 100, 'ERROR': 34}
  By Category: {'user': 450, 'llm': 450, 'tool': 234, 'system': 100}

User Interactions:
  Total: 450
  Success Rate: 98.2%
  Avg Duration: 234.5ms

LLM Calls:
  Total Calls: 450
  Total Tokens: 125,000
  Avg Tokens/Call: 278
  Avg Duration: 1,234.5ms
  By Provider: {'groq': 400, 'ollama': 50}

Tool Executions:
  Total: 234
  Success Rate: 99.1%
  Most Used Tools:
    - list_directory: 89
    - read_file: 67
    - write_file: 34
    - get_file_info: 28
    - search_files: 16
```

### Manual Viewing

Log files are stored in JSON format (one entry per line) and can be viewed manually:

```bash
# View raw logs
cat ~/.llm_os/logs/user_interactions.log

# Pretty print with jq
cat ~/.llm_os/logs/user_interactions.log | jq '.'

# Search for errors
grep '"level":"ERROR"' ~/.llm_os/logs/*.log

# Count entries by category
grep -h '"category"' ~/.llm_os/logs/*.log | cut -d'"' -f4 | sort | uniq -c
```

## Integration Guide

### Adding Logging to New Components

1. **Import the logger:**
```python
from llm_os.utils.logging import get_logger
```

2. **Get the appropriate logger:**
```python
system_logger = get_logger("system")
```

3. **Add logging calls:**
```python
async def initialize(self):
    system_logger.log_startup("my_component", {"version": "1.0"})
    try:
        # ... initialization code ...
        pass
    except Exception as e:
        system_logger.log_error("my_component", str(e))
        raise
```

### Integration Checklist

For each major component, consider adding:

- [ ] **Startup logging**: When component initializes
- [ ] **Shutdown logging**: When component shuts down
- [ ] **Error logging**: When errors occur
- [ ] **Warning logging**: For recoverable issues
- [ ] **Operation logging**: For key operations
- [ ] **Performance logging**: For slow operations

### Example: Full Integration

```python
import time
from llm_os.utils.logging import get_logger, PerformanceTimer

class MyComponent:
    def __init__(self):
        self.system_logger = get_logger("system")
        self.performance_logger = get_logger("performance")

    async def initialize(self):
        """Initialize component."""
        self.system_logger.log_startup(
            "my_component",
            {"config": "default"}
        )

        try:
            with PerformanceTimer(self.performance_logger, "initialize_my_component"):
                # ... initialization code ...
                pass
        except Exception as e:
            self.system_logger.log_error(
                "my_component",
                f"Initialization failed: {e}"
            )
            raise

    async def process(self, data):
        """Process data."""
        start_time = time.time()

        try:
            # ... processing code ...
            result = "success"

            duration_ms = (time.time() - start_time) * 1000
            if duration_ms > 1000:  # Slow operation
                self.performance_logger.log_metric(
                    "process_data",
                    duration_ms,
                    details={"data_size": len(data)}
                )

            return result

        except Exception as e:
            self.system_logger.log_error(
                "my_component",
                f"Processing failed: {e}",
                details={"data": str(data)[:100]}
            )
            raise

    async def shutdown(self):
        """Shutdown component."""
        self.system_logger.log_shutdown("my_component")
```

## Best Practices

### DO:
- ✅ Log important events (startup, shutdown, errors)
- ✅ Log user interactions for debugging
- ✅ Log tool executions for analysis
- ✅ Log LLM calls for token tracking
- ✅ Log security events for auditing
- ✅ Use appropriate log levels (INFO, WARNING, ERROR)
- ✅ Include context in log messages
- ✅ Use structured logging (JSON format)
- ✅ Monitor log file sizes

### DON'T:
- ❌ Log full responses (use summaries)
- ❌ Log sensitive data (passwords, tokens)
- ❌ Log at DEBUG level in production
- ❌ Create custom log files (use categories)
- ❌ Duplicate logging (one log per event)
- ❌ Ignore log rotation settings
- ❌ Log excessively (creates noise)

### Performance Considerations

- Logging is asynchronous and minimal overhead
- JSON serialization is fast for small objects
- File I/O is buffered and efficient
- Rotation happens automatically
- Console logging only for WARNING and above

### Security Considerations

- Never log passwords, API keys, or tokens
- Truncate sensitive parameters
- Log file permissions are 600 (user-only read/write)
- Log directory permissions are 700 (user-only access)
- Sanitize user input before logging
- Be careful with error messages (may contain sensitive info)

## Troubleshooting

### Logs not appearing

1. Check logging is initialized:
```python
from llm_os.utils.logging import setup_logging
setup_logging()
```

2. Check log directory exists:
```bash
ls -la ~/.llm_os/logs
```

3. Check file permissions:
```bash
ls -la ~/.llm_os/logs/*.log
```

### Log files too large

1. Check rotation settings in `logging.py`:
```python
MAX_LOG_SIZE = 10 * 1024 * 1024  # 10 MB
BACKUP_COUNT = 5
```

2. Verify rotation is working:
```bash
ls -lh ~/.llm_os/logs/*.log*
```

3. Reduce logging verbosity

### Missing log entries

1. Check log level (DEBUG < INFO < WARNING < ERROR)
2. Verify logger is initialized
3. Check for exceptions during logging
4. Verify file write permissions

### Performance issues

1. Check log file sizes
2. Reduce log verbosity
3. Disable console logging
4. Increase rotation threshold

## Log File Locations

Default log directory: `~/.llm_os/logs/`

Log files:
- `~/.llm_os/logs/user_interactions.log`
- `~/.llm_os/logs/system_health.log`
- `~/.llm_os/logs/tool_executions.log`
- `~/.llm_os/logs/llm_calls.log`
- `~/.llm_os/logs/security.log`
- `~/.llm_os/logs/performance.log`

Backup files (after rotation):
- `~/.llm_os/logs/user_interactions.log.1`
- `~/.llm_os/logs/user_interactions.log.2`
- ... etc

## Summary

The LLM-OS logging system provides comprehensive tracking of all system operations while maintaining efficient storage through:

- **Automatic rotation** prevents unlimited growth
- **Smart truncation** stores only what's needed
- **Multiple categories** for organization
- **Built-in viewer** for easy analysis
- **Structured format** for machine processing
- **Performance tracking** for optimization

With proper use, the logging system helps debug issues, analyze usage, track performance, and maintain security without creating massive files or impacting performance.
