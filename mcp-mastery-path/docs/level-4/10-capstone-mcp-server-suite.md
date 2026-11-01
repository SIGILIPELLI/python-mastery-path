---
description: "The capstone: a gateway in front of two or three real MCP servers, with OAuth, audit logging, tests, and a governance gate — every technique from all four levels, used together instead of in isolation."
---

# 10 · Capstone Project — A Production-Grade MCP Server Suite

This is the final project of the course. Everything from "What Is MCP & Why
It Exists" through yesterday's lesson on emerging trends has been building
toward this: a small but genuinely production-shaped suite of MCP servers,
not a single toy example. The goal isn't to follow a tutorial to the end —
it's to make the real design decisions yourself, using the vocabulary and
techniques this course gave you, and end up with something you could
actually point to as evidence you've mastered this material.

## What you're building

A gateway (Level 4, lesson 5) sitting in front of **two or three backend MCP
servers** of your own choosing, with:

- **Authentication** on the gateway using the OAuth 2.1 pattern from Level 2
- **Audit logging** of every tool call, in the shape from yesterday's lesson
- **An approval gate** on at least one genuinely state-changing tool
- **Tests** covering both individual backend tool logic and the gateway's
  routing/authorization behavior
- **Observability** — structured logs and request correlation, from Level 3

You get to choose what the backend servers actually *do*. Pick something you
can build real, working tools for rather than stubs — a notes/tasks server
like Level 1's project, a wrapper around a real public API like Level 2's
GitHub project, a retrieval server backed by a small local dataset (Level
4, lesson 3) — any combination of two or three is fine, as long as each one
has at least two real tools.

## Architecture overview

```
                         ┌───────────────────────┐
  MCP client (you,  ───► │   Gateway (FastMCP)    │
  or Inspector)          │  - OAuth-authenticated │
                         │  - namespaces tools     │
                         │  - authorizes per-tool  │
                         │  - audit-logs every call│
                         └──────────┬─────────────┘
                                    │  proxies tools/call, tools/list
                     ┌──────────────┼──────────────┐
                     ▼              ▼              ▼
              ┌───────────┐  ┌───────────┐  ┌───────────┐
              │ Backend A │  │ Backend B │  │ Backend C │
              │ (stdio or │  │ (stdio or │  │ (optional)│
              │  HTTP)    │  │  HTTP)    │  │           │
              └───────────┘  └───────────┘  └───────────┘
```

A client only ever talks to the gateway. The gateway is the only thing that
knows how many backends exist, where they live, and who's allowed to call
what on them — exactly the design from Level 4, lesson 5, now with real
auth and audit logging layered on top of it.

## Required components checklist

Work through this as your actual build checklist, not just a reading list:

- [ ] **Two or three backend MCP servers**, each with at least two real
      tools (not stubs that return hardcoded data)
- [ ] **A gateway** that aggregates all backend tools into one `tools/list`
      response, with tool names namespaced by backend (`notes.add_task`,
      `github.create_issue`, etc.)
- [ ] **Routing**: the gateway correctly forwards a `tools/call` for a
      namespaced tool to the right backend and returns its result
      unmodified
- [ ] **OAuth-based authentication** on the gateway's HTTP transport —
      a client without a valid token is rejected before any tool call is
      considered
- [ ] **Per-client authorization** — at least two distinct "client
      identities" with different allowed tool sets, enforced at the
      gateway (reuse or extend the `authorize()` pattern from lesson 5)
- [ ] **Audit logging** of every tool call through the gateway: tool name,
      arguments (sensitive fields redacted), caller identity, timestamp,
      outcome — written somewhere durable, not just printed to a console
      that scrolls away
- [ ] **An approval gate** on at least one state-changing tool, following
      the pattern from yesterday's lesson — calling it should visibly pause
      for approval, and a denial should prevent the underlying action from
      happening
- [ ] **Structured, correlated logging** — every log line for a single
      end-to-end request (gateway receives call → forwards to backend →
      backend responds → gateway responds) should share a request ID you
      can grep for
- [ ] **A test suite** covering: at least one backend tool's logic directly
      (unit-style, no protocol layer involved), and the gateway's
      authorization behavior (a disallowed tool call for a given identity
      is actually rejected, not silently allowed)
- [ ] **A README** for the whole suite: what it does, how to run it, and a
      short "architecture decisions" section explaining the choices you
      made and why — the kind of document you'd actually want if you
      inherited this project from someone else

## Suggested build phases

Don't try to build all of this at once. A workable order:

1. **Backends first, standalone.** Get your two or three backend servers
   working and manually testable with the MCP Inspector *before* any
   gateway exists. Confirm each one's tools behave correctly in isolation.
2. **Naive gateway, no auth yet.** Build the proxying/namespacing gateway
   from lesson 5 with no authentication at all — just prove the routing
   works end to end: a client calls the gateway, the gateway calls the
   right backend, the result comes back correctly.
3. **Add authentication.** Layer OAuth 2.1 on the gateway's HTTP transport.
   Confirm an unauthenticated call is rejected and an authenticated one
   still works.
4. **Add authorization, audit logging, and the approval gate together** —
   they naturally sit in the same code path (every call passes through the
   gateway's dispatch logic), so building them in the same pass keeps that
   logic coherent rather than bolted on in three separate, possibly
   conflicting places.
5. **Add structured, correlated logging** across the whole request path.
6. **Write the tests last, against the real behavior you've built** — not
   speculative tests against behavior you haven't implemented yet.
7. **Write the README.**

## A starting skeleton for the gateway's dispatch path

This is intentionally incomplete — it shows where each piece from the
checklist plugs in, not a finished implementation:

```python
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("capstone-gateway")

async def dispatch_tool_call(caller_identity: str, tool_name: str, arguments: dict):
    # 1. Authorization
    if not is_authorized(caller_identity, tool_name):
        audit_log(tool_name, arguments, caller_identity, outcome="denied")
        raise PermissionError(f"{caller_identity} is not authorized for {tool_name}")

    # 2. Approval gate (only for tools that need it)
    if requires_approval(tool_name):
        approval = await request_human_approval(tool_name, arguments)
        if not approval.approved:
            audit_log(tool_name, arguments, caller_identity, outcome="approval_denied")
            return {"status": "denied", "reason": approval.denial_reason}

    # 3. Route to the correct backend
    backend_name, real_tool_name = tool_name.split(".", 1)
    session = await get_backend_session(backend_name)
    result = await session.call_tool(real_tool_name, arguments)

    # 4. Audit the completed call
    audit_log(tool_name, arguments, caller_identity, outcome="success")
    return result
```

Everything this function calls — `is_authorized`, `requires_approval`,
`request_human_approval`, `get_backend_session`, `audit_log` — is yours to
design and implement, pulling directly from the earlier lessons each one
corresponds to.

## Deliverable checklist (what "done" looks like)

- [ ] All items in the Required Components checklist are implemented and
      actually work, not just stubbed
- [ ] You can start the whole suite, connect with the MCP Inspector (or a
      small client script) through the gateway, authenticate, and
      successfully call at least one tool on each backend
- [ ] A denied authorization attempt and a denied approval request both
      produce a clean, logged failure rather than a crash
- [ ] The test suite passes and actually exercises the authorization and
      approval logic, not just the happy path
- [ ] The README would let someone else run and understand this project
      without asking you questions

This project is meant to take real, multi-day effort — treat it as evidence
you can design and build production-shaped MCP infrastructure, not as a
checkbox to rush through. Congratulations on reaching the end of the course.
