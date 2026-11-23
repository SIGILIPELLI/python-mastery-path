---
title: "Python Cheat Sheet: Quick Reference, Beginner to Advanced"
description: "A free Python cheat sheet: 18 quick-reference tables from every level of the Python Mastery Path, each linked to its full lesson."
---

# Python Cheat Sheet

Quick-reference tables from **18 lessons** of the free Python Mastery Path, in course order from beginner to advanced. Each section links to the full lesson with explanations and runnable examples.

## Level 1 · Entry

### [07 · File I/O Basics](level-1/07-file-io.md)

| Mode | Meaning |
|------|---------|
| `"r"` | read (default, error if file missing) |
| `"w"` | write (creates file, **overwrites** existing content) |
| `"a"` | append (creates file if missing, adds to the end) |
| `"x"` | exclusive create (errors if file already exists) |
| `"rb"` / `"wb"` | binary read/write |

## Level 2 · Intermediate

### [03 · Functional Programming](level-2/03-functional-programming.md)

| Tool | Purpose | Comprehension equivalent |
|------|---------|---------------------------|
| `map(fn, iterable)` | transform each item | `[fn(x) for x in iterable]` |
| `filter(fn, iterable)` | keep matching items | `[x for x in iterable if fn(x)]` |
| `functools.reduce(fn, iterable)` | fold into one value | usually a `for` loop or `sum`/`max` |
| `lambda args: expr` | inline single-expression function | — |

### [04 · Custom Exceptions &amp; Context Managers](level-2/04-exceptions-context-managers.md)

| Tool | Use for |
|------|---------|
| `class MyError(Exception)` | a new, meaningful error type |
| `raise X from Y` | chaining — preserve the original cause |
| `class` with `__enter__`/`__exit__` | reusable context manager needing state |
| `@contextlib.contextmanager` | quick context manager from a generator |
| `contextlib.suppress(Err)` | ignore a specific, expected exception |

### [07 · Dates &amp; Times](level-2/07-dates-times.md)

| Task | Tool |
|------|------|
| Current local time | `datetime.now()` |
| Current UTC time | `datetime.now(ZoneInfo("UTC"))` |
| Add/subtract time | `timedelta(days=..., hours=...)` |
| `datetime` -> string | `.strftime(fmt)` or `.isoformat()` |
| string -> `datetime` | `datetime.strptime(text, fmt)` or `.fromisoformat()` |
| Convert timezone | `.astimezone(ZoneInfo("..."))` |

## Level 3 · Advanced

### [01 · Advanced OOP](level-3/01-advanced-oop.md)

| Concept | Purpose |
|---------|---------|
| `ABC` + `@abstractmethod` | enforce a required interface |
| Mixin | share one focused behavior across unrelated classes |
| MRO (`ClassName.__mro__`) | the order Python searches for attributes/methods |
| `@cached_property` | compute an expensive attribute once, reuse it |
| `metaclass=` | customize how classes themselves are constructed |

### [02 · Iterators, Generators &amp; Coroutines](level-3/02-iterators-generators-coroutines.md)

| Concept | What it does |
|---------|---------------|
| `__iter__` | returns an iterator for an iterable |
| `__next__` | returns the next value or raises `StopIteration` |
| `yield` | pauses a generator function, producing a value |
| `gen.send(value)` | resumes the generator, injecting `value` at the paused `yield` |
| `gen.throw(exc)` | resumes the generator by raising `exc` at the paused `yield` |
| `itertools` | fast, memory-efficient iterator utilities |

### [03 · Advanced Decorators &amp; Descriptors](level-3/03-decorators-descriptors.md)

| Tool | Purpose |
|------|---------|
| `@wraps(fn)` | preserve `__name__`/`__doc__` on a wrapper |
| decorator factory (`def deco(arg): def real(fn): ...`) | parameterized decorators |
| class with `__call__` | stateful decorators |
| `__get__`/`__set__`/`__set_name__` | descriptor protocol — reusable validated attributes |
| `@property` | the most common descriptor, built into Python |

### [07 · Consuming APIs](level-3/07-consuming-apis.md)

| Task | Code |
|------|------|
| GET with query params | `requests.get(url, params={...}, timeout=10)` |
| POST JSON body | `requests.post(url, json={...})` |
| Check for HTTP errors | `response.raise_for_status()` |
| Reusable session + retries | `requests.Session()` + `HTTPAdapter` |
| Read a secret safely | `os.environ.get("API_TOKEN")` |

### [08 · Building APIs (Flask/FastAPI)](level-3/08-building-apis.md)

| Concept | Syntax |
|---------|--------|
| Path parameter | `def route(item_id: int):` with `@app.get("/items/{item_id}")` |
| Query parameter | plain function argument with a default value |
| Request body | a `BaseModel` subclass as a function argument |
| Response shape | `response_model=` on the route decorator |
| Error response | `raise HTTPException(status_code=..., detail=...)` |
| Shared logic | `Depends(dependency_function)` |

### [09 · Packaging &amp; Distribution](level-3/09-packaging-distribution.md)

