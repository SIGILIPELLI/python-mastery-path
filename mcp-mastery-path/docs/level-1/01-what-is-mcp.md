---
description: "MCP turns the M×N integration problem (every AI app × every tool) into an M+N problem, the same way the Language Server Protocol did for editors and languages."
---

# 01 · What Is MCP & Why It Exists

## The problem: every app, every tool, a bespoke integration

Say you're building an AI assistant that needs to read a user's calendar and
post messages to Slack. Without a shared protocol, you write:

- A calendar integration specific to your assistant's internals
- A Slack integration specific to your assistant's internals

Now say a second assistant wants the same two capabilities. It writes its
own calendar integration and its own Slack integration — different code,
different auth handling, different error conventions, even though the
underlying capability ("read events", "post a message") is identical.

With **M** AI applications and **N** tools/data sources, you end up writing
roughly **M × N** integrations. Every new assistant re-implements every
integration. Every new tool has to be wired into every assistant that wants
to use it.

## The fix: a shared protocol in the middle

The Model Context Protocol (MCP) defines a standard way for an AI
application to discover and call tools, read data, and use prompt templates
— regardless of which AI application it is, and regardless of which tool or
data source is on the other end.

With MCP, the calendar integration is written **once**, as an MCP server.
Any MCP-compatible AI application can connect to it and immediately get
calendar tools, with no calendar-specific code in the application itself.
The Slack integration is written once too. The math changes from **M × N**
to **M + N**: M applications each implement the client side of MCP once, N
tools each implement the server side of MCP once, and any client can talk to
any server.

```text
Without MCP (M × N):              With MCP (M + N):

Assistant A ─── Calendar          Assistant A ─┐
Assistant A ─── Slack                          ├── MCP ──── Calendar Server
Assistant B ─── Calendar          Assistant B ─┘        └── Slack Server
Assistant B ─── Slack
```

## Why this will look familiar: the Language Server Protocol

MCP was directly inspired by the **Language Server Protocol (LSP)**, which
solved the exact same shape of problem for code editors. Before LSP, every
editor (VS Code, Vim, Emacs, Sublime...) had to implement its own
autocomplete, go-to-definition, and linting support for every programming
language it wanted to support well — again, an M × N problem.

LSP fixed it: a language's tooling author writes **one** language server
(for Python, for Rust, for Go...). Any LSP-compatible editor can talk to any
language server over the same protocol. Your editor doesn't need to know
anything about Rust's compiler internals — it just needs to speak LSP, and
the Rust language server handles the rest.

MCP applies the same idea to AI applications and the tools/data they need:
write the tool integration once, as an MCP server, and every MCP-compatible
AI application — Claude Desktop, an IDE, a custom agent — can use it without
custom code.

## A concrete example

Imagine an MCP server that exposes two tools against a calendar API:
`list_events(start_date, end_date)` and `create_event(title, start, end)`,
and a separate MCP server that exposes `post_message(channel, text)` against
Slack's API.

An AI assistant connected to both servers can be asked, in plain language,
"Check my calendar for conflicts tomorrow afternoon and post a summary to
#team-standup" — and it will call `list_events`, reason about the results,
then call `post_message`, without the assistant's own codebase containing a
single line of calendar-specific or Slack-specific code. All of that logic
lives in the two servers, where it was written once.

This course builds exactly that kind of server, starting from scratch, over
the next 40 lessons — level 1 gets you to a real, working local server by
lesson 10.

## Exercise

Without writing any code yet, sketch (in a text file or on paper) an MCP
server you'd want to exist for a tool or data source you use daily — pick
something concrete, like "my to-do app" or "my team's issue tracker." Write
down:

1. The server's name
2. Two or three tools it would expose, with a one-line description of what
   each does
3. One resource it might expose (a piece of data an assistant could read,
   as opposed to an action it could take)

Keep this sketch — you'll build something similar as this level's project.
