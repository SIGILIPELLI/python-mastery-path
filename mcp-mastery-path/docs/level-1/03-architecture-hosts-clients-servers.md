---
description: "A Host owns one or more Clients, and each Client maintains a strict 1:1 connection to exactly one Server — never a many-to-one client-to-server link."
---

# 03 · MCP Architecture: Hosts, Clients & Servers

MCP defines three distinct roles. Getting these precise — especially the
one-to-one rule below — makes everything else in this course easier to
reason about.

## The three roles

**Host** — the AI application the user actually interacts with: Claude
Desktop, an IDE with AI features, a custom agent application. The host is
responsible for managing the overall conversation, enforcing permissions,
and deciding which servers to connect to.

**Client** — lives inside the host, and manages the connection to exactly
**one** server. If a host wants to use three different MCP servers, it
creates and owns three separate client instances internally — one per
server. This is a strict 1:1 relationship: a single client never
multiplexes connections to more than one server.

**Server** — a (usually small, often standalone) program that exposes
capabilities — tools, resources, prompts — to whichever client connects to
it. A server doesn't know or care which host it's ultimately serving; it
just speaks MCP to its one connected client.

```text
┌─────────────────────────────────────┐
│ Host (e.g. Claude Desktop)           │
│                                      │
│   ┌────────┐   ┌────────┐           │
│   │Client A│   │Client B│           │
│   └───┬────┘   └───┬────┘           │
└───────┼────────────┼────────────────┘
        │ 1:1         │ 1:1
        ▼             ▼
   Server A      Server B
  (calendar)       (Slack)
```

Note what this diagram rules out: Client A never talks to Server B. If the
host wants to use both the calendar and Slack servers, it runs two clients,
each wired to exactly one server.

## Capabilities, not a fixed feature set

A server doesn't have to expose tools, resources, *and* prompts — it
declares which of these it actually implements. This declaration happens
during the `initialize` handshake (next section), so the client knows
upfront what it can ask for and never has to guess or trial-and-error its
way into discovering what a server supports.

## Server-side vs. client-side primitives

The three primitives you'll spend most of this level on are all things a
**server** offers:

| Primitive | What it is | Who controls when it's used |
|---|---|---|
| **Tools** | Functions the model can call to take an action | The model decides, based on the user's request |
| **Resources** | Data the client can read (files, records, docs) | The application or user typically selects these |
| **Prompts** | Reusable, parameterized prompt templates | The user typically invokes these explicitly |

MCP also defines two primitives that flow the other direction — a
**client**-side capability a server can request:

| Primitive | What it is |
|---|---|
| **Sampling** | A server can ask the client to run an LLM completion on its behalf, without the server needing its own API key or model access |
| **Roots** | A client can tell a server which filesystem directories (or other URI scopes) it's allowed to operate within |

You'll build and use tools, resources, and prompts throughout this level.
Sampling and roots are proper, hands-on topics in Level 2 and Level 3 — for
now, just know they exist and which direction they flow.

## How It Actually Works

The connection between a client and a server goes through a fixed lifecycle
every single time, regardless of transport:

1. **Transport connects.** For a local server this means the host spawns
   your server as a subprocess and opens its stdin/stdout; for a remote
   server it means an HTTP connection is established. Either way, no MCP
   messages have been exchanged yet — just a raw channel.
2. **`initialize` request.** The client sends an `initialize` request
   containing its own protocol version and the capabilities *it* supports
   (e.g. whether it can handle sampling requests).
3. **`initialize` response.** The server replies with its protocol version
   and the capabilities *it* supports — which of tools, resources, and
   prompts it actually implements, plus any optional features within each.
4. **`notifications/initialized`.** The client sends this one-way
   notification confirming it received and accepted the server's
   capabilities. Only after this point is the connection considered fully
   open.
5. **Normal operation.** Only now will the client send `tools/list`,
   `resources/read`, and so on. A server that receives one of these before
   the handshake completes is within its rights to reject it.

This matters practically: the SDK you'll use in the next lesson handles this
handshake for you automatically, but when something is silently not working
later in this course — a tool doesn't show up, a resource read hangs — the
first thing worth checking is whether the handshake actually completed.

## Exercise

For each of these three scenarios, write one sentence identifying which
primitive (tool, resource, or prompt) fits best, and why:

1. An assistant needs to read the contents of `README.md` in the user's
   project so it can answer a question about the project.
2. A user wants a one-click way to generate a standardized "weekly status
   update" write-up, filling in a project name and a list of accomplishments.
3. An assistant needs to create a new GitHub issue based on a bug the user
   just described.
