---
description: "The JSON Schema a model sees for a tool's arguments is generated straight from your function's Python type hints — no schema to write by hand."
---

# 05 · Tools: Exposing Functions to an LLM

A **tool** is an action the model can decide to take — look something up,
change something, compute something. Lesson 4 already showed the basic
shape; this lesson goes one level deeper into how a plain function becomes a
tool the model can actually use well.

## Type hints become the schema

Recall `tools/list` returns an `inputSchema` — a JSON Schema describing what
arguments a tool accepts. With `FastMCP`, you never write that schema by
hand. It's generated directly from your function's type hints:

```python
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("demo-server")

@mcp.tool()
def convert_currency(amount: float, from_currency: str, to_currency: str) -> str:
    """Convert an amount from one currency to another using a fixed demo rate."""
    rates = {"USD": 1.0, "EUR": 0.92, "GBP": 0.79}
    if from_currency not in rates or to_currency not in rates:
        return f"Unsupported currency: must be one of {list(rates)}"
    usd = amount / rates[from_currency]
    converted = usd * rates[to_currency]
    return f"{amount} {from_currency} = {converted:.2f} {to_currency}"
```

`amount: float`, `from_currency: str`, and `to_currency: str` become three
required properties in the generated `inputSchema`, typed `number` and
`string` respectively. There's no separate schema file or decorator argument
to keep in sync — the signature *is* the source of truth.

## The docstring is what the model reads

The model doesn't see your Python source code. What it sees, via
`tools/list`, is the tool's `name`, its `description` (taken from the
docstring), and its `inputSchema`. A vague docstring produces a tool the
model will use incorrectly or not at all; a precise one does the opposite.
Compare:

```python
@mcp.tool()
def search(q: str) -> str:
    """Search."""  # the model has almost nothing to go on
    ...

@mcp.tool()
def search_orders(customer_email: str) -> str:
    """Look up all orders placed by a customer, given their email address.
    Returns order IDs, dates, and statuses."""
    ...
```

The second version tells the model exactly when to reach for this tool and
what it will get back — that description is doing real work.

## Multiple tools, one server

A single server can expose as many tools as make sense for the thing it
wraps. Each one just needs its own `@mcp.tool()`-decorated function:

```python
@mcp.tool()
def list_orders(customer_email: str) -> str:
    """List all orders for a customer."""
    ...

@mcp.tool()
def get_order_status(order_id: str) -> str:
    """Get the current status of a single order by its ID."""
    ...

@mcp.tool()
def cancel_order(order_id: str) -> str:
    """Cancel an order by its ID, if it hasn't shipped yet."""
    ...
```

Each tool gets its own name, description, and schema in `tools/list` —
the model picks whichever one fits the user's request.

## Returning structured data

Everything so far returns a plain string, which becomes a single
`{"type": "text", "text": "..."}` content block in the `tools/call`
response. You can also return a `list` or `dict` of JSON-serializable data,
and `FastMCP` will serialize it for you — useful when the result has real
structure the model should reason over, like a list of order records rather
than a hand-formatted sentence:

```python
@mcp.tool()
def list_orders(customer_email: str) -> list[dict]:
    """List all orders for a customer as structured records."""
    return [
        {"order_id": "A1", "status": "shipped", "total": 42.50},
        {"order_id": "A2", "status": "processing", "total": 19.99},
    ]
```

## Exercise

Write a tool `word_count(text: str) -> dict` that returns a dictionary with
three keys: `"characters"` (total character count), `"words"` (count of
whitespace-separated tokens), and `"lines"` (count of newline-separated
lines). Give it a docstring precise enough that a model would know exactly
when to call it, then verify it in the Inspector with a short multi-line
string.
