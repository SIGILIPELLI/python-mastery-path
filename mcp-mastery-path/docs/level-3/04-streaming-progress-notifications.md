---
description: "Progress notifications carry a progressToken the client chose up front — the server never invents its own identifier, it just echoes back whatever token arrived in the original request."
---

# 04 · Streaming Responses & Progress Notifications

A tool call that finishes in 200ms doesn't need progress reporting. A tool
that crawls 500 web pages, re-indexes a large codebase, or runs a slow
batch job does — both so the user isn't staring at a frozen UI, and so they
have a way to cancel it. MCP has first-class support for both: progress
notifications and cancellation.

## Requesting progress updates

Progress reporting is opt-in per request. The client attaches a
`progressToken` to the request's metadata when it wants updates:

```python
import uuid

async def call_long_tool_with_progress(session, tool_name, arguments):
    token = str(uuid.uuid4())
    # the Python SDK exposes this via the session's request metadata;
    # conceptually, you're attaching: {"_meta": {"progressToken": token}}
    result = await session.call_tool(
        tool_name, arguments, progress_token=token
    )
    return result
```

That token is the whole mechanism — the server doesn't generate its own
progress identifier, it just echoes back whatever token the client sent, so
the client can correlate incoming progress notifications with the specific
call that's in flight.

## Emitting progress from a server

On the server side, inside a tool handler, you report progress against that
same token via `notifications/progress`:

```python
from mcp.server.fastmcp import FastMCP, Context

mcp = FastMCP("crawler-server")

@mcp.tool()
async def crawl_site(urls: list[str], ctx: Context) -> str:
    """Crawl a list of URLs, reporting progress as each one completes."""
    total = len(urls)
    for i, url in enumerate(urls):
        await fetch_and_index(url)  # your actual work
        await ctx.report_progress(progress=i + 1, total=total)
    return f"Crawled {total} URLs"
```

`ctx.report_progress` sends a `notifications/progress` message carrying the
token the client originally attached, plus `progress` and `total`. Because
it's a *notification* (no `id`, no response expected — the distinction from
lesson 2 of this level), it doesn't block the eventual `tools/call`
response; it's a side channel of updates that arrive while the call is
still in flight.

## Handling progress on the client

```python
async def call_with_progress_handler(session, tool_name, arguments, on_progress):
    token = str(uuid.uuid4())

    def progress_callback(progress: float, total: float | None, message: str | None):
        on_progress(progress, total, message)

    result = await session.call_tool(
        tool_name, arguments,
        progress_token=token,
        progress_callback=progress_callback,
    )
    return result

# usage
async def print_progress(progress, total, message):
    pct = f"{progress}/{total}" if total else str(progress)
    print(f"[{pct}] {message or ''}")

await call_with_progress_handler(session, "crawl_site", {"urls": urls}, print_progress)
```

The exact SDK call signature for wiring a progress callback can differ
slightly between SDK versions — check your installed version's docs for the
precise parameter name — but the protocol-level shape is fixed: a
`progressToken` goes out with the request, and zero or more
`notifications/progress` messages carrying that same token come back before
the final result.

## Cancellation

The companion primitive is `notifications/cancelled` — the client tells the
server to stop working on a specific in-flight request:

```python
async def cancel_request(session, request_id):
    await session.send_notification(
        "notifications/cancelled",
        {"requestId": request_id, "reason": "user cancelled"},
    )
```

On the server side, a long-running tool should check for cancellation
periodically rather than running to completion regardless:

```python
@mcp.tool()
async def crawl_site_cancellable(urls: list[str], ctx: Context) -> str:
    total = len(urls)
    for i, url in enumerate(urls):
        if ctx.is_cancelled():  # check between units of work, not mid-fetch
            return f"Cancelled after {i}/{total} URLs"
        await fetch_and_index(url)
        await ctx.report_progress(progress=i + 1, total=total)
    return f"Crawled {total} URLs"
```

Cancellation is a *request*, not a guarantee — a server that's deep inside a
single blocking operation (a single huge file write, a synchronous network
call) can't interrupt itself mid-operation unless that operation is itself
cancellable. The practical pattern is: do cancellable work in small
checkable units (one URL, one file, one row) and check between them, the
same way the progress-reporting example already structures its loop.

## Exercise

Add progress reporting to the `crawl_site` tool so it also reports a
human-readable `message` alongside the numeric progress (e.g. "Fetching
https://example.com (3/10)"), and add cancellation support so that calling
`cancel_request` from the client stops the crawl after the URL currently in
flight rather than running to completion. Verify by starting a crawl of 10
slow URLs and cancelling after the 3rd progress update arrives.
