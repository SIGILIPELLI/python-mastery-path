---
description: "A stdio server is trusted because the host chose to launch it; a remote HTTP server has no such guarantee, so MCP requires OAuth 2.1 bearer tokens instead."
---

# 03 · Authentication & OAuth 2.1 for Remote Servers

A stdio server never asked you for a password, and that wasn't an oversight.
A remote server can't get away with that — it needs a real authorization
story. MCP specifies one, built on **OAuth 2.1**.

## Why stdio servers skip this entirely

When Claude Desktop launches your server as a subprocess, the trust
decision already happened: you, the user, put that server's command in your
`claude_desktop_config.json`. The server only runs because you explicitly
told your own machine to run it. There's no network boundary to secure
because there's no network involved.

A remote server has none of that. Anyone who can reach its URL can send it
requests. Without authorization, "connect to this MCP server" would mean
"give an unknown caller the ability to invoke your tools" — unacceptable the
moment a tool does anything that costs money, exposes private data, or
changes state (which is most of what makes a tool worth having).

## The shape of the flow

MCP's authorization spec is standard OAuth 2.1 with a few MCP-specific
conventions layered on:

1. **Discovery.** The client fetches a well-known metadata document from the
   server (`/.well-known/oauth-protected-resource`) to learn which
   authorization server issues tokens for this MCP server, and that
   authorization server's own metadata (`/.well-known/oauth-authorization-server`)
   to learn its endpoints.
2. **Dynamic client registration** (where supported) lets the MCP client
   register itself with the authorization server on the fly, rather than
   requiring a developer to have pre-registered a client ID by hand.
3. **Authorization.** The user is sent through a normal OAuth authorization
   code flow (with PKCE, as OAuth 2.1 requires) — log in, approve the
   requested scopes, get redirected back with a code.
4. **Token issuance.** The client exchanges that code for an access token
   (and typically a refresh token).
5. **Every request after that carries the token.** `Authorization: Bearer
   <token>` on each HTTP request to the MCP server.

## What this looks like from the server's side

```python
from mcp.server.fastmcp import FastMCP
from mcp.server.auth.settings import AuthSettings

mcp = FastMCP(
    "billing-tools",
    auth=AuthSettings(
        issuer_url="https://auth.example.com",
        resource_server_url="https://mcp.example.com",
        required_scopes=["billing:read"],
    ),
)

@mcp.tool()
def list_invoices(customer_id: str) -> str:
    """Lists invoices for a customer. Requires the billing:read scope."""
    ...
```

The SDK handles validating the bearer token on incoming requests and
rejecting ones that don't present a valid token with the required scope —
your tool code only runs once that's already been checked.

## What a well-behaved client does

- Tries the request unauthenticated first (or reads the discovery document
  up front) to learn where to get a token.
- Runs the user through the authorization flow exactly once, then reuses the
  resulting access token for subsequent requests, refreshing it silently
  when it expires.
- Never stores the token anywhere a malicious page or process could read it
  more easily than it reads the user's other credentials.

## How It Actually Works

1. **Bearer tokens, not API keys hardcoded in config.** An API key baked
   into a config file is a long-lived, broad credential. A short-lived OAuth
   access token scoped to specific permissions is strictly safer: it
   expires, it can be scoped narrowly (`billing:read` but not
   `billing:write`), and it can be revoked without rotating a secret
   everyone shares.
2. **PKCE closes the authorization-code-interception hole.** OAuth 2.1
   requires PKCE (Proof Key for Code Exchange) on every authorization code
   flow — the client generates a secret verifier up front, sends only a
   hash of it with the authorization request, and must present the original
   verifier when exchanging the code for a token. Even if the code is
   intercepted in transit, it's useless without the verifier.
3. **Discovery means no hardcoded endpoints.** Because the client reads
   `/.well-known/oauth-protected-resource` and the authorization server's
   own metadata document, an MCP client can authenticate against any
   compliant server without the client's author having to pre-configure
   that specific server's OAuth details.
4. **Resource-scoped tokens prevent token reuse across servers.** OAuth 2.1
   ties a token to the specific resource server (MCP server) it was issued
   for, so a token stolen from one MCP server's traffic can't be replayed
   against a different one.

## Exercise

Without writing the full OAuth flow by hand (that's a lot of moving parts
for an exercise), sketch out — as comments or a short markdown note next to
your `billing-tools` server from this lesson — exactly which HTTP requests
would need to happen, in order, for a brand-new client to go from "has never
talked to this server before" to "successfully calling `list_invoices` with
a valid bearer token." Use the five numbered steps above as your checklist
and fill in what each one's actual HTTP method/URL would look like.
