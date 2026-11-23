---
description: "Consuming & Building APIs — call HTTP APIs reliably with requests, then build your own with FastAPI."
---

# 07 · Consuming & Building APIs

This module covers both sides of an HTTP API: first you call other people's APIs
properly with `requests`, then you build your own with FastAPI.

## 🎥 Video walkthroughs

**Part 1 — Consuming APIs**

<iframe width="100%" height="400" style="max-width:720px;aspect-ratio:16/9;height:auto;" src="https://www.youtube.com/embed/93vD542VUXw" title="Video walkthrough" frameborder="0" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share" allowfullscreen></iframe>

**Part 2 — Building APIs**

<iframe width="100%" height="400" style="max-width:720px;aspect-ratio:16/9;height:auto;" src="https://www.youtube.com/embed/OdcDezY1218" title="Video walkthrough" frameborder="0" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share" allowfullscreen></iframe>

## Part 1 · Consuming APIs

Level 2's weather project used `requests` briefly. This module covers the
`requests` library properly: authentication, pagination, timeouts, retries,
and turning HTTP failures into clear, handled errors instead of crashes.

### Installing requests

```bash
pip install requests
```

### Basic GET requests

```python
import requests

response = requests.get("https://api.github.com/users/python")
print(response.status_code)   # 200
data = response.json()
print(data["name"], data["public_repos"])
```

### Always set a timeout

Without a timeout, a hung server can block your program forever.

```python
try:
    response = requests.get("https://api.github.com/users/python", timeout=5)
except requests.exceptions.Timeout:
    print("the request took too long")
```

### Checking for errors

```python
response = requests.get("https://api.github.com/users/this-user-does-not-exist-xyz")

print(response.status_code)   # 404

try:
    response.raise_for_status()   # raises requests.HTTPError for 4xx/5xx status codes
except requests.HTTPError as e:
    print(f"request failed: {e}")
```

### Query parameters and headers

```python
response = requests.get(
    "https://api.github.com/search/repositories",
    params={"q": "language:python stars:>10000", "sort": "stars"},
    headers={"Accept": "application/vnd.github+json"},
)
data = response.json()
print(data["total_count"])
```

`params=` handles URL-encoding for you — never hand-build query strings by
concatenating them yourself.

### Authentication

```python
# API key in a header (very common pattern)
response = requests.get(
    "https://api.example.com/account",
    headers={"Authorization": "Bearer YOUR_API_TOKEN_HERE"},
)

# HTTP Basic Auth
response = requests.get(
    "https://api.example.com/secure",
    auth=("username", "password"),
)
```

Never hard-code real tokens/passwords into source files — read them from
environment variables instead.

```python
import os
import requests

token = os.environ.get("API_TOKEN")
if not token:
    raise RuntimeError("API_TOKEN environment variable is not set")

response = requests.get(
    "https://api.example.com/account",
    headers={"Authorization": f"Bearer {token}"},
)
```

### POST, PUT, DELETE

```python
# POST with a JSON body
response = requests.post(
    "https://api.example.com/tasks",
    json={"title": "Write docs", "done": False},
)
created = response.json()

# PUT to fully replace a resource
requests.put(f"https://api.example.com/tasks/{created['id']}", json={"title": "Write docs", "done": True})

# DELETE
requests.delete(f"https://api.example.com/tasks/{created['id']}")
```

`json=` automatically serializes the dict and sets the
`Content-Type: application/json` header — you rarely need to call
`json.dumps` yourself when using `requests`.

### Handling pagination

Many APIs return results a page at a time, with a link or token to the next
page.

```python
def fetch_all_pages(base_url, params=None):
    """Follow 'next' links until the API stops returning one."""
    results = []
    url = base_url
    params = dict(params or {})

    while url:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        payload = response.json()

        results.extend(payload["items"])
        next_url = payload.get("next")   # API-specific: some use a URL, others a page number/token
        url = next_url
        params = None   # the next URL already carries its own query string

    return results
```

A simpler pattern many APIs use instead is a `page` query parameter that you
increment until an empty page comes back:

```python
def fetch_all_by_page_number(base_url):
    results = []
    page = 1
    while True:
        response = requests.get(base_url, params={"page": page}, timeout=10)
        response.raise_for_status()
        batch = response.json()
        if not batch:
            break
        results.extend(batch)
        page += 1
    return results
```

