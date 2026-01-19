# Debugging Methodology & Best Practices

A comprehensive guide to debugging Python code effectively. This document covers the mindset, process, and techniques that experienced developers use to find and fix bugs efficiently.

## The Debugging Mindset

### Think Like a Detective

Debugging is investigation. You're gathering evidence, forming theories, and testing them systematically. The bug exists for a reason—your job is to find that reason.

**Key mindset shifts:**

1. **Bugs are deterministic** - The same inputs produce the same outputs. If a bug seems random, you don't yet understand all the inputs (including state, timing, external data).

2. **The computer is not wrong** - It's doing exactly what the code tells it. The gap between what you intended and what you wrote is where the bug lives.

3. **Assume nothing** - The most dangerous bugs hide behind assumptions. Verify everything with the debugger.

### Scientific Method for Debugging

Apply the same rigor scientists use:

```
OBSERVE    →  What exactly is happening? What's the error? What's the wrong output?
HYPOTHESIZE  →  What could cause this? Where might the bug be?
PREDICT    →  "If my hypothesis is correct, then variable X should be Y at line Z"
TEST       →  Set a breakpoint, run to it, check your prediction
CONCLUDE   →  Was your prediction correct? If yes, you're closer. If no, new hypothesis.
```

**Example thought process:**
```
Observation: "Function returns 0 instead of the sum"
Hypothesis: "The accumulator variable isn't being updated"
Prediction: "If true, 'total' should remain 0 inside the loop"
Test: Set breakpoint inside loop, check 'total' after each iteration
Conclusion: "total IS being updated... so the bug is elsewhere"
New hypothesis: "Maybe I'm returning the wrong variable"
```

## The Debugging Process

### Step 1: Reproduce the Bug

Before debugging, ensure you can trigger the bug consistently.

**Why this matters:**
- If you can't reproduce it, you can't verify you've fixed it
- Inconsistent reproduction suggests hidden state or timing issues
- The reproduction steps themselves are clues

**What to document:**
- Exact inputs that trigger the bug
- Environment details (Python version, dependencies)
- Any setup steps required

### Step 2: Understand Expected vs Actual Behavior

Be precise about what's wrong:

| Vague | Precise |
|-------|---------|
| "It doesn't work" | "It returns `None` instead of a list of users" |
| "It crashes" | "It raises `KeyError: 'email'` on line 45" |
| "It's slow" | "The `process_data()` function takes 30s for 1000 items" |

### Step 3: Form a Hypothesis

Based on the symptoms, theorize about the cause:

**Good hypotheses are:**
- Specific: "The `user_id` variable is None when passed to `fetch_user()`"
- Testable: Can be verified or refuted with the debugger
- Based on evidence: Connected to the observed symptoms

**Ask yourself:**
- What code path leads to this output/error?
- What values would cause this behavior?
- When was this working? What changed?

### Step 4: Set Strategic Breakpoints

Don't scatter breakpoints randomly. Place them to test your hypothesis:

```bash
# Hypothesis: "user_id is None"
# Strategic breakpoint: where user_id is used
python scripts/debugger.py break -f api.py -l 45 -c "user_id is None"
```

**Breakpoint strategies:**

| Strategy | When to Use |
|----------|-------------|
| At the error line | When you have a stack trace |
| At function entry | To verify inputs are correct |
| At function exit | To verify output before return |
| Conditional | When bug only occurs under specific conditions |
| Exception | When you don't know where the error originates |
| Binary search | When bug location is unknown—start in the middle |

### Step 5: Gather Evidence

At each breakpoint:

1. **Check local variables:** `locals`
2. **Verify specific values:** `eval "variable_name"`
3. **Check types:** `eval "type(variable)"`
4. **Examine complex objects:** `inspect object_name`
5. **Understand context:** `stack` to see how you got here

### Step 6: Iterate Until Root Cause Found

Each observation either:
- **Confirms your hypothesis** → You're on the right track, dig deeper
- **Refutes your hypothesis** → Form a new one based on what you learned

