# 03 · Functional Programming

Python isn't a purely functional language, but it borrows some of the most
useful ideas from that world: treating functions as values, transforming data
with `map`/`filter`/`reduce`, and writing small anonymous functions with
`lambda`. These tools pair naturally with the comprehensions from the previous
module.

## Functions are first-class objects

A function in Python is just another value: it can be assigned to a variable,
stored in a data structure, or passed as an argument.

```python
def shout(text):
    return text.upper() + "!"

def whisper(text):
    return text.lower() + "..."

greeting = shout          # no parentheses — this stores the function itself
print(greeting("hello"))  # HELLO!

functions = [shout, whisper]
for fn in functions:
    print(fn("Hi there"))
```

## Higher-order functions

A higher-order function takes another function as an argument, or returns one.

```python
def apply_twice(fn, value):
    return fn(fn(value))

def add_ten(x):
    return x + 10

print(apply_twice(add_ten, 5))   # 25
```

## `lambda` — small anonymous functions

`lambda` creates a single-expression function inline, useful when a full `def`
would be overkill — most commonly as a `key=` argument.

```python
square = lambda x: x * x
print(square(6))   # 36

people = [{"name": "Ada", "age": 36}, {"name": "Grace", "age": 85}]
people.sort(key=lambda p: p["age"])
print([p["name"] for p in people])   # ['Ada', 'Grace']
```

Keep lambdas short. If the logic needs a comment or more than one expression,
write a regular `def` function instead — it will be easier to read and debug.

## `map` — transform every element

```python
prices = [19.99, 5.50, 3.25]
with_tax = list(map(lambda p: round(p * 1.08, 2), prices))
print(with_tax)   # [21.59, 5.94, 3.51]

# equivalent, and usually more Pythonic:
with_tax = [round(p * 1.08, 2) for p in prices]
```

## `filter` — keep elements matching a condition

```python
words = ["apple", "kiwi", "fig", "banana", "pear"]
short_words = list(filter(lambda w: len(w) <= 4, words))
print(short_words)   # ['kiwi', 'fig', 'pear']

# equivalent comprehension form:
short_words = [w for w in words if len(w) <= 4]
```

## `functools.reduce` — fold a sequence into one value

`reduce` isn't a builtin — it lives in `functools` because it's less commonly
needed and can hurt readability if overused.

```python
from functools import reduce

numbers = [1, 2, 3, 4, 5]

total = reduce(lambda acc, n: acc + n, numbers)          # 15
product = reduce(lambda acc, n: acc * n, numbers, 1)      # 120, with explicit start value

# for simple cases, builtins are clearer:
total = sum(numbers)
```

## Closures — functions that remember their environment

```python
def make_multiplier(factor):
    def multiplier(x):
        return x * factor   # "factor" is captured from the enclosing scope
    return multiplier

double = make_multiplier(2)
triple = make_multiplier(3)

print(double(5))   # 10
print(triple(5))   # 15
```

`double` and `triple` are both built from the same inner function, but each
one remembers its own `factor` — that's a closure.

## A first look at decorators

A decorator is a higher-order function that wraps another function to add
behavior before/after it runs, without changing the original function's code.
We'll go much deeper into decorators in Level 3; this is the shape to
recognize.

```python
import time

def timed(fn):
    def wrapper(*args, **kwargs):
        start = time.perf_counter()
        result = fn(*args, **kwargs)
        elapsed = time.perf_counter() - start
        print(f"{fn.__name__} took {elapsed:.6f}s")
        return result
    return wrapper


@timed
def slow_square(n):
    total = 0
    for i in range(n):
        total += i * i
    return total


slow_square(1_000_000)
# slow_square took 0.0XXXXXs
```

`@timed` above `def slow_square` is exactly equivalent to writing
`slow_square = timed(slow_square)` right after the function is defined.

## Cheat sheet

| Tool | Purpose | Comprehension equivalent |
|------|---------|---------------------------|
| `map(fn, iterable)` | transform each item | `[fn(x) for x in iterable]` |
| `filter(fn, iterable)` | keep matching items | `[x for x in iterable if fn(x)]` |
| `functools.reduce(fn, iterable)` | fold into one value | usually a `for` loop or `sum`/`max` |
| `lambda args: expr` | inline single-expression function | — |

## Exercise

Given a list of order dictionaries like
`{"item": "Book", "price": 12.5, "qty": 2}`, use `map` and a lambda to compute
each order's total (`price * qty`), `filter` to keep only orders over $20, and
`functools.reduce` to sum the grand total of the filtered orders — then write
the same pipeline again using comprehensions and `sum()` and compare
readability.
