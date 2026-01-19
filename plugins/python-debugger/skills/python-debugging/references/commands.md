# Command Reference

Complete reference for all Python Debugger commands.

## Session Commands

### start

Start a new debugging session.

```bash
python scripts/debugger.py start <script> [args...]
```

**Arguments:**
- `script` - Python script to debug (required)
- `args` - Arguments to pass to the script (optional)

**Example:**
```bash
python scripts/debugger.py start my_script.py --config prod.yaml
```

**Output:**
```json
{
  "status": "paused",
  "stop_reason": "line",
  "location": {"file": "my_script.py", "line": 1, "function": "<module>"}
}
```

### status

Check the status of active debugging sessions.

```bash
python scripts/debugger.py status [-s SCRIPT]
```

**Options:**
- `-s, --script` - Check status for a specific script

**Example:**
```bash
python scripts/debugger.py status
```

### quit

Terminate the debugging session.

```bash
python scripts/debugger.py quit
```

## Breakpoint Commands

### break

Set a breakpoint.

```bash
python scripts/debugger.py break -f FILE -l LINE [-c CONDITION]
python scripts/debugger.py break -e EXCEPTION
```

**Options:**
- `-f, --file` - File path for line breakpoint
- `-l, --line` - Line number
- `-c, --condition` - Conditional expression (breakpoint only triggers when true)
- `-e, --exception` - Exception type to break on (use `*` for all exceptions)

**Examples:**
```bash
# Line breakpoint
python scripts/debugger.py break -f script.py -l 45

# Conditional breakpoint
python scripts/debugger.py break -f script.py -l 45 -c "i > 100"

# Exception breakpoint
python scripts/debugger.py break -e KeyError
python scripts/debugger.py break -e "*"  # All exceptions
```

### delete

Delete a breakpoint.

```bash
python scripts/debugger.py delete -f FILE -l LINE
python scripts/debugger.py delete -n NUMBER
python scripts/debugger.py delete -e EXCEPTION
```

**Options:**
- `-f, --file` - File path
- `-l, --line` - Line number
- `-n, --number` - Breakpoint number
- `-e, --exception` - Exception type (use `*` to clear all exception breakpoints)

### breakpoints

List all active breakpoints.

```bash
python scripts/debugger.py breakpoints
```

**Output:**
```json
{
  "status": "ok",
  "breakpoints": [
    {"number": 1, "file": "script.py", "line": 45, "enabled": true, "condition": null}
  ],
  "exception_breakpoints": ["ValueError"]
}
```

## Execution Commands

### continue

Continue execution until the next breakpoint or end of script.

```bash
python scripts/debugger.py continue
```

### step

Step into the next line of code, entering function calls.

```bash
python scripts/debugger.py step
```

### next

Step over to the next line, executing function calls without entering them.

```bash
python scripts/debugger.py next
```

### finish

Run until the current function returns.

```bash
python scripts/debugger.py finish
```

## Inspection Commands

### locals

Get local variables in the current frame.

```bash
python scripts/debugger.py locals [-d DEPTH]
```

**Options:**
- `-d, --depth` - Inspection depth for nested objects (default: 2)

**Output:**
```json
{
  "status": "ok",
  "locals": {
    "x": {"type": "int", "value": "42"},
    "items": {"type": "list", "value": "<list with 5 items>"}
  }
}
```

### globals

Get global variables in the current frame.

```bash
python scripts/debugger.py globals [-d DEPTH]
```

**Options:**
- `-d, --depth` - Inspection depth for nested objects (default: 2)

### eval

Evaluate an expression in the current frame's context.

```bash
python scripts/debugger.py eval "EXPRESSION"
```

**Examples:**
```bash
python scripts/debugger.py eval "len(items)"
python scripts/debugger.py eval "data['key']"
python scripts/debugger.py eval "[x*2 for x in range(5)]"
```

**Notes:**
- Has a 5-second timeout to prevent hangs
- Can execute statements (not just expressions)
- Works in the context of the currently selected stack frame

### inspect

Deep inspect a variable or expression.

```bash
python scripts/debugger.py inspect EXPRESSION [-d DEPTH]
```

**Options:**
- `-d, --depth` - Inspection depth (default: 4)

**Example:**
```bash
python scripts/debugger.py inspect my_dataframe
```

**Output includes:**
- Type information
- For DataFrames: shape, columns, dtypes, sample values
- For arrays: shape, dtype, statistics
- For objects: attributes and methods
- For collections: contents (truncated if large)

## Stack Navigation Commands

### stack

Display the current call stack.

```bash
python scripts/debugger.py stack
```

**Output:**
```json
{
  "status": "ok",
  "stack": [
    {"index": 0, "file": "script.py", "line": 45, "function": "inner", "current": true},
    {"index": 1, "file": "script.py", "line": 30, "function": "outer", "current": false},
    {"index": 2, "file": "script.py", "line": 10, "function": "<module>", "current": false}
  ],
  "current_index": 0
}
```

### up

Move up the call stack (toward the caller).

```bash
python scripts/debugger.py up
```

After moving up, `locals`, `globals`, and `eval` operate in that frame's context.

### down

Move down the call stack (toward where execution stopped).

```bash
python scripts/debugger.py down
```

## Output Format

All commands return JSON with a consistent structure:

**Success:**
```json
{
  "status": "ok",
  ...
}
```

**Paused at breakpoint:**
```json
{
  "status": "paused",
  "stop_reason": "line|return|exception",
  "location": {...},
  "variables": {...}
}
```

**Error:**
```json
{
  "error": "Error message",
  "traceback": "..."
}
```

## Value Truncation

To prevent overwhelming output:
- String values: truncated to 1000 characters
- Collections: limited to 50 items
- Stack depth: limited to 50 frames
- Nested objects: configurable depth (default 2-4)

Truncated values are indicated in the output.
