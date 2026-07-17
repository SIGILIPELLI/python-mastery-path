# 05 · Testing at Scale

Level 2 covered `pytest` basics. As a codebase and test suite grow, you need
more powerful fixture composition, a reliable way to isolate external
dependencies, tests that explore many inputs automatically, and a CI pipeline
that runs everything on every change.

## Fixture scopes

By default, a fixture runs fresh for every test that uses it. `scope=` lets
you share expensive setup across many tests when it's safe to do so.

```python
import pytest

@pytest.fixture(scope="function")   # default: fresh for every test
def fresh_list():
    return []


@pytest.fixture(scope="module")     # created once per test file
def expensive_resource():
    print("setting up expensive resource")
    resource = {"connected": True}
    yield resource
    print("tearing down expensive resource")


@pytest.fixture(scope="session")    # created once for the entire test run
def app_config():
    return {"debug": True, "env": "test"}
```

| Scope | Created | Good for |
|-------|---------|----------|
| `function` (default) | once per test | anything mutable, cheap setup |
| `class` | once per test class | grouped tests sharing read-only state |
| `module` | once per file | an expensive resource all tests in a file can share safely |
| `session` | once per test run | truly global, read-only config |

Be careful with broader scopes: if a test mutates a `module`/`session`-scoped
fixture, that mutation leaks into every other test sharing it.

## Fixture composition

Fixtures can depend on other fixtures, building up realistic test data in
layers.

```python
import pytest

@pytest.fixture
def db_session():
    # imagine a real, isolated test database session here
    return {"users": {}, "next_id": 1}


@pytest.fixture
def existing_user(db_session):
    user_id = db_session["next_id"]
    db_session["users"][user_id] = {"name": "Ada", "active": True}
    db_session["next_id"] += 1
    return user_id


def test_existing_user_is_active(db_session, existing_user):
    assert db_session["users"][existing_user]["active"] is True
```

## Mocking with `unittest.mock`

Mocking replaces a real dependency (a network call, the current time, a
database) with a controllable stand-in, so tests are fast, deterministic, and
don't depend on external systems.

```python
from unittest.mock import Mock, patch

def send_welcome_email(email_client, address):
    email_client.send(to=address, subject="Welcome!")
    return True


def test_send_welcome_email_calls_client():
    fake_client = Mock()
    result = send_welcome_email(fake_client, "ada@example.com")

    assert result is True
    fake_client.send.assert_called_once_with(to="ada@example.com", subject="Welcome!")
```

## `patch` — replacing a dependency at its usage site

```python
# weather_service.py
import requests

def get_temperature(city):
    response = requests.get(f"https://api.example.com/weather/{city}")
    return response.json()["temp"]
```

```python
# test_weather_service.py
from unittest.mock import patch
import weather_service

@patch("weather_service.requests.get")
def test_get_temperature(mock_get):
    mock_get.return_value.json.return_value = {"temp": 21}

    result = weather_service.get_temperature("London")

    assert result == 21
    mock_get.assert_called_once_with("https://api.example.com/weather/London")
```

Patch the name *where it's looked up* (`weather_service.requests.get`), not
where it was originally defined (`requests.get`) — a very common source of
mocks that silently don't take effect.

## Property-based testing with Hypothesis

Traditional tests check specific example inputs. Property-based testing
describes a *property* that should hold for a whole category of inputs, and
Hypothesis generates hundreds of test cases (including tricky edge cases) to
try to break it.

```bash
pip install hypothesis
```

```python
from hypothesis import given, strategies as st

def reverse_twice(items):
    return list(reversed(list(reversed(items))))


@given(st.lists(st.integers()))
def test_reverse_twice_is_identity(items):
    assert reverse_twice(items) == items


@given(st.integers(), st.integers())
def test_addition_is_commutative(a, b):
    assert a + b == b + a
```

```bash
pytest -v
# test_properties.py::test_reverse_twice_is_identity PASSED
# test_properties.py::test_addition_is_commutative PASSED
```

When Hypothesis finds a failing case, it automatically "shrinks" it to the
smallest, simplest example that still fails — invaluable for debugging.

```python
from hypothesis import given, strategies as st

def buggy_sort(items):
    return sorted(items)[::-1] if len(items) > 3 else sorted(items)   # deliberately wrong for len > 3


@given(st.lists(st.integers(), min_size=1))
def test_sort_is_ascending(items):
    result = buggy_sort(items)
    assert result == sorted(items)   # Hypothesis will find and shrink a failing case here
```

## Test coverage

```bash
pip install pytest-cov
pytest --cov=my_package --cov-report=term-missing
```

```text
Name                 Stmts   Miss  Cover   Missing
--------------------------------------------------
my_package/core.py      42      3    93%   57-59
--------------------------------------------------
TOTAL                    42      3    93%
```

High coverage doesn't guarantee correctness (a line can execute without its
result being asserted), but low coverage reliably reveals untested code paths.

## Continuous Integration with GitHub Actions

```yaml
# .github/workflows/tests.yml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: ["3.10", "3.11", "3.12"]

    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: ${{ matrix.python-version }}
      - run: pip install -r requirements-dev.txt
      - run: pytest --cov=my_package --cov-report=term-missing
```

Running the matrix across multiple Python versions catches
version-compatibility regressions before users do, and running on every
push/PR means broken code never merges silently.

## Cheat sheet

| Tool | Purpose |
|------|---------|
| `@pytest.fixture(scope=...)` | control how often expensive setup reruns |
| `unittest.mock.Mock` | a controllable fake object |
| `@patch("module.path")` | swap out a real dependency for a mock during a test |
| `hypothesis` | generate many inputs to test a general property |
| `pytest-cov` | measure which lines your tests actually exercise |
| GitHub Actions matrix | run tests across multiple Python versions automatically |

## Exercise

Take the Book Catalog API's `crud.py` from Level 3 and add: a `module`-scoped
fixture wrapping a shared in-memory engine, a `@patch`-based test that mocks
an (imagined) external "notify on new book" HTTP call so it never actually
hits the network, and a Hypothesis property test asserting that for any
generated `title`/`author`/`year`, creating a book and then fetching it by ID
always returns the same values back unchanged.
