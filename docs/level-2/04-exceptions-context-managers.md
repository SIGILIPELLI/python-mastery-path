# 04 · Custom Exceptions & Context Managers

Level 1 covered catching built-in exceptions. Real projects usually define
their own exception types to represent domain-specific failures, and rely on
context managers (the `with` statement) to guarantee cleanup code runs even
when something goes wrong.

## Defining custom exceptions

A custom exception is just a class that inherits from `Exception` (directly or
indirectly).

```python
class InsufficientFundsError(Exception):
    """Raised when a withdrawal exceeds the available balance."""


class Account:
    def __init__(self, balance):
        self.balance = balance

    def withdraw(self, amount):
        if amount > self.balance:
            raise InsufficientFundsError(
                f"cannot withdraw {amount}, balance is {self.balance}"
            )
        self.balance -= amount
        return self.balance


account = Account(100)
try:
    account.withdraw(150)
except InsufficientFundsError as e:
    print(f"Transaction failed: {e}")
```

## Building an exception hierarchy

Group related errors under a common base class so callers can catch broadly or
narrowly depending on what they need.

```python
class AppError(Exception):
    """Base class for all errors raised by this application."""


class ValidationError(AppError):
    """Input failed validation."""


class NotFoundError(AppError):
    """A requested resource doesn't exist."""


def get_user(users, user_id):
    if not isinstance(user_id, int):
        raise ValidationError(f"user_id must be an int, got {type(user_id).__name__}")
    if user_id not in users:
        raise NotFoundError(f"no user with id {user_id}")
    return users[user_id]


users = {1: "Ada", 2: "Grace"}

for bad_id in ("x", 99):
    try:
        get_user(users, bad_id)
    except AppError as e:
        # catches ValidationError AND NotFoundError since both are AppError
        print(f"{type(e).__name__}: {e}")
```

## Adding structured data to exceptions

Override `__init__` to attach extra context beyond the message string.

```python
class APIError(Exception):
    def __init__(self, message, status_code):
        super().__init__(message)
        self.status_code = status_code


try:
    raise APIError("rate limit exceeded", status_code=429)
except APIError as e:
    print(f"[{e.status_code}] {e}")   # [429] rate limit exceeded
```

## Re-raising and exception chaining

```python
def load_config(path):
    try:
        with open(path) as f:
            return f.read()
    except FileNotFoundError as e:
        raise AppError(f"config file missing: {path}") from e


try:
    load_config("missing.cfg")
except AppError as e:
    print(e)
    print(e.__cause__)   # the original FileNotFoundError, preserved for debugging
```

## The `with` statement

`with` guarantees a "cleanup" step runs when a block ends — even if an
exception is raised inside it. You've already used this for files:

```python
with open("notes.txt", "w") as f:
    f.write("hello")
# file is closed automatically here, even if write() had raised
```

## Writing your own context manager (class-based)

Any object with `__enter__` and `__exit__` methods can be used with `with`.

```python
class Timer:
    def __enter__(self):
        import time
        self.start = time.perf_counter()
        return self   # this becomes the "as" variable

    def __exit__(self, exc_type, exc_value, traceback):
        import time
        elapsed = time.perf_counter() - self.start
        print(f"elapsed: {elapsed:.4f}s")
        return False  # False (or None) means: don't suppress exceptions


with Timer():
    total = sum(range(1_000_000))
```

`__exit__` receives details about any exception that occurred inside the
block. Returning `True` from `__exit__` suppresses the exception; returning
`False`/`None` (the default) lets it propagate normally.

## `contextlib.contextmanager` — the easy way

Writing a full class for simple context managers is often overkill.
`@contextmanager` turns a generator function into one instead.

```python
from contextlib import contextmanager

@contextmanager
def managed_resource(name):
    print(f"acquiring {name}")
    try:
        yield name          # everything before yield is __enter__, after is __exit__
    finally:
        print(f"releasing {name}")


with managed_resource("database connection") as resource:
    print(f"using {resource}")

# acquiring database connection
# using database connection
# releasing database connection
```

The `try`/`finally` ensures the release code runs even if the `with` block
raises an exception.

## `contextlib.suppress`

```python
from contextlib import suppress

with suppress(FileNotFoundError):
    import os
    os.remove("temp_file_that_might_not_exist.txt")
# no crash even if the file doesn't exist
```

## Cheat sheet

| Tool | Use for |
|------|---------|
| `class MyError(Exception)` | a new, meaningful error type |
| `raise X from Y` | chaining — preserve the original cause |
| `class` with `__enter__`/`__exit__` | reusable context manager needing state |
| `@contextlib.contextmanager` | quick context manager from a generator |
| `contextlib.suppress(Err)` | ignore a specific, expected exception |

## Exercise

Define a `DatabaseConnectionError(AppError)` exception, and write a
`@contextmanager` function `db_connection(url)` that prints "connecting",
yields a fake connection object, and prints "closing" in a `finally` block
even if the code using the connection raises. Then simulate a failure inside
the `with` block and confirm "closing" still prints before the exception
propagates.
