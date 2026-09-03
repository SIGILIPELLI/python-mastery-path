# 07 · Consuming APIs

Level 2's weather project used `requests` briefly. This module covers the
`requests` library properly: authentication, pagination, timeouts, retries,
and turning HTTP failures into clear, handled errors instead of crashes.

## Installing requests

```bash
pip install requests
```

## Basic GET requests

```python
import requests

response = requests.get("https://api.github.com/users/python")
print(response.status_code)   # 200
data = response.json()
print(data["name"], data["public_repos"])
```

## Always set a timeout

Without a timeout, a hung server can block your program forever.

```python
try:
    response = requests.get("https://api.github.com/users/python", timeout=5)
except requests.exceptions.Timeout:
    print("the request took too long")
```

## Checking for errors

```python
response = requests.get("https://api.github.com/users/this-user-does-not-exist-xyz")

print(response.status_code)   # 404

try:
    response.raise_for_status()   # raises requests.HTTPError for 4xx/5xx status codes
except requests.HTTPError as e:
    print(f"request failed: {e}")
```

## Query parameters and headers

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

## Authentication

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

## POST, PUT, DELETE

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

## Handling pagination

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

## Retrying transient failures

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

## Wrapping API errors in your own exception

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

## Cheat sheet

| Task | Code |
|------|------|
| GET with query params | `requests.get(url, params={...}, timeout=10)` |
| POST JSON body | `requests.post(url, json={...})` |
| Check for HTTP errors | `response.raise_for_status()` |
| Reusable session + retries | `requests.Session()` + `HTTPAdapter` |
| Read a secret safely | `os.environ.get("API_TOKEN")` |

## How It Actually Works

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

## Exercise

Write a small client `github_client.py` with a function
`list_public_repos(username)` that calls GitHub's public API
(`https://api.github.com/users/{username}/repos`), follows pagination via the
`page` query parameter, raises a custom `GitHubClientError` on any HTTP or
network failure, and returns a list of `(name, stars)` tuples sorted by star
count descending. Write it with a timeout and `raise_for_status()`, and add a
`requests.Session()` with retries for transient failures.
