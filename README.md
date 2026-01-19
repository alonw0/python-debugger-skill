# Python Debugger Skill for Claude Code

A PyCharm-like debugging experience for Python scripts within Claude Code. Set breakpoints, step through code, inspect variables, and navigate the call stack—all through a simple CLI interface.

## Features

- **Breakpoints**: Line breakpoints, conditional breakpoints, and exception breakpoints
- **Execution Control**: Continue, step into, step over, and run until return
- **Variable Inspection**: View locals, globals, evaluate expressions, deep inspect objects
- **Stack Navigation**: View call stack, move up/down frames, inspect variables in any frame
- **Session Management**: Persistent debugging sessions that survive across commands
- **JSON Output**: All commands return structured JSON for easy parsing

## Requirements

- Python 3.7+
- Unix-like operating system (macOS, Linux) - uses Unix sockets for IPC

## Installation

Clone or copy this skill to your Claude Code skills directory:

```bash
# Clone the repository
git clone <repository-url> python-debugger-skill

# Or copy to your skills directory
cp -r python-debugger-skill ~/.claude/skills/
```

## Quick Start

### 1. Start a Debug Session

```bash
python scripts/debugger.py start your_script.py [args...]
```

The debugger starts and pauses at the first line of your script.

### 2. Set Breakpoints

```bash
# Line breakpoint
python scripts/debugger.py break -f your_script.py -l 25

# Conditional breakpoint (stops only when condition is true)
python scripts/debugger.py break -f your_script.py -l 25 -c "count > 100"

# Exception breakpoint
python scripts/debugger.py break -e ValueError    # Specific exception
python scripts/debugger.py break -e "*"           # All exceptions
```

### 3. Control Execution

```bash
python scripts/debugger.py continue   # Run until next breakpoint
python scripts/debugger.py step       # Step into function calls
python scripts/debugger.py next       # Step over (stay in current function)
python scripts/debugger.py finish     # Run until current function returns
```

### 4. Inspect State

```bash
python scripts/debugger.py locals              # View local variables
python scripts/debugger.py globals             # View global variables
python scripts/debugger.py eval "len(items)"   # Evaluate any expression
python scripts/debugger.py inspect my_object   # Deep inspect an object
```

### 5. Navigate the Stack

```bash
python scripts/debugger.py stack   # View the call stack
python scripts/debugger.py up      # Move to caller's frame
python scripts/debugger.py down    # Move back toward current frame
```

### 6. End Session

```bash
python scripts/debugger.py quit
```

## Command Reference

| Command | Description | Options |
|---------|-------------|---------|
| `start <script> [args]` | Start debugging a script | Script path and optional arguments |
| `status` | Check debugger status | `-s/--script` for specific script |
| `break` | Set a breakpoint | `-f/--file`, `-l/--line`, `-c/--condition`, `-e/--exception` |
| `delete` | Delete a breakpoint | `-f/--file`, `-l/--line`, `-n/--number`, `-e/--exception` |
| `breakpoints` | List all breakpoints | — |
| `continue` | Continue execution | — |
| `step` | Step into next line | — |
| `next` | Step over to next line | — |
| `finish` | Run until function returns | — |
| `locals` | Get local variables | `-d/--depth` for inspection depth |
| `globals` | Get global variables | `-d/--depth` for inspection depth |
| `eval <expr>` | Evaluate an expression | Expression string |
| `inspect <expr>` | Deep inspect variable | `-d/--depth` for inspection depth |
| `stack` | Show call stack | — |
| `up` | Move up the call stack | — |
| `down` | Move down the call stack | — |
| `quit` | End debug session | — |

## Example Session

Here's a complete debugging session for a script with a bug:

```python
# buggy_script.py
def calculate_average(numbers):
    total = 0
    for num in numbers:
        total += num
    return total / len(numbers)  # Bug: crashes on empty list

data = []
result = calculate_average(data)
print(f"Average: {result}")
```

**Debugging session:**

