---
description: "A resource template uses an RFC 6570 URI pattern like notes://{note_id} so one handler can serve an unbounded family of resources instead of one fixed URI each."
---

# 04 · Resource Templates & Dynamic URIs

In Level 1, every resource had a fixed URI — `config://settings`,
`notes://all`. That's fine for things that genuinely are singular. It falls
apart the moment you want to expose one resource *per item* in a collection
that could have thousands of entries. You don't want to hand-register a
thousand `@mcp.resource()` functions. You want one handler that serves
`notes://{note_id}` for any `note_id`.

## Registering a templated resource

```python
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("notes-templated")

notes = {
    1: "Buy milk",
    2: "Finish MCP lesson",
    3: "Call the dentist",
}

@mcp.resource("notes://{note_id}")
def get_note(note_id: str) -> str:
    """Returns a single note by id."""
    note = notes.get(int(note_id))
    if note is None:
        raise ValueError(f"No note with id {note_id}")
    return note
```

The `{note_id}` segment is a URI template variable — RFC 6570 syntax, the
same templating style used in a lot of REST API tooling. When a client reads
`notes://7`, the SDK matches it against the registered template, extracts
`note_id = "7"`, and calls `get_note(note_id="7")`.

## Multiple variables

Templates aren't limited to one variable:

```python
@mcp.resource("notes://{year}/{month}/{note_id}")
def get_dated_note(year: str, month: str, note_id: str) -> str:
    """Returns a note filed under a specific year/month."""
    ...
```

A client reading `notes://2026/11/7` gets `year="2026"`, `month="11"`,
`note_id="7"` passed to the handler.

## Discoverability: how does a client know what to fill in?

A plain fixed-URI resource shows up directly in `resources/list`. A
templated resource can't — there's no finite list of every possible
`note_id`. Instead it appears as a **resource template**, returned from
`resources/templates/list`, describing the pattern itself (`notes://{note_id}`)
plus a human-readable name and description. A client (or the model behind
it) reads that template, works out a concrete `note_id` it's interested in
— usually because a tool call just told it one exists — and then reads the
fully-resolved URI.

This is why templated resources almost always appear alongside a tool that
can enumerate the valid ids:

```python
@mcp.tool()
def list_note_ids() -> list[int]:
    """Returns every valid note id, for use with the notes://{note_id} resource."""
    return list(notes.keys())
```

Now the model has a path: call `list_note_ids`, see `[1, 2, 3]`, then read
`notes://2` to get that specific note's content.

## Exercise

Extend the `get_note` handler so that reading an id that doesn't exist
returns a clear, useful error (the `ValueError` above is a start, but check
what text actually reaches a client calling it through the Inspector) rather
than a raw Python traceback. Then add `list_note_ids` as shown above and
verify, using the Inspector, that you can go from calling the tool, to
reading a templated resource for one of the returned ids, to reading an
id that doesn't exist and seeing your error message instead of a crash.
