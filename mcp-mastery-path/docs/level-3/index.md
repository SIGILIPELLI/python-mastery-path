# Level 3 · Advanced <span class="level-badge">Scale &amp; Security</span>

Goal: go from "one server works" to "several servers work together reliably,
safely, and observably" — the engineering that separates a demo from a
system you'd trust in production.

## Modules

1. [Multi-Server Clients: Connecting to Several Servers at Once](01-multi-server-clients.md)
2. [Tool Selection & Namespacing at Scale](02-tool-selection-namespacing.md)
3. [Error Handling & Resilience Patterns](03-error-handling-resilience.md)
4. [Streaming Responses & Progress Notifications](04-streaming-progress-notifications.md)
5. [Roots: Scoping a Server to a Workspace](05-roots-workspace-scoping.md)
6. [Security: Prompt Injection & Tool Poisoning Risks](06-security-prompt-injection.md)
7. [Scopes, Permissions & Least Privilege](07-scopes-permissions.md)
8. [Caching & Rate Limiting Tool Calls](08-caching-rate-limiting.md)
9. [Observability: Logging & Tracing MCP Calls](09-observability-logging-tracing.md)
10. [Project — Orchestrating 3 MCP Servers for a Research Agent](10-project-research-agent.md)

By the end of this level you'll be able to wire up and secure multi-server
agent systems, reason about MCP-specific security risks like prompt
injection and tool poisoning, and keep a multi-server setup observable and
resilient under real failures.
