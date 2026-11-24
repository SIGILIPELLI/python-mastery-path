---
description: "FastMCP turns a plain Python function into a fully-specified MCP tool using nothing but its type hints and docstring."
---

# 04 · Setup: Python SDK & Your First Server

## Install the SDK

The official Python SDK is published as the `mcp` package, and it ships the
`FastMCP` helper class that this entire course uses to build servers.

```bash
pip install "mcp<2"
```

!!! note "Version"
    This course uses the 1.x Python SDK (the examples were checked against `mcp` 1.30).
    In `mcp` 2.x, `FastMCP` was renamed `MCPServer` and `mcp.server.fastmcp` no longer
    exists, so a plain `pip install mcp` today installs a version that cannot run the code
    here. Pin `mcp<2` (as above) to follow along, or see the SDK's migration guide before
    moving to 2.x.

You'll also want the MCP Inspector, a browser-based tool for poking at a
server interactively without needing a full host application like Claude
Desktop. It's a Node package, run directly with `npx` (no install needed):

```bash
npx @modelcontextprotocol/inspector
```

Keep that command handy — you'll use it in a moment.

## Your first server

Create `server.py`:

```python
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("demo-server")

@mcp.tool()
def add(a: int, b: int) -> int:
    """Add two numbers together."""
    return a + b

if __name__ == "__main__":
    mcp.run()
```

That's a complete, working MCP server. `FastMCP("demo-server")` creates a
server named `demo-server`. The `@mcp.tool()` decorator registers `add` as a
tool the server exposes. `mcp.run()` starts the server, defaulting to the
stdio transport covered in lesson 8 — it blocks and waits for a client to
connect over stdin/stdout.

Run it directly and it'll just sit there, waiting:

```bash
python server.py
```

That's expected — a stdio server has nothing to say until a client connects
to it. Press Ctrl+C to stop it; you'll connect to it properly next.

## Inspecting it

The MCP Inspector gives you a client to talk to your server without writing
one yourself. Run:

```bash
npx @modelcontextprotocol/inspector python server.py
```

This opens a browser UI. The Inspector launches your `server.py` as a
subprocess (the same way a real host application would), connects to it,
and lets you:

- See the `initialize` handshake and the capabilities your server reported
- Browse the `tools/list` response — you should see `add` listed, with a
  JSON Schema generated from its type hints
- Call `add` with real arguments and see the `tools/call` request and
  response, exactly as described in lesson 2

Try calling `add` with `a=2, b=3` and confirm you get `5` back, then watch
the raw JSON-RPC messages in the Inspector's message log — it's the fastest
way to connect everything from the last three lessons to something real.

## Exercise

Add a second tool to `server.py` called `multiply(a: int, b: int) -> int`
that returns the product. Restart the Inspector, confirm both `add` and
`multiply` appear in `tools/list`, and call `multiply` with two different
pairs of numbers to confirm it works.