### Retrying transient failures

```python
import time
import requests

def get_with_retry(url, max_attempts=3, backoff=0.5):
    for attempt in range(1, max_attempts + 1):
        try:
            response = requests.get(url, timeout=5)
            response.raise_for_status()
            return response
        except (requests.ConnectionError, requests.Timeout, requests.HTTPError) as e:
            if attempt == max_attempts:
                raise
            print(f"attempt {attempt} failed ({e}), retrying...")
            time.sleep(backoff * attempt)   # simple linear backoff
```

For production code, `requests` also supports a built-in retry mechanism via
`urllib3.util.Retry` and a `HTTPAdapter`, which handles this more robustly than
a hand-rolled loop.

```python
from requests.adapters import HTTPAdapter
from urllib3.util import Retry

session = requests.Session()
retry_strategy = Retry(total=3, backoff_factor=0.5, status_forcelist=[500, 502, 503, 504])
session.mount("https://", HTTPAdapter(max_retries=retry_strategy))

response = session.get("https://api.example.com/data", timeout=5)
```

### Wrapping API errors in your own exception

```python
class APIClientError(Exception):
    """Raised when the API returns an error or is unreachable."""


def safe_get_json(url, **kwargs):
    try:
        response = requests.get(url, timeout=kwargs.pop("timeout", 10), **kwargs)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        raise APIClientError(f"request to {url} failed: {e}") from e
    except ValueError as e:
        raise APIClientError(f"invalid JSON from {url}: {e}") from e
```

### Cheat sheet

| Task | Code |
|------|------|
| GET with query params | `requests.get(url, params={...}, timeout=10)` |
| POST JSON body | `requests.post(url, json={...})` |
| Check for HTTP errors | `response.raise_for_status()` |
| Reusable session + retries | `requests.Session()` + `HTTPAdapter` |
| Read a secret safely | `os.environ.get("API_TOKEN")` |

### How It Actually Works

`requests.get(url)` sits on top of `urllib3`, which manages a **connection pool**:
opening a TCP socket and completing a TLS handshake is expensive (multiple network
round trips), so a `requests.Session()` keeps underlying connections open and reuses
them for subsequent requests to the same host — this is why the docs recommend a
`Session` for repeated calls to the same API rather than bare `requests.get`, which
creates and tears down a fresh connection pool adapter every call.

`timeout=5` doesn't limit total request time as a single wall-clock deadline the way
it might sound — under the hood it's implemented as two separate socket-level
timeouts: a **connect timeout** (how long to wait for the TCP handshake) and a
**read timeout** (how long to wait between receiving chunks of the response body
once connected). Without it, the underlying socket's `recv()` call blocks
indefinitely if the server accepts the connection but never sends data — a
deliberately slow or hung server can otherwise freeze your program forever, since
nothing in the OS or Python enforces a default timeout on a socket read.

`response.raise_for_status()` works by checking `self.status_code` against ranges
(anything ≥ 400) and constructing an `HTTPError` only then — the HTTP response
itself already arrived successfully at the transport level (TCP/TLS completed fine,
bytes were received); "success" or "failure" is purely an application-level status
code the server chose to send, which is exactly why `raise_for_status()` is a
separate, optional call rather than something that happens automatically: a 404
isn't a network failure, it's valid HTTP that your code has to decide how to
interpret.

`json=` on a POST works by JSON-encoding your dict with `json.dumps` (the same
mechanism from Module 5) and setting the `Content-Type: application/json` header
before the request line is ever sent — this is purely a client-side convenience
built on top of the same body/headers that `requests.post(..., data=..., headers=...)`
would let you set manually. `Retry`/`HTTPAdapter` intercept requests at the
connection-pool level below `requests` itself: when a request fails or returns a
listed status code, `urllib3` catches it, computes a delay using the configured
backoff formula, and re-sends the *exact same* prepared request over the pool's
connection — the retry logic lives below the point where `requests`'s own API even
sees the failure, which is why it applies uniformly to `get`, `post`, and every other
method through one shared adapter.

### Exercise

Write a small client `github_client.py` with a function
`list_public_repos(username)` that calls GitHub's public API
(`https://api.github.com/users/{username}/repos`), follows pagination via the
`page` query parameter, raises a custom `GitHubClientError` on any HTTP or
network failure, and returns a list of `(name, stars)` tuples sorted by star
count descending. Write it with a timeout and `raise_for_status()`, and add a
`requests.Session()` with retries for transient failures.

