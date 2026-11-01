---
description: "A gateway makes N internal MCP servers look like one connection to every client, which is also the one place left to enforce auth and policy consistently across all of them."
---

# 05 · An Internal MCP Server Registry/Gateway

Once an organization has more than a couple of internal MCP servers —
search, a ticketing system, internal docs, a deploy tool — making every
client connect to every server individually gets unwieldy fast: N clients
each independently configuring N server connections, N sets of credentials,
and N places that need to agree on access policy. A gateway collapses that
into one connection point.

## What a gateway actually does

A gateway is itself an MCP server from a client's point of view, but instead
of implementing tools directly, it proxies `tools/list` and `tools/call`
(and the resource/prompt equivalents) to a set of registered backend
servers, aggregating their capabilities into one combined list and routing
each call to the right backend.

```python
from mcp.server.fastmcp import FastMCP
from mcp import ClientSession
from mcp.client.stdio import stdio_client, StdioServerParameters

mcp = FastMCP("internal-gateway")

# registry: server name -> connection parameters
BACKENDS = {
    "search": StdioServerParameters(command="mcp-search-server"),
    "tickets": StdioServerParameters(command="mcp-tickets-server"),
}

_sessions: dict[str, ClientSession] = {}

async def get_session(backend: str) -> ClientSession:
    if backend not in _sessions:
        read, write = await stdio_client(BACKENDS[backend]).__aenter__()
        session = ClientSession(read, write)
        await session.initialize()
        _sessions[backend] = session
    return _sessions[backend]

@mcp.tool()
async def search_search_docs(query: str) -> list[dict]:
    """Proxy to the 'search' backend's search_docs tool."""
    session = await get_session("search")
    result = await session.call_tool("search_docs", {"query": query})
    return result.content
```

A production gateway generalizes this: instead of hand-writing one proxy
tool per backend tool, it calls `tools/list` on each backend at startup (or
on a refresh interval), namespaces each tool by backend (`search.search_docs`,
`tickets.create_ticket` — tying back to the namespacing pattern from Level
3), and dynamically registers a proxying handler for each one.

## Where auth and policy belong

The gateway is the single place every call passes through, which makes it
the natural enforcement point for things that would otherwise need
duplicating in every backend server:

- **Authenticating the calling client once**, at the gateway, instead of
  each backend server independently validating credentials.
- **Per-client, per-tool authorization** — a service account for an internal
  chatbot might be allowed `search.*` but not `tickets.create_ticket`, enforced
  centrally before a call is ever forwarded.
- **Consistent audit logging** of every tool call across every backend, in
  one place, in one format — the natural home for the observability patterns
  from Level 3.
- **Rate limiting and caching** applied uniformly, rather than reimplemented
  per backend.

```python
ALLOWED_TOOLS = {
    "chatbot-service": {"search.search_docs"},
    "ops-dashboard": {"search.search_docs", "tickets.create_ticket"},
}

async def authorize(client_id: str, tool_name: str):
    if tool_name not in ALLOWED_TOOLS.get(client_id, set()):
        raise PermissionError(f"{client_id} is not authorized for {tool_name}")
```

## The registry half

The "registry" piece is simply the gateway's backend list made
discoverable and manageable on its own — a config file, a small database
table, or an admin API that lets backends register themselves (and
deregister on shutdown) rather than being hard-coded. At small scale a
static config file is entirely sufficient; dynamic registration only earns
its complexity once backends are added and removed often enough that
editing a config file by hand becomes the actual bottleneck.

## Exercise

Extend the sketch above into a working gateway with two backend servers of
your own (reuse ones from earlier levels, or stub two trivial ones). Add the
namespacing step so tool names are prefixed by backend automatically instead
of hand-written per tool, and add the simple `authorize()` check shown above
gating at least one tool behind a specific client identity.
