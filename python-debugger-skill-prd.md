# Product Requirements Document: Python Debugger Skill for Claude Code

## Executive Summary

This PRD defines a skill that gives Claude Code powerful Python debugging capabilities similar to PyCharm's debugger. The skill enables Claude to set breakpoints, inspect variables, step through code, analyze stack traces, and diagnose issues interactively—all from the command line.

---

## 1. Problem Statement

### Current State
When debugging Python code, Claude Code can:
- Read error messages and tracebacks
- Add print statements manually
- Analyze code statically
- Suggest fixes based on error patterns

### Limitations
- No ability to pause execution at specific points
- Cannot inspect runtime variable state
- No step-through execution capability
- Cannot evaluate expressions in the context of a paused program
- Limited visibility into complex control flow during execution
- Cannot set conditional breakpoints or watchpoints

### Desired State
Claude Code should be able to debug Python like a senior developer using PyCharm:
- Set breakpoints (line, conditional, exception-based)
- Step through code (step in, step over, step out, continue)
- Inspect variables, objects, and data structures at runtime
- Evaluate arbitrary expressions in the current scope
- Navigate the call stack
- Watch specific variables for changes
- Debug multi-threaded applications
- Profile code performance during debugging

---

## 2. Goals & Objectives

### Primary Goals
1. **Interactive Debugging**: Enable Claude to run Python code in a debugger and interact with paused execution
2. **State Inspection**: Allow deep inspection of variables, objects, and memory at any breakpoint
3. **Intelligent Diagnosis**: Combine debugger output with Claude's reasoning to diagnose root causes
4. **Minimal Friction**: Work seamlessly with existing Python projects without configuration

### Success Metrics
- Claude can resolve 80%+ of runtime bugs that require state inspection
- Average debugging session completes in under 5 tool calls
- Zero false positives from debugger output parsing

### Non-Goals (v1)
- Remote debugging
- GUI-based debugging visualization
- Real-time debugging of production systems
- Debugging of compiled/optimized Python bytecode

---

## 3. User Stories & Use Cases

### User Stories

| ID | As a... | I want to... | So that... |
|----|---------|--------------|------------|
| US-1 | Developer | Ask Claude to "debug why my function returns None" | Claude can inspect the actual runtime values |
| US-2 | Developer | Say "set a breakpoint at line 45 and show me what x contains" | I can see runtime state without adding print statements |
| US-3 | Developer | Request "step through the loop and show me each iteration" | I can understand the control flow |
| US-4 | Developer | Ask "why does this crash with IndexError" | Claude can catch the exception and inspect the state |
| US-5 | Developer | Say "watch the `user` variable and tell me when it changes" | I can track state mutations |
| US-6 | Developer | Request "profile this function and find the bottleneck" | I can optimize performance |

### Detailed Use Cases

#### UC-1: Debugging a Function That Returns Unexpected Values
```
User: "My calculate_total() function returns 0 when it should return the sum. Debug it."

Claude's workflow:
1. Analyze the function to identify key variables
2. Set breakpoint at function entry
3. Run with test input
4. Step through, inspecting accumulator variable
5. Identify where the logic fails
6. Report findings with actual runtime values
```

#### UC-2: Debugging an Exception
```
User: "I get KeyError: 'user_id' somewhere in my code. Find where and why."

Claude's workflow:
1. Set exception breakpoint for KeyError
2. Run the code
3. When exception is caught, inspect the dictionary and available keys
4. Walk up the stack to find where the bad data originated
5. Report the root cause with evidence
```

#### UC-3: Understanding Complex Control Flow
```
User: "This recursive function seems to recurse forever. Debug it."

Claude's workflow:
1. Set breakpoint at function entry
2. Track recursion depth
3. Inspect base case conditions
4. Identify why termination condition fails
5. Show the exact call sequence that leads to infinite recursion
```

#### UC-4: Debugging Multi-threaded Code
```
User: "My threads seem to be deadlocking. Help me debug."

Claude's workflow:
1. Attach debugger to all threads
2. Identify locked resources
3. Show thread states and what each is waiting on
4. Identify the deadlock cycle
5. Suggest resolution
```

---

## 4. Feature Requirements

### 4.1 Core Debugging Features

