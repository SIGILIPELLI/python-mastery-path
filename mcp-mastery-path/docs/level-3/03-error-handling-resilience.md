---
description: "A JSON-RPC error has a numeric code, not a type — code -32601 always means 'method not found' regardless of which server sent it, which is exactly what makes generic retry logic possible."
---

# 03 · Error Handling & Resilience Patterns

Up to now every tool call in this course has succeeded. In a multi-server
setup running for real, that stops being true: a server times out, a
network blip drops a remote connection, a tool call fails because the
underlying GitHub API rate-limited you. This lesson covers how MCP
represents failure on the wire, and how to build a client that survives it.

## The JSON-RPC error object

Every JSON-RPC error response has the same three fields, and MCP inherits
them unchanged:

```json
{
  "jsonrpc": "2.0",
  "id": 42,
  "error": {
    "code": -32601,
    "message": "Method not found",
    "data": {"method": "tools/cal"}
  }
}
```

`code` is a signed integer, `message` is a short human-readable string, and
`data` is optional, free-form extra detail. JSON-RPC 2.0 reserves a block of
standard codes:

| Code | Meaning |
|------|---------|
| `-32700` | Parse error — invalid JSON was sent |
| `-32600` | Invalid Request — well-formed JSON, but not a valid JSON-RPC request |
| `-32601` | Method not found |
| `-32602` | Invalid params |
| `-32603` | Internal error |

MCP uses these for protocol-level failures (you called a method that
doesn't exist, or sent malformed params) and layers its own, tool-specific
failure signal on top for a different case: a tool that ran but the
*operation itself* failed (e.g. "that file doesn't exist"). That case isn't
a JSON-RPC error at all — it's a normal, successful `tools/call` response
with `isError: true` on the result content:

```json
{
  "jsonrpc": "2.0",
  "id": 43,
  "result": {
    "content": [{"type": "text", "text": "File not found: notes/missing.md"}],
    "isError": true
  }
}
```

That distinction matters for how you write client code: a JSON-RPC-level
error means something is wrong with the *protocol exchange itself*
(connection, method, parameters) and is usually worth retrying or
surfacing as a system error. An `isError: true` tool result means the tool
ran correctly and is reporting that the *requested operation* failed — the
model should see that message and decide what to do next, not have your
client swallow it as a crash.

```python
async def call_tool_distinguishing_errors(session, tool_name, arguments):
    try:
        result = await session.call_tool(tool_name, arguments)
    except Exception as e:
        # protocol-level failure: connection dropped, method not found, etc.
        return {"kind": "protocol_error", "detail": str(e)}

    if result.isError:
        # the tool ran, but the operation it represents failed
        return {"kind": "tool_error", "detail": result.content}

    return {"kind": "success", "detail": result.content}
```

## How It Actually Works: what's safely retryable

Not every failure deserves the same response, and blindly retrying
everything is its own bug (retrying a non-idempotent "create issue" call on
a timeout can create the issue twice). A practical classification:

1. **Transport-level connection failures** (the subprocess died, the HTTP
   connection reset) are usually safe to retry *the connection*, not
   necessarily the in-flight call — you often can't tell if the server
   received and processed the request before the connection dropped.
2. **`-32601` Method not found / `-32602` Invalid params** are never worth
   retrying as-is — the request itself is wrong, and retrying it unchanged
   will fail identically every time. Fix the request or don't send it.
3. **`-32603` Internal error** *might* be transient (the server hit a bug
   under specific, maybe-momentary conditions) — a single retry with a
   short backoff is reasonable, but don't retry indefinitely.
4. **`isError: true` tool results** are not retryable by your client code
   at all in the generic case — "file not found" won't become "file found"
   on a second attempt. These should flow back to the model, which can
   decide to try a different approach.
5. **Idempotency is the real gate on whether to retry anything.** A
   read-only tool (`list_issues`) is safe to retry freely. A write tool
   (`create_issue`) is only safe to retry if the server supports an
   idempotency key or you can detect duplicates after the fact.

## Timeouts and backoff

```python
import asyncio

async def call_with_retry(session, tool_name, arguments, max_attempts=3, timeout=10.0):
    last_error = None
    for attempt in range(max_attempts):
        try:
            return await asyncio.wait_for(
                session.call_tool(tool_name, arguments), timeout=timeout
            )
        except asyncio.TimeoutError as e:
            last_error = e
        except Exception as e:
            # don't retry protocol errors that won't change on retry
            if "Method not found" in str(e) or "Invalid params" in str(e):
                raise
            last_error = e
        await asyncio.sleep(2 ** attempt)  # 1s, 2s, 4s backoff
    raise last_error
```

This only retries timeouts and unclassified exceptions — a method-not-found
or invalid-params error is re-raised immediately rather than wasting three
attempts on a request that can't succeed.

## Graceful degradation when a server disappears

In a multi-server client, one dead server shouldn't take down the others.
Wrap per-server operations so a failure in one is contained:

```python
async def list_all_tools_resilient(client) -> dict:
    catalog = {}
    for server_name, session in list(client.sessions.items()):
        try:
            result = await asyncio.wait_for(session.list_tools(), timeout=5.0)
            catalog[server_name] = result.tools
        except Exception as e:
            print(f"Server {server_name} unavailable, skipping: {e}")
            catalog[server_name] = []  # degrade, don't crash the whole catalog build
    return catalog
```

A user losing access to the GitHub server mid-session because of a network
blip should mean "GitHub tools are temporarily unavailable," not "the
entire assistant stopped working."

## Exercise

Add a `call_with_retry`-style wrapper to the `MultiServerClient` from
lesson 1 that: retries transport timeouts up to 3 times with exponential
backoff, never retries `-32601`/`-32602` errors, and returns a tagged
`{"kind": ..., "detail": ...}` dict like the one above for every outcome
(success, tool_error, protocol_error) so calling code never has to guard
against an unhandled exception leaking out of a tool call.
