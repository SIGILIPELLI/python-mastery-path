---
description: "Caching a tool result by its arguments only works if the tool is a pure function of those arguments — cache list_issues(repo='x') and you'll serve stale data the moment someone files a new issue."
---

# 08 · Caching & Rate Limiting Tool Calls

A tool backed by an external API (GitHub, a search provider, anything with
its own quota) has two practical problems once it's used for real: repeated
identical calls waste latency and money, and enough traffic will eventually
hit the provider's rate limit and start failing. This lesson covers both,
and the one precondition that makes caching safe at all.

## The precondition: only cache idempotent, read-only calls

Caching a `create_issue` call is a bug, not an optimization — the second
identical-looking call is a *different* request (the user wants a second
issue, or a retry after a timeout where you can't be sure the first one
landed). Caching only makes sense for calls that are safe to skip
re-executing because the result is a pure function of the inputs, at least
for some reasonable window of time: `get_issue(repo, number)`,
`list_issues(repo)`, a `search` tool.

```python
from functools import wraps
import time
import hashlib
import json

class ToolCache:
    def __init__(self, ttl_seconds: float = 60.0):
        self.ttl = ttl_seconds
        self._store: dict[str, tuple[float, object]] = {}

    def _key(self, tool_name: str, arguments: dict) -> str:
        # stable key: sorted JSON so {"a": 1, "b": 2} and {"b": 2, "a": 1} hit the same entry
        payload = json.dumps(arguments, sort_keys=True)
        return hashlib.sha256(f"{tool_name}:{payload}".encode()).hexdigest()

    def get(self, tool_name: str, arguments: dict):
        key = self._key(tool_name, arguments)
        entry = self._store.get(key)
        if entry is None:
            return None
        timestamp, value = entry
        if time.monotonic() - timestamp > self.ttl:
            del self._store[key]
            return None
        return value

    def set(self, tool_name: str, arguments: dict, value):
        key = self._key(tool_name, arguments)
        self._store[key] = (time.monotonic(), value)
```

Wiring it in at the call site, with an explicit allow-list of cacheable
tools rather than caching by default:

```python
CACHEABLE_TOOLS = {"list_issues", "get_issue", "search"}
cache = ToolCache(ttl_seconds=30.0)

async def call_tool_cached(session, tool_name: str, arguments: dict):
    if tool_name in CACHEABLE_TOOLS:
        cached = cache.get(tool_name, arguments)
        if cached is not None:
            return cached

    result = await session.call_tool(tool_name, arguments)

    if tool_name in CACHEABLE_TOOLS:
        cache.set(tool_name, arguments, result)
    return result
```

The explicit allow-list matters as much as the cache logic itself — it's
the thing that keeps a future `create_issue` or `delete_file` tool from
accidentally getting cached just because someone forgot to think about it.

## Choosing a TTL

There's no universal right answer — it's a tradeoff between staleness and
load, specific to what the data represents. A 30-second TTL on `list_issues`
means a user who just filed an issue might not see it reflected for up to
30 seconds if they immediately re-query; that's usually an acceptable
tradeoff for cutting repeated-call load during an active conversation. Data
that's genuinely static (a resource describing a fixed config, a schema
definition) can reasonably cache for much longer. Data where staleness
actively misleads the user (account balance, real-time status) often
shouldn't be cached at all, or only for a few seconds.

## Rate limiting

Caching reduces redundant calls; rate limiting bounds how fast new,
non-cached calls are allowed to go out, which matters for staying under an
upstream API's quota and avoiding a cascade of failures when you hit it.

```python
import asyncio
import time

class TokenBucketLimiter:
    """Allows `rate` calls per second, with a short burst allowance."""
    def __init__(self, rate: float, burst: int):
        self.rate = rate
        self.tokens = burst
        self.max_tokens = burst
        self.last_refill = time.monotonic()
        self._lock = asyncio.Lock()

    async def acquire(self):
        async with self._lock:
            now = time.monotonic()
            elapsed = now - self.last_refill
            self.tokens = min(self.max_tokens, self.tokens + elapsed * self.rate)
            self.last_refill = now

            if self.tokens < 1:
                wait = (1 - self.tokens) / self.rate
                await asyncio.sleep(wait)
                self.tokens = 0
            else:
                self.tokens -= 1

github_limiter = TokenBucketLimiter(rate=1.0, burst=5)  # ~1/sec sustained, bursts of 5

async def call_github_tool(session, tool_name, arguments):
    await github_limiter.acquire()
    return await session.call_tool(tool_name, arguments)
```

A token bucket is the right shape for this problem specifically because
real usage is bursty — a model might want to call `get_issue` five times in
quick succession while gathering context, then go quiet for a while. A
naive "max N calls per second, hard stop" limiter penalizes that normal
burst pattern; a token bucket absorbs it up to the burst size, then
throttles to the sustained rate.

## Respecting the upstream API's own rate-limit signals

Most real APIs tell you how close you are to their limit — use that signal
instead of guessing at your own rate independently of it:

```python
async def github_api_call_aware(repo, endpoint, token):
    response = await http_client.get(f"https://api.github.com/repos/{repo}/{endpoint}",
                                       headers={"Authorization": f"Bearer {token}"})
    remaining = int(response.headers.get("X-RateLimit-Remaining", "1"))
    if remaining < 5:
        reset_at = int(response.headers.get("X-RateLimit-Reset", "0"))
        wait = max(0, reset_at - time.time())
        print(f"Approaching GitHub rate limit, backing off {wait:.0f}s")
    return response.json()
```

A fixed local rate limit is a reasonable default guess; the API's own
headers are ground truth and should take priority when available.

## Exercise

Combine `ToolCache` and `TokenBucketLimiter` into one wrapper function
`call_tool_managed(session, tool_name, arguments)` that checks the cache
first, acquires a rate-limit token only on a cache miss, and populates the
cache after a successful cacheable call. Test it against a mock tool that
sleeps briefly (simulating network latency) and confirm that repeated
identical calls within the TTL return instantly from cache while a burst of
6+ distinct calls gets visibly throttled by the limiter.
