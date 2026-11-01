---
description: "MCP connects an agent to its tools and data, not one agent to another — in a multi-agent system, MCP servers are usually what several independent agents share, not how they talk to each other."
---

# 04 · Multi-Agent Systems Built on MCP

It's tempting to reach for MCP as the answer to "how do my agents talk to
each other," but that's not what the protocol is for. This lesson is
deliberately about drawing that line clearly, then showing the pattern that
actually does work well: multiple agents, each with their own MCP client,
sharing a common set of MCP servers.

## What MCP is not: an agent-to-agent protocol

MCP connects a **host application** (which may itself be a single agent) to
**servers** that expose tools, resources, and prompts. There is no concept
in the spec of one agent sending a message to another agent as a peer — the
client/server relationship is inherently between an application and its
tool/data providers, not between two equally-capable agents negotiating a
task. If you need agent-to-agent coordination, that's a separate concern
your system needs to solve on top of (or alongside) MCP, not something MCP
hands you.

## What does work: shared servers, independent clients

The pattern that holds up in practice is each agent running its own MCP
client(s), independently connecting to the same servers your organization
already runs:

```
 Agent A (research)         Agent B (writer)         Agent C (reviewer)
      │  client                   │  client                 │  client
      ▼                           ▼                         ▼
 ┌─────────────────────────────────────────────────────────────┐
 │        Shared MCP servers: search, docs, file storage        │
 └─────────────────────────────────────────────────────────────┘
```

Each agent connects, lists tools, and calls them independently — there's no
MCP-level awareness that other agents exist. The servers don't know or care
how many clients are connected; each connection is just another client as
far as the protocol is concerned. This gives you real benefits without
inventing a new protocol:

- **One place to maintain the integration** (a search tool, a docs tool) no
  matter how many agents end up using it.
- **Consistent permissions and auditing**, since every agent's tool calls go
  through the same server-side logic, logging, and access control.
- **Agents can be added or removed freely** without touching the servers at
  all.

## Where actual coordination happens

If agent A's output needs to become agent B's input, or agent C needs to
know what A and B already did, that's orchestration logic your application
owns — a shared state store, a message queue, a workflow engine, or simply
one orchestrating process that calls each agent in sequence and passes
results along. A simple, concrete version: a coordinator process holds a
blackboard a task's results get written to, with each agent reading what it
needs from that blackboard before starting its own MCP-backed work, and
writing its results back when done. MCP is in this picture only as what each
agent uses to reach the outside world — the coordination itself happens
entirely outside the protocol.

```python
# a minimal coordinator — NOT part of MCP, just application logic
blackboard = {}

async def run_research_agent(session):
    results = await session.call_tool("search_web", {"query": "..."})
    blackboard["research"] = results

async def run_writer_agent(session):
    draft = await generate_draft(blackboard["research"])
    blackboard["draft"] = draft
    await session.call_tool("save_file", {"path": "draft.md", "content": draft})
```

## A note on emerging agent-to-agent protocols

Separate efforts exist in the wider ecosystem specifically aimed at
agent-to-agent communication — letting one agent discover and delegate work
to another agent as a peer, rather than to a tool. Those are a genuinely
different layer of the stack from MCP, and the two are complementary rather
than competing: an agent exposed via an agent-to-agent protocol might
internally use MCP to reach its own tools and data, the same way any other
MCP host would.

## Exercise

Sketch (in code or in a short diagram-in-prose) a two-agent system where
both agents connect independently to one shared MCP server exposing a
`search_docs` tool. Write the minimal coordinator logic that runs agent A
first, passes its result to agent B, and have agent B call the same shared
tool with a query derived from A's output. The point is to see, concretely,
that the "coordination" part is ordinary application code sitting entirely
outside of MCP.
