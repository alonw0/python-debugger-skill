# Troubleshooting

Common issues and solutions for the Python Debugger.

## Connection Issues

### "Could not connect to debugger. Is it running?"

**Cause:** The debugger subprocess is not running or the socket connection failed.

**Solutions:**
1. Check if a session is active: `python scripts/debugger.py status`
2. If stale session, quit and restart:
   ```bash
   python scripts/debugger.py quit
   python scripts/debugger.py start script.py
   ```
3. Manually clean up session files:
   ```bash
   rm -rf ~/.claude_debugger/
   ```

### "Debugger already running for this script"

**Cause:** A previous session wasn't properly terminated.

**Solutions:**
1. Quit the existing session: `python scripts/debugger.py quit`
2. If that fails, kill the process:
   ```bash
   python scripts/debugger.py status  # Get PID
   kill <pid>
   rm -rf ~/.claude_debugger/
   ```

## Execution Issues

### Script doesn't stop at breakpoints

**Possible causes:**
1. Breakpoint set on wrong file path (relative vs absolute)
2. Line number doesn't contain executable code
3. Condition never evaluates to true

**Solutions:**
1. Use absolute paths: `break -f /full/path/to/script.py -l 45`
2. Verify line has executable code (not comment or blank)
3. Test condition separately: `eval "your_condition"`
4. List breakpoints to verify: `breakpoints`

### "Expression evaluation timed out"

**Cause:** The expression took longer than 5 seconds to evaluate.

**Solutions:**
1. Simplify the expression
2. Avoid expressions that iterate over large collections
3. Check for infinite loops in the expression

### Script exits immediately

**Cause:** The script may have completed before reaching breakpoints.

**Solutions:**
1. Set breakpoint at the start of the script
2. Use exception breakpoint if script is crashing: `break -e "*"`
3. Check script's entry point

## Inspection Issues

### Variables show "<circular reference>"

**Cause:** Object contains a reference to itself.

**Solution:** This is expected behavior to prevent infinite recursion. The object exists but can't be fully displayed.

### Large objects are truncated

**Cause:** By design, output is limited to prevent overwhelming responses.

**Workarounds:**
1. Use `inspect` with higher depth: `inspect var -d 6`
2. Use `eval` to access specific parts: `eval "large_dict['specific_key']"`
3. For DataFrames: `eval "df.head(20).to_dict()"`

### "No frame available"

**Cause:** Trying to inspect when not paused at a breakpoint.

**Solution:** Make sure the debugger is paused:
```bash
python scripts/debugger.py status
```

## Platform Issues

### Unix socket errors

**Cause:** Socket file permissions or filesystem issues.

**Solutions:**
1. Check `~/.claude_debugger/` directory permissions
2. Ensure the filesystem supports Unix sockets
3. Clean up and retry:
   ```bash
   rm -rf ~/.claude_debugger/
   python scripts/debugger.py start script.py
   ```

### Signal handling conflicts

**Cause:** Script being debugged also uses SIGALRM or SIGTERM.

**Workaround:** The debugger uses these signals internally. If your script depends on them, be aware of potential conflicts.

## Best Practices

1. **Always quit sessions when done:** `python scripts/debugger.py quit`
2. **Use absolute paths** for breakpoint file arguments
3. **Start simple:** Test with a basic script before debugging complex ones
4. **Check status frequently:** `python scripts/debugger.py status`
5. **Use exception breakpoints** to find crashes: `break -e "*"`

## Getting Help

If issues persist:
1. Check the session state: `ls -la ~/.claude_debugger/`
2. Review the session file contents for error messages
3. Ensure you're using Python 3.7+
4. Try with a minimal test script to isolate the issue
