# Level 2 · Intermediate <span class="level-badge">Production Servers</span>

Goal: move past a local stdio server and build something you could actually
ship — remote transport, real authentication, and a server that wraps a real
external API.

## Modules

1. [The TypeScript SDK](01-typescript-sdk.md)
2. [Streamable HTTP & SSE Transport](02-http-sse-transport.md)
3. [Authentication & OAuth 2.1 for Remote Servers](03-auth-oauth.md)
4. [Resource Templates & Dynamic URIs](04-resource-templates.md)
5. [Sampling: Letting a Server Ask the LLM for Completions](05-sampling.md)
6. [Structured Output & Tool Input Schemas](06-structured-output-schemas.md)
7. [Wrapping a Real API: GitHub as an MCP Server](07-wrapping-github-api.md)
8. [Testing MCP Servers (Inspector & Unit Tests)](08-testing-mcp-servers.md)
9. [Deploying a Remote MCP Server](09-deploying-remote-server.md)
10. [Project — A GitHub Issues MCP Server](10-project-github-issues-server.md)

By the end of this level you'll be fluent in both the Python and TypeScript
SDKs, comfortable with remote transport and OAuth 2.1, and you'll have built
and deployed a real server that wraps a live external API.
