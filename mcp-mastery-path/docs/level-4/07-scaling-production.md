---
description: "A stateless MCP server scales like any other HTTP service behind a load balancer — a stateful SSE server doesn't, because a client's long-lived stream has to keep landing on the same process."
---

# 07 · Scaling MCP Servers in Production

Scaling an MCP server mostly means scaling an ordinary web service — until
you hit the one place MCP is genuinely different from a typical REST API:
long-lived, server-initiated streaming connections. This lesson covers both
halves.

## Stateless servers: the easy case

A server that keeps no in-memory session state between requests — every
`tools/call` is handled using only the arguments in that request, with
anything persistent (user data, cached results) living in an external store
like a database or cache — scales exactly like any stateless HTTP service:

```
            ┌──────────────┐
  clients → │ Load Balancer │ → server instance 1
            └──────────────┘ → server instance 2
                             → server instance 3
```

Any instance can handle any request. Add instances under load, remove them
when load drops, and a standard load balancer with a basic health check is
all the routing logic you need. If your server's tools only ever read from
or write to external systems (a database, an API) rather than holding state
in the process itself, aim to keep it stateless — it's by far the simpler
scaling story.

## Stateful servers: the real constraint

A server using the Streamable HTTP transport's SSE stream for
server-initiated messages (progress notifications, sampling requests) has a
connection a specific client is actively listening on. If a load balancer
routes that client's next request to a *different* instance than the one
holding its open stream, the server-initiated messages have nowhere to go.

```
            ┌──────────────┐
  client  → │ Load Balancer │ → instance A  ← client's SSE stream is HERE
                             → instance B  ← a later request lands here
                                               and can't reach the stream
```

The standard fixes, in order of how much they cost you:

- **Session affinity (sticky sessions)** at the load balancer — route a
  given `Mcp-Session-Id` to the same backend instance for the life of the
  session. Simple to configure, but it means that instance's failure drops
  every session pinned to it, and it can produce uneven load if some
  sessions are much longer-lived than others.
- **A shared pub/sub backbone between instances** (Redis Streams, a message
  queue) — any instance can receive a request, and if the client's session
  is pinned to a *different* instance's stream, the receiving instance
  publishes the message for the owning instance to pick up and forward.
  More infrastructure, but no single instance failure drops sessions it
  isn't directly holding.
- **Externalizing session state entirely**, so "which instance owns this
  session" is a lookup in a shared store rather than a load-balancer
  routing decision baked in at connection time — the most flexible option,
  and the most work to build correctly.

Most teams start with sticky sessions and only move to a shared backbone
once session-affinity failures or load imbalance actually become a measured
problem — building the pub/sub version up front for a server that doesn't
need it yet is usually wasted complexity.

## Connection pooling to backends

A server's tools very often call out to something else — a database, an
internal API, another MCP server behind a gateway. Under concurrent load,
opening a fresh connection per tool call to each of those backends adds
real, avoidable latency and can exhaust the backend's own connection limits.
Pool connections to each backend the same way you would in any backend
service:

```python
import asyncpg

_pool: asyncpg.Pool | None = None

async def get_db_pool() -> asyncpg.Pool:
    global _pool
    if _pool is None:
        _pool = await asyncpg.create_pool(dsn="...", min_size=2, max_size=10)
    return _pool

@mcp.tool()
async def get_user(user_id: int) -> dict:
    pool = await get_db_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow("SELECT * FROM users WHERE id = $1", user_id)
        return dict(row)
```

Size the pool against the backend's own connection limit divided by the
number of server instances you expect to run concurrently, not against a
guess — an oversized pool across many instances is a common way to
accidentally exhaust a database's connection limit under scale-out.

## Exercise

For a server you've already built (pick one with at least one tool that
calls an external system), write a short scaling plan: is it stateless or
does it rely on server-initiated SSE messages? If stateless, what would you
need at the load balancer? If stateful, which of the three fixes above
would you reach for first, and why? Then add connection pooling to any tool
in it that currently opens a fresh connection per call.
