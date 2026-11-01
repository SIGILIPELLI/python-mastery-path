---
description: "A tool's inputSchema is JSON Schema, and a well-written one — with enums, required fields, and tight constraints — stops bad calls before your handler code ever runs."
---

# 06 · Structured Output & Tool Input Schemas

Level 1 let type hints generate a tool's schema automatically. That's fine
for `add(a: int, b: int)`. Real tools need real constraints — a status that
can only be one of three values, a nested object, a field that's optional
with a default. This lesson goes under the hood of what that schema
actually is, and how to shape it on purpose.

## What a tool's schema actually looks like

Every tool's `inputSchema` is plain JSON Schema. This is what `FastMCP`
generates for:

```python
from typing import Literal

@mcp.tool()
def create_ticket(
    title: str,
    priority: Literal["low", "medium", "high"],
    assignee: str | None = None,
) -> str:
    """Creates a support ticket."""
    ...
```

```json
{
  "type": "object",
  "properties": {
    "title": { "type": "string" },
    "priority": { "type": "string", "enum": ["low", "medium", "high"] },
    "assignee": { "type": ["string", "null"] }
  },
  "required": ["title", "priority"]
}
```

This schema is what the model actually sees when deciding how to call the
tool. A tight schema — the `enum` on `priority` especially — makes it far
less likely the model ever sends `"priority": "urgent"` by mistake, because
`"urgent"` was never a valid option it could have picked from.

## Nested objects

```python
from pydantic import BaseModel

class Address(BaseModel):
    street: str
    city: str
    zip_code: str

@mcp.tool()
def ship_order(order_id: str, address: Address) -> str:
    """Ships an order to the given address."""
    ...
```

A Pydantic model as a parameter type produces a nested `object` schema
automatically — `address` becomes `{"type": "object", "properties": {
"street": ..., "city": ..., "zip_code": ... }}` — and the SDK validates and
parses the incoming JSON into a real `Address` instance before your handler
ever runs.

## Structured tool output

A tool doesn't have to return only free text. Returning a Pydantic model (or
a `dict`) lets the SDK attach a matching **output schema** and send back
structured content a client can parse programmatically, in addition to a
text fallback for the model to read directly:

```python
class TicketResult(BaseModel):
    ticket_id: str
    status: str

@mcp.tool()
def create_ticket(title: str, priority: Literal["low", "medium", "high"]) -> TicketResult:
    """Creates a support ticket and returns its id and status."""
    ticket_id = f"T-{next_id()}"
    return TicketResult(ticket_id=ticket_id, status="open")
```

A client that wants to chain this ticket id into another tool call can read
it directly from the structured result instead of parsing it back out of
prose text.

## Validation errors the model can act on

When a call doesn't match the schema, don't let your handler raise a bare
exception with a Python stack trace — return (or raise, through the SDK's
own error path) a message that tells the model specifically what was wrong:

```python
@mcp.tool()
def create_ticket(title: str, priority: str) -> str:
    """Creates a support ticket. priority must be low, medium, or high."""
    if priority not in ("low", "medium", "high"):
        raise ValueError(
            f"priority must be one of 'low', 'medium', 'high' — got {priority!r}"
        )
    ...
```

A specific error like this gives the model everything it needs to retry the
call correctly on its next attempt. A bare traceback doesn't.

## Exercise

Take the `ship_order` tool above and add a `quantity: int` field with a
constraint that it must be at least 1 (use Pydantic's `Field(ge=1)`). Call
the tool through the Inspector with `quantity: 0` and `quantity: -5` and
confirm you get a clear validation error in both cases rather than the
handler silently running with an invalid quantity.
