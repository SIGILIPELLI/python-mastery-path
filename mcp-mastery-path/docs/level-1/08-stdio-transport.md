---
description: "A stdio server must never print to stdout — anything other than newline-delimited JSON-RPC messages there corrupts the protocol stream and breaks the connection."
---

# 08 · The stdio Transport & Local Servers

## How stdio transport actually works

When a host connects to a local MCP server, it doesn't open a network
socket — it **spawns your server as a subprocess** and talks to it over
that process's standard input and standard output. This is the stdio
transport, and it's what `mcp.run()` defaults to when you don't specify
anything else.

Concretely: the host runs something equivalent to
`subprocess.Popen(["python", "server.py"], stdin=PIPE, stdout=PIPE)`. Every
JSON-RPC message the host sends gets written to your server's stdin, one
JSON object per line, newline-terminated. Every message your server sends
back gets written to stdout in the same format. There's no HTTP, no
sockets, no ports to configure — just a pipe in each direction.

This is why stdio is the default and simplest choice for local servers:
there's effectively zero setup beyond "run this command," which is exactly
what you'll register in `claude_desktop_config.json` in the next lesson.

## The one rule you cannot break

Because stdout is the literal protocol channel, **anything your server
prints to stdout other than well-formed JSON-RPC messages corrupts the
stream** and breaks the connection — often in confusing ways, since the
failure shows up as a parse error on whichever message happened to follow
the stray output.

This means a plain `print()` call anywhere in your server's code, including
deep inside a library you're calling, is a real bug:

```python
@mcp.tool()
def add(a: int, b: int) -> int:
    print(f"Adding {a} and {b}")  # BUG: this corrupts the stdio stream
    return a + b
```

That innocent-looking debug `print()` writes `Adding 2 and 3` straight into
the same stream the client is trying to parse as JSON-RPC. The client will
fail to parse it, and depending on timing, may also fail to parse the
*next* legitimate message because the stream is now out of sync.

## Log to stderr instead

Standard error is a separate stream, untouched by the protocol — it's the
right place for anything you want to see while debugging, and `FastMCP`
servers can write there freely:

```python
import sys

@mcp.tool()
def add(a: int, b: int) -> int:
    print(f"Adding {a} and {b}", file=sys.stderr)  # safe
    return a + b
```

Or, more idiomatically, use Python's `logging` module configured to a
stream handler on `stderr` (the standard library default for
`logging.StreamHandler()` with no argument), which gives you levels and
formatting for free without any risk of touching stdout.

## Why this doesn't apply equally to every transport

This specific gotcha is unique to stdio. Lesson 2 of Level 2 covers
Streamable HTTP transport, where the protocol messages travel over HTTP
request/response bodies instead of a shared process stream — ordinary
console output there doesn't collide with anything. But stdio is what every
local server you build in this level uses, so the habit of never touching
stdout starts now.

## Exercise

Take the `server.py` from lesson 4 and deliberately add a `print()`
statement inside the `add` tool, pointed at stdout. Run it through the MCP
Inspector and call `add` — observe what actually happens (a parse error, a
hang, or a garbled response, depending on your SDK version and timing).
Then fix it by redirecting that same debug line to `sys.stderr` and confirm
the tool call works cleanly again.
