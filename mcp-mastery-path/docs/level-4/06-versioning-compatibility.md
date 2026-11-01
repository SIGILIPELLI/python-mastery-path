---
description: "Protocol version compatibility is negotiated once, during initialize, before a single tool call happens — get that handshake wrong and nothing else works."
---

# 06 · Versioning & Backward Compatibility

Two different kinds of "versioning" matter in an MCP system, and they're
easy to conflate: the version of the **MCP protocol itself**, negotiated on
every connection, and the version of **your server's own tool set**, which
evolves on your own schedule. This lesson covers both.

## Protocol version negotiation

Every connection starts with the client sending an `initialize` request
that includes the protocol version it supports:

```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "initialize",
  "params": {
    "protocolVersion": "2025-06-18",
    "capabilities": {},
    "clientInfo": {"name": "example-host", "version": "1.0.0"}
  }
}
```

The server responds with the protocol version *it* will use for this
session — either the client's requested version if it supports it, or a
different version it does support, along with its own capabilities:

```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "result": {
    "protocolVersion": "2025-06-18",
    "capabilities": {"tools": {}, "resources": {"subscribe": true}},
    "serverInfo": {"name": "docs-server", "version": "2.1.0"}
  }
}
```

If the client doesn't support the version the server comes back with, it's
expected to close the connection rather than proceed on a protocol version
it can't correctly implement. This exchange happens exactly once, before
`initialized` is sent and normal operation begins — there's no
mid-session protocol version switching.

## Capabilities: declaring what you actually support

Alongside the protocol version, both sides declare *capabilities* — which
optional parts of the spec they implement. A server that doesn't support
resource subscriptions simply omits `subscribe: true` from its
`capabilities.resources` object; a client should check for a capability
before relying on it rather than assuming every server supports everything
the spec defines. This is the main lever that lets the protocol add new
optional features over time without breaking servers and clients that
predate them.

## How It Actually Works

The negotiation is designed around a specific failure mode: a client and
server built against different protocol-spec dates connecting to each
other.

1. **The client proposes a version it was built against.** This is the
   version whose request/response shapes its SDK code actually implements.
2. **The server either confirms that version or proposes an alternative it
   does support.** A well-behaved server should support at least one version
   the client is likely to understand; SDKs typically track a small range of
   recent spec versions rather than only the very latest.
3. **The client must validate the server's answer**, not just assume success
   — proceeding with a protocol version your client code doesn't actually
   implement is how you get obscure runtime errors on the first real
   request rather than a clean failure at startup.
4. **Capabilities are the finer-grained compatibility signal within a
   given protocol version** — two implementations can agree on the same
   protocol version and still differ on which optional features they
   support, which is exactly why capabilities are negotiated separately
   rather than implied by version number alone.

## Evolving your own tool set without breaking clients

Separately from protocol versioning, your *server's* tools, resources, and
prompts change over time as you add features. The practical rules that keep
existing clients working:

- **Adding a new tool is always safe** — clients that don't know about it
  simply never call it.
- **Adding a new optional parameter to an existing tool is safe**, as long
  as it has a sensible default and omitting it preserves the old behavior.
- **Removing a tool, renaming a tool, or changing a required parameter's
  type is a breaking change** — treat it exactly like a breaking API change
  anywhere else: version your server's own release (your `serverInfo.version`
  field, and ideally your own changelog), give existing integrations notice,
  and consider keeping the old tool as a deprecated alias for a transition
  period rather than deleting it outright.
- **Changing what a tool's description promises, even without changing its
  schema, is also a real compatibility break** from the model's point of
  view — a model relying on the old description to decide when to call the
  tool may now call it at the wrong moments.

## Exercise

Take a tool from any server you built in an earlier level. Write two
versions of its definition: the current one, and a "v2" that adds one new
optional parameter with a safe default. Confirm (by reasoning through it,
or by actually testing with an old client call that doesn't pass the new
parameter) that the old call still behaves identically under the new
version — that's the concrete bar "backward compatible" needs to clear.
