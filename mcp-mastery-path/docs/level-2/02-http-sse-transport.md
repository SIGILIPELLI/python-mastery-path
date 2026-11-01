---
description: "Streamable HTTP replaces stdio's stdin/stdout pipe with a single POST endpoint for client-to-server messages and an optional SSE stream for server-initiated ones."
---

# 02 · Streamable HTTP & SSE Transport

Everything so far has used stdio: the host spawns your server as a child
process and talks to it over stdin/stdout. That only works when client and
server live on the same machine. A server deployed to the cloud, shared by
many users, needs a transport that works over a network — that's
**Streamable HTTP**.

## Why stdio can't cross a network

stdio transport assumes:

- The server is a subprocess the host directly spawned and owns.
- There's exactly one client talking to exactly one server process.
- The pipe is private — no other process can read or write it.

None of that holds for a server running on infrastructure you don't control
from the client's machine. You need a transport built on a protocol that
networks actually support, with a notion of separate client connections and
message framing that survives going through load balancers and proxies.
HTTP is that protocol.

## How Streamable HTTP works

A Streamable HTTP MCP server exposes a single endpoint, typically `/mcp`,
that handles two kinds of traffic:

- **`POST /mcp`** — the client sends a JSON-RPC request or notification as
  the request body. For a simple request/response exchange, the server's
  HTTP response body is just the JSON-RPC response.
- **`GET /mcp`** with `Accept: text/event-stream` — opens a long-lived
  Server-Sent Events stream the server can use to push messages to the
  client without the client having to poll (notifications, or responses to
  requests the server is still processing).

A `Mcp-Session-Id` header, set by the server on its first response and
echoed back by the client on every subsequent request, ties a sequence of
HTTP requests together into one logical MCP session — the network
equivalent of "the same stdio pipe."

## A minimal HTTP server (Python)

```bash
pip install "mcp[cli]"
```

```python
# http_server.py
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("http-demo")

@mcp.tool()
def echo(message: str) -> str:
    """Returns the message back unchanged."""
    return message

if __name__ == "__main__":
    mcp.run(transport="streamable-http")
```

```bash
python http_server.py
# serving on http://127.0.0.1:8000/mcp by default
```

Point the Inspector at a URL instead of a local command to connect to it:

```bash
npx @modelcontextprotocol/inspector
# then choose "Streamable HTTP" and enter http://127.0.0.1:8000/mcp
```

## A raw POST, to see the shape

You don't need the Inspector to talk to this server — it's just HTTP:

```bash
curl -s http://127.0.0.1:8000/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -d '{
    "jsonrpc": "2.0",
    "id": 1,
    "method": "tools/call",
    "params": {"name": "echo", "arguments": {"message": "hi"}}
  }'
```

The response is the same JSON-RPC `result` object you'd see over stdio —
the transport changed, the protocol on top of it didn't.

## How It Actually Works

1. **Every request is still JSON-RPC.** Streamable HTTP doesn't change what
   a request, response, or notification looks like — only how the bytes get
   from client to server and back. `tools/call` over HTTP has the exact
   same `params` shape as `tools/call` over stdio.
2. **The session ID is the glue.** stdio gets "this is the same
   conversation" for free, because it's one process talking over one pipe.
   HTTP requests are independent by default, so the server issues a
   `Mcp-Session-Id` on the `initialize` response, and the client must send
   it back on every later request so the server can find the right
   in-memory session state.
3. **SSE is for the server-initiated direction.** A plain HTTP response can
   only answer the request that triggered it. But MCP needs the server to
   be able to send unsolicited messages — a progress notification during a
   long tool call, or a `sampling/createMessage` request asking the
   client's LLM for a completion. The `GET` endpoint's event stream is how
   those reach the client without the client polling.
4. **A `POST` can itself open a stream.** If handling a request will take a
   while or needs to emit intermediate notifications, the server can
   respond to that `POST` with `Content-Type: text/event-stream` instead of
   a single JSON body, streaming the eventual result as one of the events.
5. **Statelessness is a deployment choice, not a protocol requirement.** A
   server can be written to keep no session state at all (treating every
   request independently) specifically so it scales horizontally without
   sticky sessions — more on this trade-off in Level 4.

## Exercise

Add a second tool to `http_server.py`, `slow_count(n: int)`, that sleeps for
one second `n` times. Run the server, then use the Inspector's "History" or
network panel to watch what happens on the connection while a call to
`slow_count(3)` is in flight — note that the HTTP request doesn't return
until the tool finishes, even though nothing is streamed back incrementally
in this simple version. That gap is exactly what Level 3's progress
notifications are for.