```bash
$ python scripts/debugger.py start buggy_script.py
{"status": "paused", "location": {"line": 1, "function": "<module>"}, ...}

$ python scripts/debugger.py break -e ZeroDivisionError
{"status": "ok", "message": "Exception breakpoint set for ZeroDivisionError"}

$ python scripts/debugger.py continue
{"status": "paused", "stop_reason": "exception",
 "location": {"file": "buggy_script.py", "line": 5, "function": "calculate_average"},
 "exception": {"type": "ZeroDivisionError", "message": "division by zero"},
 "variables": {"locals": {"total": {"value": "0"}, "numbers": {"value": "[]"}}}}

# Found it! numbers is empty, causing division by zero

$ python scripts/debugger.py quit
{"status": "terminated"}
```

## JSON Output Format

All commands return JSON for easy integration:

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

## Architecture

The debugger uses a **persistent subprocess + Unix socket** architecture:

```
┌─────────────────────────────────────────────────────────────┐
│                     Claude Code CLI                          │
└─────────────────────────────────────────────────────────────┘
                              │
        ┌─────────────────────┼─────────────────────┐
        │                     │                     │
        ▼                     ▼                     ▼
   debugger.py           debugger.py          debugger.py
   start script.py       break -f ...         continue
        │                     │                     │
        │                     │                     │
        ▼                     ▼                     ▼
┌─────────────────────────────────────────────────────────────┐
│              Debugger Subprocess (persistent)                │
│  ┌─────────────────────────────────────────────────────┐    │
│  │  ClaudeDebugger (extends bdb.Bdb)                   │    │
│  │  - Manages breakpoints                              │    │
│  │  - Controls execution                               │    │
│  │  - Inspects frames                                  │    │
│  └─────────────────────────────────────────────────────┘    │
│                            │                                 │
│                            ▼                                 │
│  ┌─────────────────────────────────────────────────────┐    │
│  │  Unix Socket Server                                 │    │
│  │  - Receives commands                                │    │
│  │  - Sends JSON responses                             │    │
│  └─────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│              Session State (~/.claude_debugger/)             │
│  - Session metadata (PID, script path, socket path)         │
│  - Enables session recovery                                  │
└─────────────────────────────────────────────────────────────┘
```

**Why this architecture?**

- Python's `bdb` debugger state (frames, locals, breakpoints) cannot be serialized
- The debugger process must stay alive across commands
- Unix sockets provide reliable IPC for command/response patterns
- Session state files enable recovery and multi-session support

## File Structure

```
python-debugger-skill/
├── README.md                 # This file
├── SKILL.md                  # Claude Code skill definition
├── scripts/
│   ├── debugger.py           # Core debugger implementation
│   └── inspector.py          # Deep object inspection utilities
└── references/
    ├── commands.md           # Detailed command reference
    ├── examples.md           # Example debugging sessions
    └── troubleshooting.md    # Common issues and solutions
```

## Troubleshooting

### "Could not connect to debugger. Is it running?"

The debugger subprocess may have terminated. Check status and restart:

```bash
python scripts/debugger.py status
python scripts/debugger.py quit  # Clean up if needed
python scripts/debugger.py start script.py
```

### "Debugger already running for this script"

A previous session wasn't properly terminated:

```bash
python scripts/debugger.py quit
# If that fails:
rm -rf ~/.claude_debugger/
```

### Script doesn't stop at breakpoints

1. Verify the file path is correct (use absolute paths)
2. Ensure the line contains executable code (not a comment or blank line)
3. For conditional breakpoints, verify the condition can be true

### Expression evaluation times out

The `eval` command has a 5-second timeout. Simplify your expression or avoid operations on very large data structures.

## Limitations

- **Unix-only**: Requires Unix sockets (macOS, Linux)
- **Single script**: One debug session per script at a time
- **No remote debugging**: Debugger runs locally only
- **No threading support**: Limited support for multi-threaded scripts

## Contributing

Contributions are welcome! Areas for improvement:

- [ ] Windows support (named pipes instead of Unix sockets)
- [ ] Watch expressions
- [ ] Breakpoint persistence across sessions
- [ ] Integration with popular testing frameworks
- [ ] Source code display with context

## License

MIT License - See LICENSE file for details.