| Task | Command |
|------|---------|
| Editable install for development | `pip install -e ".[dev]"` |
| Build wheel + sdist | `python -m build` |
| Upload to TestPyPI | `twine upload --repository testpypi dist/*` |
| Upload to real PyPI | `twine upload dist/*` |

### [10 · Profiling &amp; Performance](level-3/10-profiling-performance.md)

| Question | Tool |
|----------|------|
| Which of these two snippets is faster? | `timeit` |
| Which function is my program's bottleneck? | `cProfile` (sorted by `cumulative`) |
| Which *line* inside that function is slow? | `line_profiler` |
| Is a function using too much memory? | `memory_profiler` |
| Visualize a whole profile | `snakeviz` |

## Level 4 · Master

### [02 · Advanced Asyncio Patterns](level-4/02-advanced-asyncio.md)

| Tool | Use |
|------|-----|
| `asyncio.TaskGroup()` | run multiple tasks with guaranteed cleanup/propagation |
| `except*` | handle an `ExceptionGroup` raised by a `TaskGroup` |
| `task.cancel()` | request cancellation of a running task |
| `asyncio.timeout(seconds)` | cancel a block of code if it runs too long |
| `asyncio.Queue` | coordinate producer/consumer coroutines |
| `asyncio.Semaphore(n)` | cap how many coroutines run concurrently |

### [03 · Metaprogramming](level-4/03-metaprogramming.md)

| Tool | Purpose |
|------|---------|
| `__init_subclass__` | react to subclass creation (preferred, simpler) |
| `metaclass=` / `type.__new__` | full control over class construction |
| `type(name, bases, ns)` | build a class dynamically at runtime |
| `exec(code, namespace)` | generate and run code from a string (framework-level only) |
| `inspect` module | introspect signatures, source, members at runtime |

### [04 · Production-Grade APIs](level-4/04-production-apis.md)

| Concern | Tool |
|---------|------|
| Login & tokens | OAuth2 password flow + JWT (`python-jose`) |
| Password storage | `passlib` with bcrypt, never plain text |
| Cross-cutting logic | `@app.middleware("http")` |
| Cross-origin requests | `CORSMiddleware` (explicit origins, not `*` with credentials) |
| API evolution | prefix-based routers (`/api/v1`, `/api/v2`) |
| Abuse protection | `slowapi` rate limiting |
| Consistent error shape | `@app.exception_handler(...)` |

### [05 · Testing at Scale](level-4/05-testing-at-scale.md)

| Tool | Purpose |
|------|---------|
| `@pytest.fixture(scope=...)` | control how often expensive setup reruns |
| `unittest.mock.Mock` | a controllable fake object |
| `@patch("module.path")` | swap out a real dependency for a mock during a test |
| `hypothesis` | generate many inputs to test a general property |
| `pytest-cov` | measure which lines your tests actually exercise |
| GitHub Actions matrix | run tests across multiple Python versions automatically |

### [06 · Data Engineering](level-4/06-data-engineering.md)

| Task | Code |
|------|------|
| Read CSV/JSON/Excel | `pd.read_csv/json/excel(path)` |
| Filter rows | `df[df["col"] > value]` |
| New column from existing ones | `df["new"] = df["a"] * df["b"]` |
| Group and summarize | `df.groupby("col").agg(...)` |
| Join two tables | `df1.merge(df2, on="key", how="left")` |
| Handle missing data | `df.dropna()` / `df.fillna(value)` |

### [07 · ML Foundations](level-4/07-ml-foundations.md)

| Step | scikit-learn tool |
|------|---------------------|
| Split data | `train_test_split(X, y, test_size=..., random_state=...)` |
| Scale features | `StandardScaler().fit_transform(...)` |
| Train a model | `model.fit(X_train, y_train)` |
| Predict | `model.predict(X_test)` |
| Regression metrics | `mean_absolute_error`, `mean_squared_error`, `r2_score` |
| Classification metrics | `accuracy_score`, `classification_report` |
| Chain steps safely | `Pipeline([...])` |
| Robust evaluation | `cross_val_score(model, X, y, cv=5)` |

### [09 · Security Best Practices](level-4/09-security-best-practices.md)

| Vulnerability | Cause | Prevention |
|----------------|-------|-------------|
| SQL injection | string-built queries with untrusted input | parameterized queries / ORM |
| XSS | unescaped user input rendered as HTML | auto-escaping templates, avoid `\| safe` |
| Command injection | `shell=True` with untrusted input | pass argument lists, avoid `shell=True` |
| Insecure deserialization | `pickle.load` on untrusted data | use JSON for untrusted data |
| Weak password storage | fast/reversible hashing, or plain text | bcrypt/argon2 via `passlib` |
| Hard-coded secrets | credentials committed to source | environment variables / secrets manager |
| Known-vulnerable dependencies | outdated packages | `pip-audit` in CI |

---

Go deeper with the full [Python Mastery Path](index.md) curriculum or test yourself with the [interview questions](interview-questions.md).
