---
name: python-debugging
description: |
  Debug Python scripts with PyCharm-like capabilities: breakpoints, stepping, variable inspection, and stack navigation. Use this skill when:
  - User wants to debug a Python script ("debug this script", "help me debug")
  - User wants to set breakpoints ("set a breakpoint at line X", "break on exception")
  - User wants to step through code ("step through the code", "trace execution")
  - User wants to inspect variables ("what's the value of X", "inspect this variable", "show locals")
  - User wants to understand a crash ("why is this crashing", "find this bug")
  - User wants to see the call stack ("show the call stack", "how did we get here")
  - User is troubleshooting Python code behavior
---

# Python Debugging

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

## Debugging Methodology

Debug systematically, not randomly. Follow these principles:

1. **Form a hypothesis first** - Before setting breakpoints, have a theory about what's wrong
2. **Reproduce consistently** - Ensure you can trigger the bug reliably
3. **Read error messages carefully** - They often point directly to the problem
4. **Binary search for bugs** - Narrow down by halving the search space
5. **Verify assumptions** - Use `eval` to check values are what you expect
6. **Change one thing at a time** - Isolate variables to identify root cause

## Decision Framework

| Situation | Approach |
|-----------|----------|
| Script crashes with exception | `break -e ExceptionType` → `continue` → inspect `locals` and `stack` |
| Wrong output, unknown cause | Binary search: breakpoint at midpoint, check state, narrow down |
| Loop produces wrong result | `break -l <line> -c "i == <problem_iteration>"` |
| Function returns wrong value | Breakpoint at return, inspect all locals before return |
| Variable has unexpected value | Trace backwards: where was it last assigned? |
| Intermittent bug | `break -e "*"` to catch any exception |

## Python Bug Patterns

| Bug Pattern | Symptoms | How to Debug |
|-------------|----------|--------------|
| `None` propagation | `AttributeError: 'NoneType'` | `eval "var"` at each step to find where it became None |
| Mutable default args | Function "remembers" values | `eval "func.__defaults__"` |
| Off-by-one errors | Missing first/last item | `break -c "i == 0 or i == len(items)-1"` |
| Scope issues | `UnboundLocalError` | Compare `locals` vs `globals` |
| Type coercion | Unexpected concatenation | `eval "type(var)"` |
| Dict key errors | `KeyError` | `eval "key in dict"` before access |
| Mutating while iterating | Missing items | `eval "len(collection)"` each iteration |

## The Debugging Process

```
1. REPRODUCE   →  Trigger the bug reliably
2. HYPOTHESIZE →  "I think X is wrong because Y"
3. INSTRUMENT  →  Set strategic breakpoint(s)
4. OBSERVE     →  Run to breakpoint, inspect state
5. ANALYZE     →  Does evidence support hypothesis?
   YES → Fix it    NO → New hypothesis, goto 2
6. VERIFY      →  Run again to confirm fix
```

## Common Workflows

### Debugging Exceptions

```bash
python scripts/debugger.py start script.py
python scripts/debugger.py break -e ValueError  # Or -e "*" for any
python scripts/debugger.py continue
# When exception occurs:
python scripts/debugger.py locals               # What values caused this?
python scripts/debugger.py stack                # How did we get here?
python scripts/debugger.py up                   # Check caller's context
```

### Debugging Wrong Output

```bash
python scripts/debugger.py start script.py
python scripts/debugger.py break -f script.py -l <output_line>
python scripts/debugger.py continue
python scripts/debugger.py eval "output_var"    # Already wrong?
# Binary search: set breakpoint at midpoint, repeat
```

### Debugging Loops

```bash
python scripts/debugger.py break -f script.py -l <loop_line> -c "i == 5"
python scripts/debugger.py continue
python scripts/debugger.py locals               # Check loop state
python scripts/debugger.py next                 # Step through iteration
```

## Anti-Patterns (Avoid These)

- **Random breakpoint placement** - Think first, then place strategically
- **Not reading error messages** - Python errors are descriptive
- **Changing code without understanding** - Understand before fixing
- **Assuming instead of verifying** - Use `eval` to check
- **Skipping reproduction** - Can't verify fix without consistent repro

## JSON Output Format

All commands return JSON:

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
      "item": {"type": "dict", "value": "{'id': 1}"},
      "result": {"type": "NoneType", "value": "None"}
    }
  }
}
```

## Additional Resources

- [Methodology & Best Practices](references/methodology.md) - Detailed debugging methodology
- [Command Reference](references/commands.md) - Complete command documentation
- [Troubleshooting](references/troubleshooting.md) - Common issues and solutions
- [Examples](references/examples.md) - Example debugging sessions