#### 4.1.1 Breakpoint Management
| Feature | Priority | Description |
|---------|----------|-------------|
| Line breakpoints | P0 | Set breakpoint at specific file:line |
| Conditional breakpoints | P0 | Break only when condition is true |
| Exception breakpoints | P0 | Break when specific exception is raised |
| Function breakpoints | P1 | Break when function is called |
| Temporary breakpoints | P1 | Break once then auto-remove |
| Hit count breakpoints | P2 | Break after N hits |

#### 4.1.2 Execution Control
| Feature | Priority | Description |
|---------|----------|-------------|
| Continue | P0 | Resume execution until next breakpoint |
| Step over | P0 | Execute current line, don't enter functions |
| Step into | P0 | Step into function calls |
| Step out | P0 | Continue until current function returns |
| Run to cursor | P1 | Continue to specific line |
| Reverse debugging | P3 | Step backwards (if supported) |

#### 4.1.3 State Inspection
| Feature | Priority | Description |
|---------|----------|-------------|
| Variable inspection | P0 | Show all local/global variables |
| Object deep inspection | P0 | Expand nested objects/dicts/lists |
| Expression evaluation | P0 | Evaluate arbitrary Python expressions |
| Type information | P0 | Show variable types |
| Watch expressions | P1 | Monitor specific expressions |
| Memory address inspection | P2 | Show object memory locations |

#### 4.1.4 Call Stack Navigation
| Feature | Priority | Description |
|---------|----------|-------------|
| Stack trace display | P0 | Show full call stack |
| Frame navigation | P0 | Move up/down the call stack |
| Frame-local variables | P0 | Inspect variables in any frame |
| Source context | P0 | Show code around current line |

### 4.2 Advanced Features

#### 4.2.1 Exception Handling
| Feature | Priority | Description |
|---------|----------|-------------|
| Catch all exceptions | P0 | Break on any exception |
| Catch specific exceptions | P0 | Break on named exception types |
| Uncaught only | P1 | Break only on unhandled exceptions |
| Exception inspection | P0 | Inspect exception object and traceback |

#### 4.2.2 Data Visualization
| Feature | Priority | Description |
|---------|----------|-------------|
| DataFrame display | P1 | Format pandas DataFrames nicely |
| Array visualization | P1 | Show numpy array shapes and samples |
| Collection summaries | P1 | Summarize large lists/dicts |
| Truncation handling | P0 | Handle large data without overflow |

#### 4.2.3 Performance Analysis
| Feature | Priority | Description |
|---------|----------|-------------|
| Line profiling | P2 | Time per line execution |
| Memory profiling | P2 | Memory usage per line |
| Call count tracking | P2 | Number of function calls |

### 4.3 Integration Features

#### 4.3.1 Project Integration
| Feature | Priority | Description |
|---------|----------|-------------|
| Virtual environment detection | P0 | Use project's venv |
| Working directory handling | P0 | Run from correct directory |
| Module path handling | P0 | Handle imports correctly |
| pytest integration | P1 | Debug test functions |
| Django/Flask integration | P2 | Debug web frameworks |

---

## 5. Technical Architecture

### 5.1 Debugger Backend Options

#### Option A: pdb/pdb++ (Recommended for v1)
**Pros:**
- Built into Python standard library
- No additional dependencies
- Full programmatic control
- Text-based output perfect for CLI

**Cons:**
- Limited async support
- No built-in remote debugging

#### Option B: debugpy (VS Code debugger)
**Pros:**
- More powerful features
- Better async support
- JSON-based protocol

**Cons:**
- Requires DAP protocol implementation
- More complex setup

#### Option C: pudb
**Pros:**
- Rich TUI interface
- Good inspection capabilities

**Cons:**
- TUI doesn't work well for programmatic control

### 5.2 Recommended Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Claude Code                              │
│  ┌─────────────────────────────────────────────────────┐    │
│  │                   SKILL.md                           │    │
│  │  - Workflow guidance                                 │    │
│  │  - Command reference                                 │    │
│  │  - Output parsing patterns                           │    │
│  └─────────────────────────────────────────────────────┘    │
│                            │                                 │
│                            ▼                                 │
│  ┌─────────────────────────────────────────────────────┐    │
│  │              scripts/debugger.py                     │    │
│  │  - Programmatic pdb wrapper                          │    │
│  │  - JSON output formatting                            │    │
│  │  - Session management                                │    │
│  └─────────────────────────────────────────────────────┘    │
│                            │                                 │
│                            ▼                                 │
│  ┌─────────────────────────────────────────────────────┐    │
│  │                Python pdb/bdb                        │    │
│  │  - Actual debugging engine                           │    │
│  └─────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────┘
```

### 5.3 Debug Session Model

```python
# Conceptual session state
class DebugSession:
    script_path: str
    args: list[str]
    breakpoints: list[Breakpoint]
    current_frame: FrameInfo
    call_stack: list[FrameInfo]
    watches: list[str]
    state: Literal["running", "paused", "terminated"]
    
