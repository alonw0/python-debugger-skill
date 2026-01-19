# Python Debugger Plugin Marketplace

A Claude Code plugin marketplace containing the Python Debugger plugin - PyCharm-like debugging for Python scripts.

## Why Use This Skill?

### The Problem

When Claude Code encounters a bug in Python code, it typically resorts to:
- Adding print statements and re-running
- Reading code and guessing what's wrong
- Making changes based on assumptions without verifying them

This is inefficient. Real developers don't debug this way—they use debuggers.

### The Solution

This skill gives Claude Code the same debugging capabilities that developers use in PyCharm or VS Code:

- **Set breakpoints** at specific lines or on exceptions
- **Step through code** line by line to see exactly what happens
- **Inspect variables** at any point during execution
- **Navigate the call stack** to understand how execution reached a certain point
- **Evaluate expressions** in the current context to test hypotheses

### Why This Matters

1. **Faster bug resolution** - Instead of guessing and re-running, Claude can pause execution exactly where needed and inspect state directly.

2. **Systematic debugging** - The skill includes debugging methodology that teaches Claude to debug like an experienced developer: form hypotheses, verify assumptions, binary search for bugs.

3. **Better accuracy** - By actually observing runtime values rather than inferring them from code, Claude makes fewer mistakes when diagnosing issues.

4. **Complex bug handling** - Some bugs only manifest at runtime with specific data. Print debugging can't easily catch issues like race conditions, state mutations, or deep call stack problems. A real debugger can.

### Example Scenario

**Without this skill:**
```
User: "This function returns wrong values sometimes"
Claude: *reads code* "I think the issue might be X. Let me add some prints..."
*adds prints, runs, reads output, guesses again*
```

**With this skill:**
```
User: "This function returns wrong values sometimes"
Claude: *sets conditional breakpoint* "Let me pause when the output looks wrong"
*inspects actual variable values at that moment*
"Found it - the input was None here because..."
```

## Installation

### 1. Add the marketplace

```bash
/plugin marketplace add alonw0/python-debugger-skill
```

### 2. Install the plugin

```bash
/plugin install python-debugger@python-debugger-marketplace
```

## Available Plugins

### python-debugger

PyCharm-like Python debugging with breakpoints, stepping, variable inspection, and stack navigation.

**Features:**
- Line, conditional, and exception breakpoints
- Step into, step over, continue, finish
- Variable inspection (locals, globals, eval, deep inspect)
- Call stack navigation
- Built-in debugging methodology and best practices

**Usage:** Just ask Claude Code to debug your Python scripts:
```
"Debug my_script.py - it's returning wrong values"
"Set a breakpoint at line 25 and inspect the variables"
"Why is this function crashing?"
"Step through the loop and show me what's happening"
```

## Repository Structure

```
python-debugger-skill/
├── .claude-plugin/
│   └── marketplace.json
├── plugins/
│   └── python-debugger/
│       ├── .claude-plugin/
│       │   └── plugin.json
│       └── skills/
│           └── python-debugging/
│               ├── SKILL.md
│               ├── scripts/
│               │   ├── debugger.py
│               │   └── inspector.py
│               └── references/
│                   ├── methodology.md
│                   ├── commands.md
│                   ├── examples.md
│                   └── troubleshooting.md
├── examples/
│   └── buggy_calculator.py      # Try debugging this!
└── README.md
```

## Try It Out

The repo includes an example buggy script with 3 intentional bugs. After installing the plugin, ask Claude Code to debug it.

### 1. First, see the bugs in action

```bash
python examples/buggy_calculator.py
```

You'll see incorrect outputs and errors.

### 2. Ask Claude Code to debug

Once the plugin is installed, just ask Claude Code naturally:

```
"Debug examples/buggy_calculator.py - it's crashing on empty lists"
```

```
"Help me find why calculate_total_price returns wrong values on the second call"
```

```
"Step through process_user_data and figure out why it's missing users"
```

Claude Code will automatically use the python-debugging skill to:
- Start a debug session
- Set appropriate breakpoints
- Step through the code
- Inspect variables
- Identify the root cause
- Explain what's wrong and how to fix it

### Example Debugging Session

**You:** "Debug examples/buggy_calculator.py - the calculate_total_price function returns wrong values"

**Claude Code:** *Uses the debugging skill to:*
1. Start the debugger on the script
2. Set a breakpoint inside `apply_discount`
3. Continue and inspect the `discounts` list
4. Notice it accumulates across calls (mutable default argument bug)
5. Explain the issue and suggest the fix

### What Claude Code Can Debug

Just describe the problem naturally:
- "This script crashes sometimes, help me find why"
- "Why does this function return None?"
- "Debug this - the loop skips some items"
- "Set a breakpoint at line 45 and show me what's in the data variable"
- "Step through the calculate function and explain what's happening"

## Requirements

- Python 3.7+
- macOS or Linux

## License

MIT