## Part 2 · Building APIs (FastAPI)

So far you've been a client of other people's APIs. This module flips that:
building your own web API with **FastAPI**, a modern framework built on type
hints, automatic request validation via Pydantic, and automatically generated
interactive documentation.

### Installing FastAPI

```bash
pip install fastapi uvicorn
```

`uvicorn` is the ASGI server that actually runs a FastAPI application.

### A minimal API

```python
# main.py
from fastapi import FastAPI

app = FastAPI(title="Task API")


@app.get("/")
def root():
    return {"message": "Task API is running"}


@app.get("/health")
def health_check():
    return {"status": "ok"}
```

```bash
uvicorn main:app --reload
# visit http://127.0.0.1:8000/         -> {"message": "Task API is running"}
# visit http://127.0.0.1:8000/docs     -> interactive Swagger UI, generated automatically
```

### Path and query parameters

FastAPI reads Python type hints to validate and convert incoming data
automatically.

```python
from fastapi import FastAPI

app = FastAPI()

tasks = {1: "Write docs", 2: "Review PR"}


@app.get("/tasks/{task_id}")
def get_task(task_id: int):          # FastAPI converts the URL segment to int, or 422s
    return {"task_id": task_id, "title": tasks.get(task_id)}


@app.get("/tasks")
def list_tasks(limit: int = 10, done: bool | None = None):
    # limit and done are optional query params: /tasks?limit=5&done=true
    return {"limit": limit, "done_filter": done}
```

Visiting `/tasks/abc` (a non-integer) automatically returns a `422 Unprocessable
Entity` response with a clear validation error — no manual checking required.

### Request bodies with Pydantic models

Pydantic models define the *shape* of data you expect, and FastAPI validates
incoming JSON against them automatically.

```python
from fastapi import FastAPI
from pydantic import BaseModel, Field

app = FastAPI()


class TaskCreate(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    done: bool = False


class TaskOut(BaseModel):
    id: int
    title: str
    done: bool


tasks_db: dict[int, TaskOut] = {}
next_id = 1


@app.post("/tasks", response_model=TaskOut, status_code=201)
def create_task(task: TaskCreate):
    global next_id
    new_task = TaskOut(id=next_id, title=task.title, done=task.done)
    tasks_db[next_id] = new_task
    next_id += 1
    return new_task
```

If the client sends `{"title": ""}` (violating `min_length=1`), FastAPI
rejects it with a `422` response describing exactly which field failed and
why — before your function body ever runs.

### Full CRUD example

```python
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI(title="Task API")


class TaskCreate(BaseModel):
    title: str
    done: bool = False


class TaskUpdate(BaseModel):
    title: str | None = None
    done: bool | None = None


class TaskOut(BaseModel):
    id: int
    title: str
    done: bool


tasks_db: dict[int, TaskOut] = {}
next_id = 1


@app.post("/tasks", response_model=TaskOut, status_code=201)
def create_task(task: TaskCreate):
    global next_id
    new_task = TaskOut(id=next_id, **task.model_dump())
    tasks_db[next_id] = new_task
    next_id += 1
    return new_task


@app.get("/tasks", response_model=list[TaskOut])
def list_tasks():
    return list(tasks_db.values())


@app.get("/tasks/{task_id}", response_model=TaskOut)
def get_task(task_id: int):
    task = tasks_db.get(task_id)
    if task is None:
        raise HTTPException(status_code=404, detail="task not found")
    return task


@app.patch("/tasks/{task_id}", response_model=TaskOut)
def update_task(task_id: int, patch: TaskUpdate):
    task = tasks_db.get(task_id)
    if task is None:
        raise HTTPException(status_code=404, detail="task not found")
    updated_data = task.model_dump()
    updated_data.update({k: v for k, v in patch.model_dump().items() if v is not None})
    updated_task = TaskOut(**updated_data)
    tasks_db[task_id] = updated_task
    return updated_task


@app.delete("/tasks/{task_id}", status_code=204)
def delete_task(task_id: int):
    if task_id not in tasks_db:
        raise HTTPException(status_code=404, detail="task not found")
    del tasks_db[task_id]
```

`HTTPException` is FastAPI's way of returning a specific HTTP status code and
error body from inside a route — raising it works like any other exception,
but FastAPI catches it and turns it into the right response.

