---
description: "Roots are advisory, not enforced by the protocol — a well-behaved server checks them before touching the filesystem, but nothing stops a malicious server from ignoring them entirely."
---

# 05 · Roots: Scoping a Server to a Workspace

A filesystem-capable MCP server connected to your machine is, in principle,
capable of reading or writing anywhere the process has permission to touch.
That's far more access than almost any real workflow needs. `roots` is the
MCP primitive for narrowing that down: the *client* declares which
directories (or, more generally, URI prefixes) a server should treat as
its working set.

## Who declares roots, and when

Unlike tools/resources/prompts (which servers expose), roots flow in the
other direction: the **client** advertises them to the server, typically
right after the `initialize` handshake, and can update them later (e.g. the
user switches which project folder they're working in).

```python
from mcp.types import Root

async def set_workspace_roots(session, workspace_paths: list[str]):
    roots = [Root(uri=f"file://{path}", name=path.split("/")[-1]) for path in workspace_paths]
    await session.send_roots_list_changed(roots)
```

A server that supports roots declares that capability during `initialize`,
and the client only bothers sending roots to servers that said they'd use
them.

## Consuming roots on the server side

The server's job is to treat the declared roots as the *only* legitimate
scope for filesystem-style operations, rejecting anything outside it:

```python
import os
from pathlib import Path
from mcp.server.fastmcp import FastMCP, Context

mcp = FastMCP("workspace-files-server")

def is_within_roots(path: Path, roots: list[Path]) -> bool:
    resolved = path.resolve()
    return any(
        resolved == root or root in resolved.parents
        for root in (r.resolve() for r in roots)
    )

@mcp.tool()
async def read_workspace_file(relative_path: str, ctx: Context) -> str:
    """Read a file, but only if it falls within one of the client's declared roots."""
    roots = await ctx.list_roots()  # URIs the client declared, e.g. file:///home/user/project
    root_paths = [Path(r.uri.removeprefix("file://")) for r in roots]

    # resolve relative to the first root, then verify it didn't escape via ../..
    candidate = (root_paths[0] / relative_path).resolve()
    if not is_within_roots(candidate, root_paths):
        return f"Access denied: {relative_path} is outside the declared workspace roots"

    return candidate.read_text()
```

The `.resolve()` + parent-directory check is doing the actual security
work here — without it, a relative path like `../../etc/passwd` would
"resolve" outside the intended root while still looking like a harmless
relative path string at the call site. Always resolve to an absolute path
and check containment against the resolved root, never against the raw
string.

## Roots are advisory, not enforced by the protocol

This is the detail worth sitting with: MCP defines how roots are
*communicated*, but it has no mechanism that forces a server to respect
them. A well-implemented server checks every filesystem operation against
the declared roots, the way the example above does. A buggy or malicious
server can simply ignore the roots entirely and read whatever the host
process's OS permissions allow.

That means roots are a **cooperative scoping mechanism between a trusted
client and a trusted server**, not a security sandbox against an untrusted
one. If you're connecting to a server you don't fully trust, roots alone
aren't the control that protects you — OS-level sandboxing (containers,
restricted file permissions, a dedicated low-privilege user) is what
actually enforces a boundary a server can't opt out of. Roots are about
making a *well-behaved* server's default scope sensible and
workspace-aware, not about containing a *hostile* one. (The broader
security picture — prompt injection, tool poisoning, trust boundaries
generally — is this level's next lesson.)

## Handling root changes

A user switching projects mid-session should update the server's effective
scope without requiring a reconnect:

```python
@mcp.on_roots_list_changed()
async def handle_roots_changed(ctx: Context):
    new_roots = await ctx.list_roots()
    # invalidate any cached file listings, in-memory indexes, etc.
    # built against the previous root set
    file_index_cache.clear()
```

Servers that cache anything derived from the filesystem (a search index, a
directory listing) need to treat a roots-changed notification as "the
ground truth moved" and invalidate accordingly, not keep serving results
built against the old workspace.

## Exercise

Extend `read_workspace_file` with a matching `write_workspace_file` tool
that applies the same root-containment check before writing, and a
`list_workspace_files` tool that lists files recursively within the roots
only. Write a quick test that declares a root at a temp directory, confirms
a file inside it can be read/written/listed normally, and confirms a path
using `../` to escape the root is rejected by all three tools.