class Breakpoint:
    file: str
    line: int
    condition: str | None
    hit_count: int
    enabled: bool
    
class FrameInfo:
    file: str
    line: int
    function: str
    locals: dict
    globals: dict
    code_context: list[str]
```

### 5.4 Command Interface

The debugger script should accept commands via stdin/arguments and return structured JSON:

```bash
# Start a debug session
python debugger.py start script.py --args "arg1 arg2"

# Set breakpoint
python debugger.py break --file script.py --line 45 --condition "x > 10"

# Step commands
python debugger.py step [over|into|out|continue]

# Inspect state
python debugger.py inspect --expr "variable_name"
python debugger.py locals
python debugger.py stack

# Watch
python debugger.py watch --expr "len(items)"
```

### 5.5 Output Format

All commands return structured JSON for reliable parsing:

```json
{
  "status": "paused",
  "location": {
    "file": "/path/to/script.py",
    "line": 45,
    "function": "calculate_total",
    "code": "    total += item.price"
  },
  "locals": {
    "total": {"type": "int", "value": 0},
    "item": {"type": "Item", "value": "<Item name='Widget' price=29.99>"},
    "items": {"type": "list", "length": 5, "sample": ["<Item...>", "<Item...>"]}
  },
  "stack": [
    {"file": "main.py", "line": 10, "function": "main"},
    {"file": "script.py", "line": 45, "function": "calculate_total"}
  ],
  "watches": {
    "len(items)": {"type": "int", "value": 5}
  }
}
```

---

## 6. Skill Structure

### 6.1 Directory Layout

```
python-debugger/
├── SKILL.md                      # Main skill instructions
├── scripts/
│   ├── debugger.py               # Main debugger wrapper
│   ├── inspector.py              # Deep object inspection utilities
│   └── profiler.py               # Performance profiling utilities
└── references/
    ├── commands.md               # Full command reference
    ├── troubleshooting.md        # Common issues and solutions
    └── examples.md               # Example debugging sessions
```

### 6.2 SKILL.md Content (Draft)

```markdown
---
name: python-debugger
description: Interactive Python debugging with breakpoints, stepping, variable inspection, and stack navigation. Use when debugging Python runtime issues, inspecting variable state, stepping through code execution, catching exceptions, or diagnosing why code produces unexpected results. Triggers on requests like "debug this function", "set a breakpoint", "why does this return None", "step through this code", "inspect variable X", or "catch this exception".
---

# Python Debugger Skill

Debug Python code interactively with breakpoints, stepping, and state inspection.

## Quick Start

Debug a script:
```bash
python scripts/debugger.py start script.py
```

Set breakpoint and run:
```bash
python scripts/debugger.py break -f script.py -l 45
python scripts/debugger.py continue
```

## Debugging Workflow

1. **Identify the issue**: Determine what to debug (unexpected return, exception, etc.)
2. **Set strategic breakpoints**: Place breakpoints before the suspected problem
3. **Run to breakpoint**: Execute until paused
4. **Inspect state**: Check variables, evaluate expressions
5. **Step through**: Use step commands to trace execution
6. **Diagnose**: Identify the root cause from observed state

## Commands Reference

### Session Control
| Command | Description |
|---------|-------------|
| `start <file> [args]` | Start debugging a script |
| `attach <pid>` | Attach to running process |
| `quit` | End debug session |

### Breakpoints
| Command | Description |
|---------|-------------|
| `break -f <file> -l <line>` | Set line breakpoint |
| `break -f <file> -l <line> -c "<condition>"` | Conditional breakpoint |
| `break -e <ExceptionType>` | Exception breakpoint |
| `delete <breakpoint_id>` | Remove breakpoint |
| `disable/enable <breakpoint_id>` | Toggle breakpoint |

### Execution
| Command | Description |
|---------|-------------|
| `continue` / `c` | Continue to next breakpoint |
| `step` / `s` | Step into |
| `next` / `n` | Step over |
| `finish` / `f` | Step out (finish function) |
| `until <line>` | Run until line |

