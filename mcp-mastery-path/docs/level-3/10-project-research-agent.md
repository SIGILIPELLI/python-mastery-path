---
description: "The whole point of this project is that the orchestration layer you build is what makes three independently simple servers behave like one reliable system — the servers themselves don't need to know about each other."
---

# 10 · Project — Orchestrating 3 MCP Servers for a Research Agent

This level's capstone: build a simple research agent backed by three MCP
servers — web search, notes, and file output — connected through one
multi-server client that applies the patterns from this level: namespacing,
error handling, and graceful degradation. The goal isn't a clever agent
loop; it's a correctly-engineered orchestration layer around tools that are
individually trivial.

## What you're building

A command-line tool that, given a research question, can:

1. Search the web for relevant information (`search` server).
2. Save interesting findings as notes (`notes` server — reuse/extend Level
   1's project).
3. Write a final summary document to disk (`files` server).

The interesting part isn't any single server — it's that the orchestration
layer survives one server being slow, one server being temporarily
unavailable, and tool names that would otherwise collide (`search` as a
tool name is tempting to reuse across more than one of these servers).

## The three servers

**`search_server.py`** — one tool, `web_search(query: str) -> list[dict]`,
returning a list of `{"title": str, "url": str, "snippet": str}`. For this
project, a server that hits a real search API is ideal, but a server that
reads from a small local JSON file of canned results is a completely valid
substitute — the orchestration logic being exercised doesn't care where the
results come from.

**`notes_server.py`** — reuse Level 1's project server, or rebuild a
minimal version with `add_note(title: str, content: str) -> dict` and
`list_notes() -> list[dict]`, persisted to a local JSON file.

**`files_server.py`** — one tool, `write_file(path: str, content: str) ->
dict`, which should apply the roots-style containment check from lesson 5
so it can only write inside a designated output directory — don't skip this
part; a file-writing tool with no path containment check is exactly the
kind of thing lesson 6 warned about.

## The orchestration layer: what to build yourself

Starting from the `MultiServerClient` in lesson 1, build a
`ResearchAgent` class with roughly this shape:

```python
class ResearchAgent:
    def __init__(self, client: MultiServerClient):
        self.client = client
        self.namespaced_catalog: dict = {}  # built via lesson 2's namespacing

    async def setup(self):
        await self.client.connect_all()
        raw_catalog = await list_all_tools_resilient(self.client)  # lesson 3's resilient version
        self.namespaced_catalog = build_namespaced_catalog(raw_catalog)  # lesson 2

    async def research(self, question: str, max_results: int = 5) -> str:
        """
        1. Call search__web_search with the question as the query.
        2. For each promising result (you decide "promising" — e.g. the
           top N, or ones whose snippet contains question keywords),
           call notes__add_note to save title + snippet.
        3. Call notes__list_notes to pull everything saved this session.
        4. Build a plain-text summary from the saved notes.
        5. Call files__write_file to save that summary to an output path.
        6. Return the path that was written.
        Use call_with_retry (lesson 3) around each tool call, and make sure
        a failure in step 2 for one result doesn't abort the whole research
        run — log it and continue with the rest.
        """
        ...
```

The docstring above is the spec; filling in the method body — deciding how
results get filtered, how the summary gets formatted, and making sure
errors in one step don't take down the whole pipeline — is the actual
exercise.

## Required behavior (this is what gets checked, not the internals)

- Running `research("what is MCP roots?")` against your three connected
  servers produces a written summary file and returns its path.
- If the `search` server is killed before `research()` runs, the agent
  should report a clear error ("search unavailable") rather than crashing
  with an unhandled exception or hanging.
- If `notes__add_note` fails for one search result (simulate this by making
  one canned result deliberately cause an error in your notes server), the
  other results should still get saved, and the final summary should
  reflect whichever notes succeeded.
- Tool names across all three servers must be namespaced
  (`search__web_search`, `notes__add_note`, `files__write_file`) — direct,
  unprefixed names should not appear anywhere in the orchestration code
  that routes calls.
- `files__write_file` must reject a path that attempts to escape the
  configured output directory (test this explicitly with a `../`-based
  path).

## Suggested build order

1. Get all three servers running individually and verify each with the
   MCP Inspector before wiring anything together.
2. Build `ResearchAgent.setup()` and confirm the namespaced catalog
   contains exactly the tools you expect, correctly prefixed.
3. Implement `research()` against the happy path first (all three servers
   up, every call succeeds).
4. Add the resilience behavior — kill the search server mid-run and
   confirm you get a clear error instead of a crash; make one notes call
   fail and confirm the run still completes with partial results.
5. Add the path-containment test for `files__write_file` last, since it's
   the one place a bug has a real consequence (writing outside the
   intended directory) rather than just a worse user experience.

## Exercise

Once the above is working, add a fourth capability without touching the
other three servers or the `ResearchAgent` orchestration logic: a simple
in-memory cache (lesson 8) in front of `search__web_search` keyed on the
query string, so asking the same research question twice in one session
doesn't re-issue the search. This should be addable purely by wrapping the
call site in `research()` — if it requires changing the search server
itself, you've coupled something that shouldn't be coupled.