### Dependency injection

FastAPI's `Depends` lets you share setup logic (like "get the current user" or
"get a database session") across multiple routes cleanly.

```python
from fastapi import Depends, FastAPI

app = FastAPI()


def get_query_token(token: str | None = None):
    if token != "secret-token":
        from fastapi import HTTPException
        raise HTTPException(status_code=401, detail="invalid or missing token")
    return token


@app.get("/protected")
def protected_route(token: str = Depends(get_query_token)):
    return {"message": "you're in", "token": token}
```

### Testing a FastAPI app

FastAPI's own `TestClient` makes it easy to exercise routes without running a
real server.

```python
# test_main.py
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


def test_create_and_get_task():
    response = client.post("/tasks", json={"title": "Test task"})
    assert response.status_code == 201
    task_id = response.json()["id"]

    response = client.get(f"/tasks/{task_id}")
    assert response.status_code == 200
    assert response.json()["title"] == "Test task"


def test_get_missing_task_returns_404():
    response = client.get("/tasks/9999")
    assert response.status_code == 404
```

### Cheat sheet

| Concept | Syntax |
|---------|--------|
| Path parameter | `def route(item_id: int):` with `@app.get("/items/{item_id}")` |
| Query parameter | plain function argument with a default value |
| Request body | a `BaseModel` subclass as a function argument |
| Response shape | `response_model=` on the route decorator |
| Error response | `raise HTTPException(status_code=..., detail=...)` |
| Shared logic | `Depends(dependency_function)` |

### How It Actually Works

`def get_task(task_id: int):` validating and converting the URL segment isn't
FastAPI reading your mind about intent — at import time, FastAPI inspects each route
function's **signature** using Python's `inspect`/`typing` machinery (the same
runtime introspection `functools.wraps` relies on) and, for every parameter, builds
a corresponding Pydantic field from its type annotation. When a request for
`/tasks/abc` arrives, FastAPI extracts the raw string `"abc"` from the URL path,
hands it to Pydantic's validator for `int`, which fails to coerce it and raises a
structured validation error — FastAPI catches that specific exception type and
converts it into the `422` JSON response, all before your function body executes at
all; a matching request for `/tasks/7` goes through the same coercion but succeeds,
so `task_id` arrives inside your function already as a real Python `int`, not a
string you'd have to convert yourself.

A `BaseModel` subclass like `TaskCreate` is not just documentation — Pydantic
generates, once per model class (via `__init_subclass__`/metaclass hooks and a
compiled validator, precompiled to Rust in Pydantic v2 for speed), a fast validation
routine covering every field. When a request body arrives, FastAPI reads the raw
bytes, decodes them as JSON (using the same recursive parsing you saw in Module 5),
and passes the resulting dict through that compiled validator — a violated
constraint like `min_length=1` fails during that single pass and never reaches
`create_task`'s body, which is why routes can assume validated input rather than
manually checking `if not task.title: raise ...` everywhere.

`Depends(get_query_token)` implements dependency injection through the same
signature-introspection mechanism as request bodies: FastAPI sees the parameter's
default is a `Depends(...)` marker, calls `get_query_token` itself (passing along any
of *its* declared parameters, resolved recursively — dependencies can depend on
other dependencies), and substitutes the return value as the argument to your route
function. If `get_query_token` raises `HTTPException`, FastAPI's own exception
handling middleware — installed automatically around every route — catches it and
converts it directly into an HTTP response with that status code and detail message,
short-circuiting before your route body ever runs, exactly like the type-validation
path above.

`uvicorn` and FastAPI communicate through the **ASGI** interface: uvicorn is
responsible for the raw TCP/HTTP protocol parsing and turns each incoming connection
into a Python coroutine call following that standard interface, which is why FastAPI
route handlers can be either plain `def` functions (uvicorn runs them in a thread
pool to avoid blocking the event loop) or `async def` (run directly on the event
loop) — the framework layer is decoupled from the network layer specifically so
either style of handler works.

### Exercise

Extend the CRUD example above with a `priority: str` field on `TaskCreate`
(one of `"low"`, `"medium"`, `"high"`, validated with a Pydantic
`Field`/`Literal`), a `GET /tasks?priority=high` filter using a query
parameter, and a `TestClient`-based test file covering create, list-with-filter,
update, and delete-then-404.
