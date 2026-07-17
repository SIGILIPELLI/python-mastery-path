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

## Exercise

Write a function `divide_safely(a, b)` that returns the division result, or a
descriptive error message string if `b` is zero or either argument isn't a
number — without crashing the program either way.
