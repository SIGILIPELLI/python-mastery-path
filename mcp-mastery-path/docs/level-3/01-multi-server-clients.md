---
description: "A Host doesn't share one Client across servers — it creates a dedicated Client instance per Server connection, then aggregates their capabilities at the Host layer."
---

# 01 · Multi-Server Clients: Connecting to Several Servers at Once

Every lesson so far has used one server at a time. Real MCP hosts — Claude
Desktop, an IDE, your own agent — usually talk to several servers at once: a
filesystem server, a GitHub server, a search server, all available in the
same conversation. This lesson builds the piece that makes that possible: a
host-side layer that owns multiple client connections and presents them to
the rest of the application as one unified tool catalog.

## One Client per Server, not one Client for everything

The MCP spec is strict about this: a `Client` has a 1:1 relationship with a
`Server`. If you want to talk to three servers, you create three `Client`
instances, each with its own transport (its own subprocess, if you're using
stdio). There's no multiplexed "one client, many servers" object in the SDK —
that aggregation is something *you* build at the layer above the clients,
inside your Host application.

```python
from contextlib import AsyncExitStack
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

SERVER_CONFIGS = {
    "notes": StdioServerParameters(command="python", args=["notes_server.py"]),
    "github": StdioServerParameters(command="python", args=["github_server.py"]),
    "search": StdioServerParameters(command="python", args=["search_server.py"]),
}

class MultiServerClient:
    def __init__(self):
        self.sessions: dict[str, ClientSession] = {}
        self._stack = AsyncExitStack()

    async def connect_all(self):
        for name, params in SERVER_CONFIGS.items():
            read, write = await self._stack.enter_async_context(stdio_client(params))
            session = await self._stack.enter_async_context(ClientSession(read, write))
            await session.initialize()
            self.sessions[name] = session

    async def close(self):
        await self._stack.aclose()
```

`AsyncExitStack` is doing real work here: each server is its own subprocess
and its own async context manager. Without it you'd need deeply nested
`async with` blocks, one per server, and they'd all have to stay open for as
long as the conversation runs. The stack lets you open an arbitrary, runtime
-determined number of them and close them all cleanly with one call.

## Aggregating the tool catalog

Once every session is initialized, list tools from each one and merge them
into a single catalog the rest of your application can treat uniformly:

```python
async def list_all_tools(client: MultiServerClient) -> dict[str, list]:
    catalog = {}
    for server_name, session in client.sessions.items():
        result = await session.list_tools()
        catalog[server_name] = result.tools
    return catalog
```

At this point you have, for example, `catalog["notes"]` containing
`add_note`/`list_notes`, and `catalog["github"]` containing
`list_issues`/`create_issue`. Two different servers, two different tool
lists, same shape.

## Routing a tool call to the right server

The model doesn't know or care which server owns which tool — it just sees
one flat list of available tools (how you flatten that list is next lesson's
topic). When a tool call comes back from the model, you need to know which
server to forward it to:

```python
def build_tool_index(catalog: dict[str, list]) -> dict[str, str]:
    """Map tool_name -> server_name for routing."""
    index = {}
    for server_name, tools in catalog.items():
        for tool in tools:
            index[tool.name] = server_name
    return index

async def call_tool(client: MultiServerClient, tool_index: dict, tool_name: str, arguments: dict):
    server_name = tool_index[tool_name]
    session = client.sessions[server_name]
    return await session.call_tool(tool_name, arguments)
```

This is the whole trick of a multi-server client: build an index once after
connecting (and again whenever a server's tool list changes — more on that
in the next lesson), then use that index to route every incoming call. The
model-facing surface stays simple; the routing complexity lives entirely on
your side of the connection.

## What happens if one server is slow or hangs during connect

`connect_all` above connects sequentially — server two doesn't start
connecting until server one's `initialize()` has returned. For three fast
local servers that's fine. For a mix of local and remote servers, a hung
connection to one remote server blocks every other server from becoming
available. A more robust version connects concurrently and tolerates partial
failure:

```python
import asyncio

async def connect_all_concurrent(client: MultiServerClient):
    async def connect_one(name, params):
        try:
            read, write = await client._stack.enter_async_context(stdio_client(params))
            session = await client._stack.enter_async_context(ClientSession(read, write))
            await session.initialize()
            client.sessions[name] = session
        except Exception as e:
            print(f"Failed to connect to {name}: {e}")  # log, don't crash the whole host

    await asyncio.gather(*(connect_one(n, p) for n, p in SERVER_CONFIGS.items()))
```

Full resilience patterns — retries, timeouts, graceful degradation when a
server disappears mid-conversation — are this level's lesson 3. For now,
the point is structural: a multi-server client should assume any one
connection can fail without taking the other servers down with it.

## Exercise

Extend `MultiServerClient` with a `call_tool_safe` method that looks up the
tool in the index, and if the tool name isn't found in any connected
server, returns a clear error dict (e.g. `{"error": "unknown tool: X"}`)
instead of raising a `KeyError`. Then write a small script that connects to
two toy servers (reuse Level 1's notes server and a second trivial server
with one `echo` tool), lists the combined catalog, and calls a tool from
each by name through the same `call_tool_safe` function.
