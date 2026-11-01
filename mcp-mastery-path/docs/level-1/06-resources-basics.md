---
description: "A resource is data the client reads on its own initiative; a tool is an action the model decides to take — mixing the two up produces a confusing server."
---

# 06 · Resources: Exposing Data to an LLM

## Resources vs. tools: the real distinction

It's tempting to think "a resource is just a tool that returns data," but
the distinction that actually matters is about **control**, not shape:

- A **tool** is called when the *model* decides, mid-conversation, that
  calling it will help answer the user. The model chooses the arguments.
- A **resource** is typically read because the *application or user*
  explicitly attached it — picked a file from a list, pasted a link, or the
  host proactively loaded it as context before the conversation even
  reaches the model.

A file's contents, a database record, a config value — things that are
simply *there* to be read, with no side effects and no decision-making
required — are resources. An action that changes something, searches with
arbitrary model-chosen parameters, or has side effects belongs as a tool.

## Exposing a resource

The `@mcp.resource()` decorator takes a URI and registers a function to
handle it. This lesson covers **static** URIs — fixed, exact strings.
Templated URIs with variable segments (`notes://{note_id}`, for example) are
a Level 2 topic, once you've got the fixed case solid.

```python
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("demo-server")

@mcp.resource("config://app-settings")
def get_app_settings() -> str:
    """The current application settings, as JSON."""
    return '{"theme": "dark", "notifications": true}'
```

The URI's scheme (`config://` here) is entirely up to you — MCP doesn't
mandate a fixed set of schemes. Pick something that describes what the
resource actually is: `file://`, `config://`, `notes://`, whatever reads
clearly for your server.

## Multiple resources

Just like tools, a server can expose as many resources as it needs:

```python
@mcp.resource("docs://readme")
def get_readme() -> str:
    """The project's README file."""
    with open("README.md") as f:
        return f.read()

@mcp.resource("docs://changelog")
def get_changelog() -> str:
    """The project's changelog."""
    with open("CHANGELOG.md") as f:
        return f.read()
```

A client calling `resources/list` gets back both URIs with their
descriptions, and can then `resources/read` whichever one it actually needs
— mirroring the `tools/list` → `tools/call` pattern from lesson 5, but for
reading instead of acting.

## When you genuinely need both

Nothing stops a server from offering a resource and a tool that overlap in
subject matter, as long as each is doing the job it's suited for:

```python
@mcp.resource("orders://all")
def all_orders() -> list[dict]:
    """The full current order list, as structured records."""
    return load_all_orders()

@mcp.tool()
def search_orders(status: str) -> list[dict]:
    """Search orders by status (e.g. 'shipped', 'pending')."""
    return [o for o in load_all_orders() if o["status"] == status]
```

The resource is the whole dataset, available for a client to load as
context whenever it wants. The tool is a model-driven, parameterized query
against that same data — the model decides what `status` to search for
based on what the user actually asked.

## Exercise

Add a resource `stats://summary` to a server of your own that returns a
short string summarizing some data you already have lying around (a word
count of a file, the number of lines in a log, anything). Confirm in the
Inspector that it shows up under `resources/list` and that reading it
returns the right content.
