# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

This is a Claude Code plugin marketplace containing the **Python Debugger** plugin. The plugin provides PyCharm-like debugging capabilities for Python scripts, including breakpoints, stepping, variable inspection, and stack navigation.

## Repository Structure

```
.claude-plugin/marketplace.json     # Marketplace configuration
plugins/python-debugger/
  .claude-plugin/plugin.json        # Plugin metadata
  skills/python-debugging/
    SKILL.md                        # Skill definition and quick reference
    scripts/
      debugger.py                   # Main debugger implementation
      inspector.py                  # Variable inspection utilities
    references/                     # Extended documentation
examples/
  buggy_calculator.py               # Example script with intentional bugs for testing
```

## Testing the Plugin

Run the example buggy script to see bugs in action:
```bash
python examples/buggy_calculator.py
```

## Debugger Commands

All commands are run from the `plugins/python-debugger/skills/python-debugging/` directory:

```bash
# Start debugging
python scripts/debugger.py start script.py [args...]

# Breakpoints
python scripts/debugger.py break -f script.py -l 45           # Line breakpoint
python scripts/debugger.py break -f script.py -l 45 -c "x>10" # Conditional
python scripts/debugger.py break -e ValueError               # Exception breakpoint

# Execution control
python scripts/debugger.py continue   # Run until next breakpoint
python scripts/debugger.py step       # Step into
python scripts/debugger.py next       # Step over
python scripts/debugger.py finish     # Run until return

# Inspection
python scripts/debugger.py locals     # Local variables
python scripts/debugger.py eval "expression"
python scripts/debugger.py inspect variable_name
python scripts/debugger.py stack      # View call stack
```

## Plugin Installation (for users)

```bash
/plugin marketplace add alonw0/python-debugger-skill
/plugin install python-debugger@python-debugger-marketplace
```
