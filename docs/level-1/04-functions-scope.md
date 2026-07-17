# 04 · Functions & Scope

## Defining functions

```python
def add(a, b):
    return a + b

def greet(name="friend"):   # default argument
    return f"Hello, {name}!"

print(add(2, 3))    # 5
print(greet())       # Hello, friend!
print(greet("Ada"))  # Hello, Ada!
```

## Type hints (recommended from day one)

```python
def add(a: int, b: int) -> int:
    return a + b
```

Type hints don't change runtime behavior — they document intent and let tools
like `mypy` and your editor catch mistakes before you run the code.

## *args and **kwargs

```python
def total(*numbers: int) -> int:
    return sum(numbers)

def make_profile(**fields: str) -> dict:
    return fields

print(total(1, 2, 3, 4))                 # 10
print(make_profile(name="Ada", city="London"))
# {'name': 'Ada', 'city': 'London'}
```

## Keyword-only and positional-only arguments

```python
def connect(host, port, *, timeout=30):
    # timeout MUST be passed as a keyword: connect("x", 80, timeout=5)
    ...

def divide(a, b, /):
    # a and b MUST be passed positionally: divide(10, 2)
    return a / b
```

## Scope (LEGB)

Python resolves names using Local → Enclosing → Global → Built-in:

```python
x = "global"

def outer():
    x = "enclosing"

    def inner():
        x = "local"
        print(x)  # local

    inner()
    print(x)  # enclosing

outer()
print(x)  # global
```

Use `global` or `nonlocal` to modify an outer variable from an inner scope
(rare — usually a sign to restructure the code instead):

```python
counter = 0

def increment():
    global counter
    counter += 1
```

## Functions are objects

```python
def square(x):
    return x * x

operations = {"square": square}
print(operations["square"](5))  # 25

# Higher-order function: takes a function as an argument
def apply_twice(fn, value):
    return fn(fn(value))

print(apply_twice(square, 3))  # 81
```

## Exercise

Write a function `summarize(*values, **options)` that returns the min, max, and
average of `values`, rounding the average to the number of decimal places given
by `options.get("precision", 2)`.
