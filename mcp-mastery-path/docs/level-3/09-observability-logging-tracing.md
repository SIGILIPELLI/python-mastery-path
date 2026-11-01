---
description: "For a stdio server, logging to stdout isn't just bad practice — it silently corrupts the JSON-RPC message stream, so every observability example in this lesson writes to stderr instead."
---

# 09 · Observability: Logging & Tracing MCP Calls

Once you're running several servers behind retries, caching, and
confirmation gates, "it isn't working" stops being something you can debug
by reading code — you need to see what actually happened across every layer
of a real request. This lesson covers structured logging and the bare
minimum of tracing needed to answer "which server, which tool, how long,
what went wrong" after the fact.

## The stdout rule, again, because it matters here specifically

Level 1 covered this as a gotcha; it's worth restating because
observability code is exactly where it tends to slip back in. A stdio
server's stdout carries the JSON-RPC protocol stream — every `print()`
statement you add for debugging corrupts it. Every example below logs to
`stderr` or a proper logging handler, never `print()`:

```python
import logging
import sys

logging.basicConfig(
    stream=sys.stderr,
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)
logger = logging.getLogger("mcp-server")
```

## Structured logging of every tool call

Free-text log lines are fine for a human staring at a terminal; they're
painful to query once you have more than a handful of log entries. Log
structured fields instead — even a simple JSON line per event is enough to
grep, filter, and eventually feed into a real log aggregator:

```python
import json
import time
from mcp.server.fastmcp import FastMCP, Context

mcp = FastMCP("github-server")

def log_event(event: str, **fields):
    logger.info(json.dumps({"event": event, "ts": time.time(), **fields}))

@mcp.tool()
async def list_issues(repo: str, ctx: Context) -> list[dict]:
    start = time.monotonic()
    log_event("tool_call_start", tool="list_issues", repo=repo)
    try:
        result = await fetch_issues(repo)
        log_event("tool_call_success", tool="list_issues", repo=repo,
                   duration_ms=round((time.monotonic() - start) * 1000), count=len(result))
        return result
    except Exception as e:
        log_event("tool_call_error", tool="list_issues", repo=repo,
                   duration_ms=round((time.monotonic() - start) * 1000), error=str(e))
        raise
```

The three events — start, success (with duration and a size/count signal),
error (with the actual exception) — are the minimum set that lets you
answer "is this tool slow," "is this tool failing," and "how often is it
even being called," purely from log lines, without attaching a debugger.

## Correlating a request across client and server

A single user turn can fan out into several tool calls across several
servers. Without a shared identifier, correlating "which of these five log
lines across three processes belong to the same user request" is
guesswork. Generate a request ID on the client side and thread it through:

```python
import contextvars
import uuid

request_id_var = contextvars.ContextVar("request_id", default=None)

async def call_tool_traced(session, tool_name, arguments):
    request_id = str(uuid.uuid4())
    request_id_var.set(request_id)
    # MCP's _meta field on requests is the standard place to carry this kind
    # of cross-cutting context without it being treated as a tool argument
    result = await session.call_tool(
        tool_name, arguments, meta={"requestId": request_id}
    )
    return result
```

On the server, pull it back out of the request metadata and include it in
every log line for that call:

```python
@mcp.tool()
async def list_issues(repo: str, ctx: Context) -> list[dict]:
    request_id = ctx.request_meta.get("requestId", "unknown")
    log_event("tool_call_start", tool="list_issues", repo=repo, request_id=request_id)
    ...
```

Now `grep request_id` across every server's logs reconstructs the full
fan-out for one user turn, even when the tool calls landed on different
processes.

## A minimal tracing setup

Full distributed tracing (OpenTelemetry spans, a trace backend like Jaeger)
is the production-grade version of this, and is worth adopting once you
have more than a couple of servers — but the core idea is simple enough to
build a minimal version of yourself first, to understand what a tracing
backend is actually doing for you:

```python
class Span:
    def __init__(self, name: str, request_id: str, parent: "Span | None" = None):
        self.name = name
        self.request_id = request_id
        self.parent = parent
        self.start = time.monotonic()
        self.end: float | None = None

    def finish(self):
        self.end = time.monotonic()
        log_event("span", name=self.name, request_id=self.request_id,
                   duration_ms=round((self.end - self.start) * 1000),
                   parent=self.parent.name if self.parent else None)

async def traced_tool_call(session, tool_name, arguments, request_id, parent_span=None):
    span = Span(f"tool_call:{tool_name}", request_id, parent_span)
    try:
        return await session.call_tool(tool_name, arguments, meta={"requestId": request_id})
    finally:
        span.finish()
```

A real tracing backend adds sampling, proper span context propagation
across process boundaries, and a UI for visualizing the resulting tree —
but the fundamental unit, a named span with a start, an end, a parent, and
a shared request ID, is exactly what the toy version above captures.

## Exercise

Wire the `log_event` structured logging into the `MultiServerClient` from
lesson 1, so every call routed through it logs `tool_call_start`,
`tool_call_success`/`tool_call_error`, and includes a request ID generated
once per user-facing call and threaded through every underlying tool call
it fans out to (even when one user action triggers calls to two different
servers). Confirm, by grepping the resulting log output, that you can
reconstruct the full set of tool calls belonging to a single multi-server
request.