The root cause is where the actual behavior diverges from intended behavior.

### Step 7: Verify the Fix

After fixing:
1. Run the original reproduction steps
2. Verify the bug no longer occurs
3. Check that you haven't broken anything else

## Python Bug Pattern Recognition

### None Propagation

**Symptoms:** `AttributeError: 'NoneType' has no attribute 'X'`

**Common causes:**
- Function doesn't explicitly return (implicit `return None`)
- Dictionary `.get()` returning default `None`
- Failed API calls returning `None`
- Conditional logic that doesn't cover all cases

**Debugging approach:**
```bash
# Find where the None originated
# Set breakpoints at each assignment and check the value
python scripts/debugger.py break -f script.py -l <assignment_line>
python scripts/debugger.py eval "variable"  # Check if None
# Work backwards until you find where it became None
```

### Mutable Default Arguments

**Symptoms:** Function "remembers" values between calls

**The bug:**
```python
def add_item(item, items=[]):  # BUG: default list is shared!
    items.append(item)
    return items
```

**Debugging approach:**
```bash
python scripts/debugger.py eval "add_item.__defaults__"
# Shows: ([...items from previous calls...],)
```

**The fix:** Use `None` as default, create new list inside function.

### Off-by-One Errors

**Symptoms:** Missing first or last item, `IndexError`

**Common causes:**
- `range(len(items))` vs `range(len(items) - 1)`
- `<=` vs `<` in loop conditions
- Forgetting that indices start at 0

**Debugging approach:**
```bash
# Check boundary conditions
python scripts/debugger.py break -f script.py -l <loop_line> -c "i == 0"
python scripts/debugger.py break -f script.py -l <loop_line> -c "i == len(items) - 1"
```

### Scope and Closure Issues

**Symptoms:** `UnboundLocalError`, variable has unexpected value

**The bug:**
```python
count = 0
def increment():
    count += 1  # BUG: Python thinks count is local because of assignment
```

**Debugging approach:**
```bash
python scripts/debugger.py locals   # Check what's in local scope
python scripts/debugger.py globals  # Check what's in global scope
# Compare to see if variable is in expected scope
```

### Type Coercion Surprises

**Symptoms:** Unexpected string concatenation, wrong arithmetic

**Common causes:**
- Input from files/APIs is always strings
- `"1" + "2"` = `"12"`, not `3`
- Integer division in Python 2 vs 3

**Debugging approach:**
```bash
python scripts/debugger.py eval "type(variable)"
python scripts/debugger.py eval "repr(variable)"  # Shows quotes for strings
```

### Mutating While Iterating

**Symptoms:** Missing items, infinite loop, unexpected behavior

**The bug:**
```python
for item in items:
    if should_remove(item):
        items.remove(item)  # BUG: modifying list while iterating
```

**Debugging approach:**
```bash
# Watch the collection size change
python scripts/debugger.py break -f script.py -l <loop_line>
python scripts/debugger.py eval "len(items)"  # Check each iteration
```

### Shallow vs Deep Copy

**Symptoms:** Changes to "copy" affect original

**Debugging approach:**
```bash
python scripts/debugger.py eval "id(original)"
python scripts/debugger.py eval "id(copy)"
# If same ID, they're the same object

python scripts/debugger.py eval "id(original[0])"
python scripts/debugger.py eval "id(copy[0])"
# Check nested objects too
```

### Exception Handling Hiding Bugs

**Symptoms:** Silent failures, unexpected behavior

**The bug:**
```python
try:
    result = risky_operation()
except:  # BUG: catches everything, including bugs
    result = default_value
```

**Debugging approach:**
```bash
# Break on all exceptions to see what's being swallowed
python scripts/debugger.py break -e "*"
```

## Decision Framework

### When to Use Exception Breakpoints

Use `break -e <ExceptionType>`:
- You have an error message but don't know where it originates
- Debugging intermittent failures
- Understanding error propagation
- Finding swallowed exceptions

