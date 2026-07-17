# 09 · Testing Basics (pytest)

Manually running your code and eyeballing the output doesn't scale — and it's
easy to forget to re-check old behavior after a change. Automated tests let
you verify your code works now, and keep verifying it as you change it.
`pytest` is the most widely used testing tool in the Python ecosystem.

## Installing pytest

```bash
pip install pytest
```

## Your first test

pytest discovers test files named `test_*.py` or `*_test.py`, and inside them,
functions named `test_*`.

```python
# calculator.py
def add(a, b):
    return a + b

def divide(a, b):
    if b == 0:
        raise ValueError("cannot divide by zero")
    return a / b
```

```python
# test_calculator.py
from calculator import add, divide

def test_add():
    assert add(2, 3) == 5

def test_add_negative_numbers():
    assert add(-1, -1) == -2

def test_divide():
    assert divide(10, 2) == 5
```

```bash
pytest
# ================= test session starts =================
# collected 3 items
#
# test_calculator.py ...                              [100%]
#
# ================== 3 passed in 0.01s ===================
```

## Plain `assert` — no special API needed

pytest rewrites plain `assert` statements to give you rich failure output,
without needing methods like `assertEqual`.

```python
def test_add_shows_useful_failure():
    assert add(2, 2) == 5   # deliberately wrong, to show the output
```

```text
    def test_add_shows_useful_failure():
>       assert add(2, 2) == 5
E       assert 4 == 5
E        +  where 4 = add(2, 2)
```

## Testing for expected exceptions

```python
import pytest
from calculator import divide

def test_divide_by_zero_raises():
    with pytest.raises(ValueError):
        divide(10, 0)

def test_divide_by_zero_message():
    with pytest.raises(ValueError, match="cannot divide by zero"):
        divide(10, 0)
```

## Fixtures — shared setup

A fixture is a function that provides data or a resource to your tests.
pytest injects it automatically when a test function takes a parameter with
the same name.

```python
# test_shopping_cart.py
import pytest

class ShoppingCart:
    def __init__(self):
        self.items = []

    def add(self, name, price):
        self.items.append({"name": name, "price": price})

    @property
    def total(self):
        return sum(item["price"] for item in self.items)


@pytest.fixture
def cart():
    """Runs before each test that requests it, returning a fresh cart."""
    c = ShoppingCart()
    c.add("Book", 12.50)
    c.add("Pen", 1.50)
    return c


def test_cart_total(cart):
    assert cart.total == 14.00

def test_cart_add_more_items(cart):
    cart.add("Notebook", 5.00)
    assert cart.total == 19.00
```

Each test gets its own fresh `cart` — fixtures don't leak state between tests.

## Fixtures with teardown

```python
@pytest.fixture
def temp_file(tmp_path):
    """tmp_path is a built-in pytest fixture: a unique temp directory per test."""
    path = tmp_path / "data.txt"
    path.write_text("hello")
    yield path                  # test runs here
    # anything after yield runs as cleanup, even if the test fails
    print(f"cleaning up {path}")


def test_temp_file_contents(temp_file):
    assert temp_file.read_text() == "hello"
```

## Parametrized tests

Run the same test logic against many inputs without copy-pasting.

```python
import pytest
from calculator import add

@pytest.mark.parametrize("a, b, expected", [
    (1, 1, 2),
    (2, 3, 5),
    (-1, 1, 0),
    (0, 0, 0),
])
def test_add_parametrized(a, b, expected):
    assert add(a, b) == expected
```

```bash
pytest -v
# test_calculator.py::test_add_parametrized[1-1-2] PASSED
# test_calculator.py::test_add_parametrized[2-3-5] PASSED
# test_calculator.py::test_add_parametrized[-1-1-0] PASSED
# test_calculator.py::test_add_parametrized[0-0-0] PASSED
```

## Useful command-line flags

| Command | Effect |
|---------|--------|
| `pytest` | run everything discovered |
| `pytest -v` | verbose — show each test name |
| `pytest -k "add"` | run only tests whose name contains "add" |
| `pytest -x` | stop after the first failure |
| `pytest --tb=short` | shorter tracebacks on failure |

## Exercise

Write `stack.py` with a small `Stack` class (`push`, `pop`, `peek`, `is_empty`,
raising a custom `EmptyStackError` when popping/peeking an empty stack). Then
write `test_stack.py` with: a fixture that returns an empty `Stack`, a
parametrized test that pushes several values and confirms they pop back in
reverse (LIFO) order, and a test that confirms `pop()` on an empty stack raises
`EmptyStackError` using `pytest.raises`.
