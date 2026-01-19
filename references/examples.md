# Example Debugging Sessions

Real-world examples of using the Python Debugger.

## Example 1: Finding a Logic Bug

**Script:** `calculate.py`
```python
def calculate_average(numbers):
    total = 0
    for num in numbers:
        total += num
    return total / len(numbers)  # Bug: doesn't handle empty list

result = calculate_average([])
print(f"Average: {result}")
```

**Debugging Session:**
```bash
# Start debugging
$ python scripts/debugger.py start calculate.py

# Output shows we're at line 1
{"status": "paused", "location": {"line": 1, ...}}

# Set breakpoint at the division
$ python scripts/debugger.py break -f calculate.py -l 5

# Continue to breakpoint
$ python scripts/debugger.py continue

# Check the variables
$ python scripts/debugger.py locals
{"locals": {"total": {"type": "int", "value": "0"}, "numbers": {"type": "list", "value": "<list with 0 items>"}}}

# Aha! numbers is empty, len(numbers) is 0 - division by zero!

# Quit
$ python scripts/debugger.py quit
```

## Example 2: Debugging an Exception

**Script:** `process_data.py`
```python
def process_user(data):
    name = data['name']
    age = data['age']
    return f"{name} is {age} years old"

users = [
    {'name': 'Alice', 'age': 30},
    {'name': 'Bob'},  # Missing 'age' key
    {'name': 'Carol', 'age': 25}
]

for user in users:
    print(process_user(user))
```

**Debugging Session:**
```bash
# Start with exception breakpoint
$ python scripts/debugger.py start process_data.py
$ python scripts/debugger.py break -e KeyError
$ python scripts/debugger.py continue

# Stops when KeyError is raised
{"status": "paused", "stop_reason": "exception",
 "exception": {"type": "KeyError", "message": "'age'"}, ...}

# Check what user we're processing
$ python scripts/debugger.py eval "data"
{"result": {"type": "dict", "value": "{'name': 'Bob'}"}}

# Found it - Bob is missing the 'age' key!

$ python scripts/debugger.py quit
```

## Example 3: Stepping Through Code

**Script:** `fibonacci.py`
```python
def fib(n):
    if n <= 1:
        return n
    return fib(n-1) + fib(n-2)

result = fib(5)
print(result)
```

**Debugging Session:**
```bash
$ python scripts/debugger.py start fibonacci.py
$ python scripts/debugger.py break -f fibonacci.py -l 6
$ python scripts/debugger.py continue

# At the call to fib(5)
$ python scripts/debugger.py step  # Step into fib()

{"location": {"line": 2, "function": "fib"}}

$ python scripts/debugger.py locals
{"locals": {"n": {"type": "int", "value": "5"}}}

$ python scripts/debugger.py next  # Step over the if check
$ python scripts/debugger.py next  # Now at return statement

# Step into the recursive call
$ python scripts/debugger.py step

$ python scripts/debugger.py locals
{"locals": {"n": {"type": "int", "value": "4"}}}

# Use finish to run until this call returns
$ python scripts/debugger.py finish

$ python scripts/debugger.py quit
```

## Example 4: Inspecting Complex Objects

**Script:** `data_analysis.py`
```python
import pandas as pd

df = pd.DataFrame({
    'name': ['Alice', 'Bob', 'Carol'],
    'score': [85, 92, 78],
    'grade': ['B', 'A', 'C']
})

filtered = df[df['score'] > 80]
print(filtered)
```

**Debugging Session:**
```bash
$ python scripts/debugger.py start data_analysis.py
$ python scripts/debugger.py break -f data_analysis.py -l 9
$ python scripts/debugger.py continue

# Inspect the DataFrame
$ python scripts/debugger.py inspect df
{
  "type": "DataFrame",
  "shape": [3, 3],
  "column_info": [
    {"name": "name", "dtype": "object", "samples": ["Alice"]},
    {"name": "score", "dtype": "int64", "samples": ["85"]},
    {"name": "grade", "dtype": "object", "samples": ["B"]}
  ],
  "preview": [
    {"name": "Alice", "score": 85, "grade": "B"},
    {"name": "Bob", "score": 92, "grade": "A"},
    {"name": "Carol", "score": 78, "grade": "C"}
  ]
}

# Evaluate a filter expression
$ python scripts/debugger.py eval "df[df['score'] > 90].to_dict()"

$ python scripts/debugger.py quit
```

## Example 5: Navigating the Call Stack

**Script:** `nested_calls.py`
```python
def level3(value):
    result = value * 2
    return result  # Breakpoint here

def level2(value):
    return level3(value + 10)

def level1(value):
    return level2(value + 5)

output = level1(100)
print(output)
```

**Debugging Session:**
```bash
$ python scripts/debugger.py start nested_calls.py
$ python scripts/debugger.py break -f nested_calls.py -l 3
$ python scripts/debugger.py continue

# Stopped in level3
$ python scripts/debugger.py locals
{"locals": {"value": {"type": "int", "value": "115"}}}

# View the call stack
$ python scripts/debugger.py stack
{"stack": [
  {"index": 0, "function": "level3", "current": true},
  {"index": 1, "function": "level2"},
  {"index": 2, "function": "level1"},
  {"index": 3, "function": "<module>"}
]}

# Move up to see level2's context
$ python scripts/debugger.py up
{"location": {"function": "level2", "line": 6}}

$ python scripts/debugger.py locals
{"locals": {"value": {"type": "int", "value": "105"}}}

# Move up again to level1
$ python scripts/debugger.py up
$ python scripts/debugger.py locals
{"locals": {"value": {"type": "int", "value": "100"}}}

# Move back down
$ python scripts/debugger.py down
$ python scripts/debugger.py down

# Now back in level3
$ python scripts/debugger.py quit
```

## Example 6: Conditional Breakpoints

**Script:** `loop_bug.py`
```python
def process_items(items):
    results = []
    for i, item in enumerate(items):
        processed = item.upper()  # Bug: fails on None
        results.append(processed)
    return results

data = ['apple', 'banana', None, 'cherry']
process_items(data)
```

**Debugging Session:**
```bash
$ python scripts/debugger.py start loop_bug.py
# Only stop when item is None
$ python scripts/debugger.py break -f loop_bug.py -l 4 -c "item is None"
$ python scripts/debugger.py continue

# Stops only when the condition is true
{"location": {"line": 4}, ...}

$ python scripts/debugger.py locals
{"locals": {"i": {"value": "2"}, "item": {"value": "None"}}}

# Found where it will fail!
$ python scripts/debugger.py quit
```
