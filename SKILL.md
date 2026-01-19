---
name: python-debugger
description: |
  Debug Python scripts with PyCharm-like capabilities. Use when users say:
  - "debug this script", "set a breakpoint", "step through the code"
  - "inspect variables", "what's the value of X", "show the call stack"
  - "why is this crashing", "trace the execution", "find this bug"
---

# Python Debugger

Debug Python scripts with breakpoints, stepping, variable inspection, and stack navigation.

## Quick Reference

```bash
# Start debugging
python scripts/debugger.py start script.py [args...]

# Breakpoints
python scripts/debugger.py break -f script.py -l 45           # Line breakpoint
python scripts/debugger.py break -f script.py -l 45 -c "x>10" # Conditional
python scripts/debugger.py break -e ValueError               # Exception breakpoint
python scripts/debugger.py breakpoints                        # List all

# Execution
python scripts/debugger.py continue   # Run until next breakpoint
python scripts/debugger.py step       # Step into
python scripts/debugger.py next       # Step over
python scripts/debugger.py finish     # Run until return

# Inspection
python scripts/debugger.py locals     # Local variables
python scripts/debugger.py globals    # Global variables
python scripts/debugger.py eval "expression"
python scripts/debugger.py inspect variable_name

# Stack
python scripts/debugger.py stack      # View call stack
python scripts/debugger.py up         # Move up stack
python scripts/debugger.py down       # Move down stack

# Session
python scripts/debugger.py status     # Check status
python scripts/debugger.py quit       # End session
```

## Workflow

### Starting a Debug Session

```bash
python scripts/debugger.py start buggy_script.py
```

The debugger starts and pauses at the first line. You'll receive JSON output showing:
- Current location (file, line, function)
- Local variables at that point
- Stop reason

### Setting Breakpoints

Set breakpoints at specific lines:
```bash
python scripts/debugger.py break -f /path/to/script.py -l 45
```

With conditions (only stops when condition is true):
```bash
python scripts/debugger.py break -f script.py -l 45 -c "count > 100"
```

Break on exceptions:
```bash
python scripts/debugger.py break -e ValueError       # Specific exception
python scripts/debugger.py break -e "*"              # All exceptions
```

### Stepping Through Code

| Command | Action |
|---------|--------|
| `continue` | Run until next breakpoint |
| `step` | Step into function calls |
| `next` | Step over function calls (stay in current function) |
| `finish` | Run until current function returns |

### Inspecting State

**View all local variables:**
```bash
python scripts/debugger.py locals
```

**Evaluate any expression:**
```bash
python scripts/debugger.py eval "len(items)"
python scripts/debugger.py eval "user.name"
python scripts/debugger.py eval "[x for x in data if x > 10]"
```

**Deep inspect complex objects:**
```bash
python scripts/debugger.py inspect dataframe
python scripts/debugger.py inspect -d 5 nested_dict
```

### Navigating the Stack

View the call stack to see how you got here:
```bash
python scripts/debugger.py stack
```

Move up/down to inspect different frames:
```bash
python scripts/debugger.py up    # Move to caller
python scripts/debugger.py down  # Move back
```

When in a different frame, `locals` and `eval` work in that frame's context.

## JSON Output Format

All commands return JSON for easy parsing:

```json
{
  "status": "paused",
  "stop_reason": "line",
  "location": {
    "file": "/path/to/script.py",
    "line": 45,
    "function": "process_data",
    "code": "    result = calculate(item)"
  },
  "variables": {
    "locals": {
      "item": {"type": "dict", "value": "{'id': 1, 'name': 'test'}"},
      "result": {"type": "NoneType", "value": "None"}
    }
  }
}
```

## Common Debugging Patterns

### Finding a Bug

1. Start debugging: `start script.py`
2. Set breakpoint near suspected issue: `break -f script.py -l 100`
3. Continue to breakpoint: `continue`
4. Inspect variables: `locals` or `eval "suspicious_var"`
5. Step through: `step` or `next`
6. Repeat until bug found

### Debugging Exceptions

1. Set exception breakpoint: `break -e ValueError`
2. Start script: `start script.py`
3. Continue: `continue`
4. When exception occurs, inspect state: `locals`, `stack`
5. Use `up` to examine calling functions

### Understanding Control Flow

1. Set breakpoints at key decision points
2. Use `continue` to jump between them
3. Use `eval` to check condition values
4. Use `stack` to see the execution path

## Architecture Notes

The debugger uses a persistent subprocess architecture:
- The debugged script runs in a child process
- Commands communicate via Unix socket
- Session state stored in `~/.claude_debugger/`
- Allows state to persist across commands

This means you can:
- Run multiple commands without restarting
- Inspect state incrementally
- Keep breakpoints across continues

## Additional Resources

- [Command Reference](references/commands.md) - Complete command documentation
- [Troubleshooting](references/troubleshooting.md) - Common issues and solutions
- [Examples](references/examples.md) - Example debugging sessions