### When to Use Conditional Breakpoints

Use `break -f file -l line -c "condition"`:
- Bug only occurs on specific iterations
- Bug only occurs with specific values
- You'd hit the breakpoint too many times otherwise
- Debugging loops or frequently-called functions

### When to Step vs Continue

**Use `step` when:**
- You want to see inside a function call
- You're narrowing down which function has the bug
- You need to trace data flow through functions

**Use `next` when:**
- You trust the function being called
- You want to stay at the current level of abstraction
- The function is a library/built-in you don't need to debug

**Use `continue` when:**
- You want to run to the next breakpoint
- You've seen enough at this location
- You're using breakpoints to check specific points

### When to Inspect the Stack

Use `stack`, `up`, `down` when:
- You need to understand how execution reached this point
- The bug might be in a calling function
- You need to check values in the caller's context
- Debugging recursive functions

## Debugging Anti-Patterns

### The Shotgun Debugger

**Problem:** Setting breakpoints everywhere hoping to stumble on the bug.

**Why it fails:** Too much information, no direction, wastes time.

**Better approach:** Form a hypothesis first, set targeted breakpoints.

### The Code Changer

**Problem:** Changing code to "see what happens" without understanding the bug.

**Why it fails:** Might introduce new bugs, doesn't build understanding.

**Better approach:** Understand the bug first, then make one deliberate change.

### The Assumption Maker

**Problem:** Assuming variables have certain values without checking.

**Why it fails:** The bug often lives in violated assumptions.

**Better approach:** Verify everything with `eval`. Trust nothing.

### The Print Debugger (in complex scenarios)

**Problem:** Using print statements when a debugger would be more effective.

**Why it fails:** Can't inspect state dynamically, clutters code, misses the moment.

**Better approach:** Use the debugger for interactive investigation.

### The Error Message Ignorer

**Problem:** Skimming or ignoring error messages and stack traces.

**Why it fails:** Error messages contain crucial information.

**Better approach:** Read the full error message and stack trace carefully.

## Advanced Techniques

### Binary Search Debugging

When you have no idea where the bug is:

1. Set a breakpoint at the midpoint of the code path
2. Check if the bug has already occurred (values already wrong)
3. If yes: bug is in the first half
4. If no: bug is in the second half
5. Repeat until you've narrowed down to a few lines

### Using Eval to Test Fixes

Before modifying code, test your fix hypothesis:

```bash
# Hypothesis: "I should add 1 to the index"
python scripts/debugger.py eval "items[index]"      # Current (wrong) value
python scripts/debugger.py eval "items[index + 1]"  # What the fix would give
```

### Debugging Recursive Functions

1. Set a breakpoint at function entry
2. Use `stack` to see recursion depth
3. Use conditional breakpoint for specific depth: `break -c "depth == 5"`
4. Track how parameters change at each level

### Tracing Data Flow

To understand how data transforms through your code:

1. Start at the source of the data
2. Set breakpoints at each transformation
3. At each stop, `eval` the data to see its current form
4. Follow until you find where it goes wrong

### Debugging Async Code

For async/await code:
1. Set breakpoints inside async functions
2. Be aware that execution order may not be linear
3. Use `stack` to understand the current execution context
4. Consider setting breakpoints on await points

## Checklist: Before You Start Debugging

- [ ] Can I reproduce the bug consistently?
- [ ] Have I read the full error message/stack trace?
- [ ] Do I understand what the code SHOULD do?
- [ ] Do I have a hypothesis about the cause?
- [ ] Have I identified strategic breakpoint locations?

## Checklist: When You're Stuck

- [ ] Am I making assumptions I haven't verified?
- [ ] Have I checked the inputs to the problematic code?
- [ ] Have I looked at the full stack trace?
- [ ] Is the bug actually where I think it is?
- [ ] Would it help to start fresh with a new hypothesis?
- [ ] Can I simplify the reproduction case?
