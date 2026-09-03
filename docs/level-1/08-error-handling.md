# 08 · Error Handling Basics

## try / except

```python
try:
    result = 10 / 0
except ZeroDivisionError:
    print("can't divide by zero")
```

## Catching specific exceptions

Always catch the narrowest exception type you can — a bare `except:` hides bugs.

```python
def safe_int(value):
    try:
        return int(value)
    except ValueError:
        print(f"'{value}' is not a valid number")
        return None

safe_int("42")    # 42
safe_int("abc")   # prints message, returns None
```

## else and finally

```python
try:
    number = int("42")
except ValueError:
    print("conversion failed")
else:
    print(f"conversion succeeded: {number}")  # runs only if no exception
finally:
    print("this always runs")  # cleanup, runs no matter what
```

## Multiple exception types

```python
try:
    data = {"a": 1}
    print(data["b"])
except (KeyError, IndexError) as e:
    print(f"lookup failed: {e}")
```

## Raising your own exceptions

```python
def withdraw(balance, amount):
    if amount > balance:
        raise ValueError("insufficient funds")
    return balance - amount

try:
    withdraw(100, 150)
except ValueError as e:
    print(e)  # insufficient funds
```

## Common built-in exceptions

| Exception | When it happens |
|-----------|------------------|
| `ValueError` | right type, wrong value (`int("abc")`) |
| `TypeError` | wrong type entirely (`"2" + 2`) |
| `KeyError` | missing dict key |
| `IndexError` | list index out of range |
| `FileNotFoundError` | opening a file that doesn't exist |
| `ZeroDivisionError` | dividing by zero |

## How It Actually Works

**Entering a `try` block is now free.** Up to Python 3.10, `try` emitted a
`SETUP_FINALLY` opcode that pushed a handler entry onto a runtime block stack
on every execution. Since 3.11, the compiler instead builds a static
**exception table**: a side table mapping ranges of bytecode offsets to the
handler that covers them. If no exception is raised, that table is never
consulted — so `try` costs nothing until something actually goes wrong
("zero-cost exceptions").

**When an exception is raised:**

1. `raise` (or a failing operation) creates an exception *object* and starts
   unwinding. The interpreter also attaches a *traceback* object, and as each
   frame is unwound it prepends that frame's location — this is why a
   traceback reads outermost-call-first, bottom-up.
2. For the current frame, the interpreter looks up the instruction pointer in
   the exception table. If a handler covers it, execution jumps there with the
   exception pushed onto the value stack.
3. Each `except X` clause runs an `isinstance(exc, X)` check. The *first*
   matching clause wins, which is why you order narrow-to-broad. No match
   means the exception keeps unwinding into the calling frame, repeating from
   step 2.
4. If it reaches the top frame unhandled, CPython prints the traceback to
   `stderr` and exits with status 1.

`finally` and `with`-cleanup are woven in as handler entries that run their
code and then *re-raise*. `raise X from Y` sets `X.__cause__ = Y`; an
exception raised while handling another automatically gets `__context__` set —
both are what produce "During handling of the above exception, another
occurred".

## Exercise

Write a function `divide_safely(a, b)` that returns the division result, or a
descriptive error message string if `b` is zero or either argument isn't a
number — without crashing the program either way.