### Inspection
| Command | Description |
|---------|-------------|
| `locals` | Show local variables |
| `globals` | Show global variables |
| `inspect <expr>` | Deep inspect expression |
| `eval <expr>` | Evaluate expression |
| `stack` | Show call stack |
| `up` / `down` | Navigate stack frames |

### Watches
| Command | Description |
|---------|-------------|
| `watch <expr>` | Add watch expression |
| `unwatch <expr>` | Remove watch |
| `watches` | Show all watches with values |

## Output Interpretation

The debugger returns JSON. Key fields:

- `status`: "running", "paused", "terminated", "error"
- `location`: Current file, line, function
- `locals`: Variables in current scope
- `stack`: Full call stack
- `exception`: Exception info if stopped on exception

## Common Patterns

### Debug function return value
```bash
# Set breakpoint at return statement
debugger.py break -f module.py -l <return_line>
debugger.py start main.py
# When paused, inspect the return expression
debugger.py eval "result"
```

### Catch and inspect exception
```bash
debugger.py break -e KeyError
debugger.py start main.py
# When exception caught:
debugger.py eval "str(e)"  # Exception message
debugger.py locals          # See what variables exist
debugger.py eval "list(my_dict.keys())"  # See available keys
```

### Debug loop iteration
```bash
debugger.py break -f script.py -l <loop_body_line> -c "i == 5"
debugger.py start script.py
# Stops only on 5th iteration
```

## Handling Large Data

For DataFrames, large lists, or complex objects:
```bash
debugger.py inspect <var> --depth 2 --max-items 10
```

## See Also

- `references/commands.md` - Complete command reference
- `references/troubleshooting.md` - Common issues
- `references/examples.md` - Example sessions
```

---

## 7. Implementation Plan

### Phase 1: Core Debugger (Week 1-2)
- [ ] Implement `debugger.py` with pdb wrapper
- [ ] Basic commands: start, break, continue, step, next, finish
- [ ] JSON output formatting
- [ ] Variable inspection (locals, globals, inspect)
- [ ] Basic stack navigation

### Phase 2: Enhanced Inspection (Week 3)
- [ ] Deep object inspection with `inspector.py`
- [ ] DataFrame/numpy array formatting
- [ ] Watch expressions
- [ ] Conditional breakpoints
- [ ] Exception breakpoints

### Phase 3: Advanced Features (Week 4)
- [ ] pytest integration
- [ ] Virtual environment detection
- [ ] Performance profiling basics
- [ ] Multi-file project handling

### Phase 4: Polish & Documentation (Week 5)
- [ ] Comprehensive error handling
- [ ] Edge case testing
- [ ] Documentation completion
- [ ] Example debugging sessions

---

## 8. Script Specifications

### 8.1 debugger.py

```python
#!/usr/bin/env python3
"""
Python debugger wrapper for Claude Code.
Provides programmatic control over pdb with JSON output.

Usage:
    debugger.py start <script> [--args "arg1 arg2"]
    debugger.py break -f <file> -l <line> [-c <condition>]
    debugger.py break -e <exception_type>
    debugger.py continue | step | next | finish
    debugger.py locals | globals | stack
    debugger.py inspect <expression> [--depth N]
    debugger.py eval <expression>
    debugger.py watch <expression>
    debugger.py quit
"""

import sys
import json
import bdb
import linecache
from typing import Any, Optional
from dataclasses import dataclass, asdict
from pathlib import Path

# Core implementation follows...
# See full implementation in scripts/debugger.py
```

Key implementation requirements:

1. **Session persistence**: Use a state file to maintain debug session across invocations
2. **Safe evaluation**: Sandbox expression evaluation to prevent security issues
3. **Truncation**: Handle large objects gracefully (max 1000 chars per value)
4. **Type representation**: Show types for all values
5. **Error handling**: Graceful handling of all error conditions with helpful messages

### 8.2 inspector.py

```python
#!/usr/bin/env python3
"""
Deep object inspection utilities for the debugger.

Features:
- Recursive object inspection with depth control
- Special handling for common types (DataFrame, ndarray, etc.)
- Memory-safe inspection of large objects
- Type introspection and method listing
"""

def inspect_object(obj: Any, depth: int = 2, max_items: int = 20) -> dict:
    """Deep inspect an object, returning structured representation."""
    pass

def format_dataframe(df) -> dict:
    """Format pandas DataFrame for display."""
    pass

def format_ndarray(arr) -> dict:
    """Format numpy array for display."""
    pass
