# 03 · Advanced Decorators & Descriptors

Level 2 showed a basic decorator that wrapped a function. This module covers
decorators that take their own arguments, the `functools.wraps` fix for a
subtle bug those wrappers introduce, and the descriptor protocol — the
mechanism that makes `@property` (and much of Python's object model) work.

## Recap: a plain decorator

```python
def logged(fn):
    def wrapper(*args, **kwargs):
        print(f"calling {fn.__name__}{args}")
        return fn(*args, **kwargs)
    return wrapper


@logged
def add(a, b):
    return a + b

print(add(2, 3))   # calling add(2, 3) / 5
```

## The problem `functools.wraps` solves

Without help, the wrapper function replaces the original's identity —
`__name__`, `__doc__`, and introspection tools all now see `wrapper` instead
of the real function.

```python
print(add.__name__)   # wrapper  <- wrong! we lost the original name
print(add.__doc__)    # None
```

```python
from functools import wraps

def logged(fn):
    @wraps(fn)              # copies __name__, __doc__, etc. from fn onto wrapper
    def wrapper(*args, **kwargs):
        print(f"calling {fn.__name__}{args}")
        return fn(*args, **kwargs)
    return wrapper


@logged
def add(a, b):
    """Add two numbers."""
    return a + b

print(add.__name__)   # add
print(add.__doc__)    # Add two numbers.
```

Always use `@wraps(fn)` in your own decorators — skipping it silently breaks
debugging, documentation tools, and anything else that inspects functions.

## Decorators with their own arguments

To let a decorator accept arguments (`@retry(times=3)` instead of just
`@retry`), you need an extra layer: a function that takes the arguments and
*returns* the actual decorator.

```python
import time
from functools import wraps

def retry(times=3, delay=0.1):
    """Decorator factory: retry(times=3) returns the real decorator."""
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            last_exception = None
            for attempt in range(1, times + 1):
                try:
                    return fn(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    print(f"attempt {attempt} failed: {e}")
                    time.sleep(delay)
            raise last_exception
        return wrapper
    return decorator


attempts = {"count": 0}

@retry(times=3, delay=0)
def flaky():
    attempts["count"] += 1
    if attempts["count"] < 3:
        raise ValueError("not yet!")
    return "success"


print(flaky())
# attempt 1 failed: not yet!
# attempt 2 failed: not yet!
# success
```

`@retry(times=3, delay=0)` first calls `retry(times=3, delay=0)`, which
returns `decorator`; *that* function then gets applied to `flaky`, exactly
like a plain decorator.

## Class-based decorators

A decorator doesn't have to be a function — any callable works, including a
class with `__call__`.

```python
class CountCalls:
    def __init__(self, fn):
        self.fn = fn
        self.calls = 0

    def __call__(self, *args, **kwargs):
        self.calls += 1
        print(f"{self.fn.__name__} has been called {self.calls} time(s)")
        return self.fn(*args, **kwargs)


@CountCalls
def greet(name):
    return f"Hello, {name}!"

greet("Ada")
greet("Grace")
print(greet.calls)   # 2
```

## Stacking multiple decorators

Decorators apply bottom-up: the one closest to the function runs first.

```python
@logged
@retry(times=2, delay=0)
def unreliable_add(a, b):
    return a + b

# equivalent to: unreliable_add = logged(retry(times=2, delay=0)(unreliable_add))
```

## The descriptor protocol

A descriptor is any object defining `__get__`, `__set__`, and/or
`__delete__`, placed as a *class* attribute. It's what powers `@property`,
methods, and `@staticmethod`/`@classmethod` under the hood.

```python
class PositiveNumber:
    """A reusable, validated attribute — a descriptor."""

    def __set_name__(self, owner, name):
        self.name = "_" + name   # store the real value under a private name

    def __get__(self, instance, owner):
        if instance is None:
            return self          # accessed on the class itself, not an instance
        return getattr(instance, self.name)

    def __set__(self, instance, value):
        if value <= 0:
            raise ValueError(f"{self.name[1:]} must be positive, got {value}")
        setattr(instance, self.name, value)


class Product:
    price = PositiveNumber()     # descriptor applied once, reused by every instance
    quantity = PositiveNumber()

    def __init__(self, price, quantity):
        self.price = price        # goes through PositiveNumber.__set__
        self.quantity = quantity


p = Product(9.99, 3)
print(p.price, p.quantity)   # 9.99 3

try:
    p.quantity = -1
except ValueError as e:
    print(e)   # quantity must be positive, got -1
```

Unlike `@property` (which is written per-attribute, per-class), a descriptor
like `PositiveNumber` is written once and reused across as many attributes and
classes as you like — here both `price` and `quantity` share identical
validation logic with zero duplication.

## `@property` is a descriptor

```python
class Circle:
    def __init__(self, radius):
        self.radius = radius

    @property
    def area(self):
        return 3.14159 * self.radius ** 2

# roughly equivalent to writing your own descriptor:
# area = property(fget=lambda self: 3.14159 * self.radius ** 2)
```

`property` is itself a built-in class implementing `__get__`/`__set__` — when
you use `@property`, you're using a descriptor that Python provides for you.

## Cheat sheet

| Tool | Purpose |
|------|---------|
| `@wraps(fn)` | preserve `__name__`/`__doc__` on a wrapper |
| decorator factory (`def deco(arg): def real(fn): ...`) | parameterized decorators |
| class with `__call__` | stateful decorators |
| `__get__`/`__set__`/`__set_name__` | descriptor protocol — reusable validated attributes |
| `@property` | the most common descriptor, built into Python |

## How It Actually Works

`@wraps(fn)` fixes an identity problem that exists because a decorator's wrapper
really is a brand-new `function` object — it has its own freshly built `__name__`
(`"wrapper"`), its own `__doc__` (`None`, since your wrapper has no docstring), and
its own `__dict__`. `functools.wraps` doesn't do anything magical to prevent this —
it runs *after* `wrapper` is defined and copies over a fixed list of attributes
(`__name__`, `__doc__`, `__module__`, `__qualname__`, and merges `__dict__`) from
`fn` onto `wrapper`, and additionally sets `wrapper.__wrapped__ = fn`, which is what
lets introspection tools like `inspect.signature` see through one or more layers of
wrapping to the original function's real parameter list.

A decorator factory like `retry(times=3)` works through ordinary closures, nothing
special to decorators: calling `retry(times=3, delay=0)` runs immediately and
returns `decorator`, a function that has closed over `times` and `delay` in its own
cell variables (exactly the closure mechanism from Level 2). `@retry(times=3,
delay=0)` above `def flaky(): ...` then compiles to `flaky = decorator(flaky)` — the
"factory" layer exists purely because the compiler always calls exactly what
immediately follows `@` with the decorated function as its single argument, so a
parameterized decorator needs one extra function call in between to produce the
actual single-argument decorator.

`@CountCalls` above `def greet` works because Python's call syntax `obj(...)`
compiles to `type(obj).__call__(obj, ...)` regardless of whether `obj` is a plain
function or a class instance — `greet` after decoration is literally a `CountCalls`
instance, and `greet("Ada")` dispatches to `CountCalls.__call__`, which is why state
like `self.calls` persists naturally between calls without needing `global` or a
closure cell.

The descriptor protocol is the real backbone here: attribute lookup on an instance
(`obj.attr`) first checks `type(obj).__mro__` for `attr`; if what it finds there
defines `__get__` *and* `__set__` (a **data descriptor**, like `PositiveNumber` or
`property`), that descriptor wins even over an entry already sitting in
`obj.__dict__`. `p.price = 9.99` therefore doesn't write into `p.__dict__["price"]`
at all — it's intercepted by `PositiveNumber.__set__`, which validates and stores the
value under `p.__dict__["_price"]` instead. `__set_name__` is a hook the class
machinery calls automatically, once, right after the class body finishes executing,
telling each descriptor instance what attribute name it was assigned to — which is
exactly how one `PositiveNumber()` instance shared by `price` and `quantity` knows to
store each under a different private name (`_price` vs. `_quantity`) without you
passing the name explicitly.

## Exercise

Write a decorator factory `@cache_for(seconds)` that caches a function's
return value per unique set of arguments, re-running the function only after
`seconds` have elapsed since the last call with those exact arguments (use
`functools.wraps` and `time.monotonic()`). Then write a `TypedAttribute(type_)`
descriptor that raises `TypeError` if a value of the wrong type is assigned,
and use it to build a `Point` class with strictly-`float` `x`/`y` attributes.