```

### 8.3 profiler.py

```python
#!/usr/bin/env python3
"""
Performance profiling utilities.

Features:
- Line-by-line timing
- Memory profiling
- Call count tracking
"""

def profile_function(func, *args, **kwargs) -> dict:
    """Profile a function call and return timing data."""
    pass
```

---

## 9. Testing Strategy

### 9.1 Unit Tests

Test each debugger command in isolation:
- Breakpoint setting/clearing
- Step commands
- Variable inspection
- Expression evaluation
- Stack navigation

### 9.2 Integration Tests

Test full debugging workflows:
- Debug simple script with breakpoint
- Debug function with exception
- Debug loop with conditional breakpoint
- Debug multi-file project

### 9.3 Edge Case Tests

- Very large variables (10MB+ strings/lists)
- Deeply nested objects (100+ levels)
- Circular references
- Multi-threaded code
- Async code
- C extension modules

### 9.4 Example Test Cases

```python
# Test: Basic breakpoint and variable inspection
def test_basic_debugging():
    """Debug a simple function and verify variable inspection."""
    script = """
def add(a, b):
    result = a + b
    return result

print(add(2, 3))
"""
    # Start debug session
    # Set breakpoint at line 3
    # Continue
    # Verify locals shows: a=2, b=3, result=5
    pass

# Test: Exception debugging
def test_exception_debugging():
    """Catch and inspect KeyError."""
    script = """
data = {"name": "Alice"}
print(data["age"])  # KeyError
"""
    # Set exception breakpoint for KeyError
    # Run
    # Verify stopped at line 2
    # Verify can inspect data.keys()
    pass
```

---

## 10. Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Security: Arbitrary code execution | Medium | High | Sandbox eval, restrict to project directory |
| Performance: Large object inspection crashes | Medium | Medium | Implement strict truncation limits |
| Compatibility: Different Python versions | Medium | Medium | Test on 3.8, 3.9, 3.10, 3.11, 3.12 |
| Reliability: Session state corruption | Low | High | Validate state file, implement recovery |
| Usability: Complex async debugging | High | Medium | Document limitations, defer to v2 |

---

## 11. Future Enhancements (v2+)

1. **Remote debugging**: Debug processes on remote machines
2. **Async support**: Full async/await debugging
3. **Memory debugging**: Track memory leaks and allocations
4. **Time-travel debugging**: Record and replay execution
5. **Visual call graphs**: Generate execution flow diagrams
6. **IDE integration**: Export debug sessions to VS Code/PyCharm
7. **Collaborative debugging**: Share debug sessions

---

## 12. Appendix

### A. Comparison with PyCharm Debugger

| Feature | PyCharm | This Skill |
|---------|---------|------------|
| Line breakpoints | ✅ | ✅ |
| Conditional breakpoints | ✅ | ✅ |
| Exception breakpoints | ✅ | ✅ |
| Step into/over/out | ✅ | ✅ |
| Variable inspection | ✅ | ✅ |
| Expression evaluation | ✅ | ✅ |
| Watch expressions | ✅ | ✅ |
| Stack navigation | ✅ | ✅ |
| Remote debugging | ✅ | ❌ (v2) |
| GUI | ✅ | ❌ (CLI) |
| Memory view | ✅ | ❌ (v2) |
| Thread debugging | ✅ | ⚠️ (Basic) |

### B. Command Quick Reference

```
Session:    start, attach, quit
Breakpoints: break, delete, disable, enable, list
Execution:  continue, step, next, finish, until
Inspection: locals, globals, inspect, eval, stack, up, down
Watches:    watch, unwatch, watches
```

### C. JSON Output Schema

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "properties": {
    "status": {
      "type": "string",
      "enum": ["running", "paused", "terminated", "error"]
    },
    "location": {
      "type": "object",
      "properties": {
        "file": {"type": "string"},
        "line": {"type": "integer"},
        "function": {"type": "string"},
        "code": {"type": "string"}
      }
    },
    "locals": {
      "type": "object",
      "additionalProperties": {
        "type": "object",
        "properties": {
          "type": {"type": "string"},
          "value": {"type": "string"}
        }
      }
    },
    "stack": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "file": {"type": "string"},
          "line": {"type": "integer"},
          "function": {"type": "string"}
        }
      }
    },
    "error": {
      "type": "object",
      "properties": {
        "type": {"type": "string"},
        "message": {"type": "string"}
      }
    }
  }
}
```
