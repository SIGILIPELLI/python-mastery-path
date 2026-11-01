---
description: "sampling/createMessage flips the usual direction: instead of a client asking a server to do something, the server asks the client's own LLM to generate text for it."
---

# 05 · Sampling: Letting a Server Ask the LLM for Completions

Every primitive so far flows one way: the client (on the model's behalf)
calls a tool, reads a resource, or fetches a prompt from the server.
**Sampling** is the one primitive that flows the other way — a server, in
the middle of handling something, asks the client's LLM to generate text
for it.

## Why a server would ever want this

Imagine a tool that fetches a long web page and is supposed to return a
short summary. Two ways to build that:

- The server calls out to its own LLM API, using its own API key, to
  generate the summary.
- The server asks the **client's** LLM — the same model the user is already
  talking to — to generate the summary, via `sampling/createMessage`.

The second option means the server never needs its own model access, its
own API key, or its own usage bill. It borrows the model the user already
has, under the user's own approval.

## Requesting a completion from a tool handler

```python
from mcp.server.fastmcp import FastMCP
from mcp.server.fastmcp.server import Context

mcp = FastMCP("summarizer")

@mcp.tool()
async def summarize_url(url: str, ctx: Context) -> str:
    """Fetches a URL and returns a short summary of its content."""
    page_text = fetch_page_text(url)  # your own HTTP fetch, omitted here

    result = await ctx.session.create_message(
        messages=[
            {
                "role": "user",
                "content": {
                    "type": "text",
                    "text": f"Summarize this in two sentences:\n\n{page_text[:4000]}",
                },
            }
        ],
        max_tokens=200,
    )
    return result.content.text
```

The `Context` object gives a tool handler access to `ctx.session`, which is
the live connection back to the client — `create_message` sends a
`sampling/createMessage` request over that connection and awaits the
client's response.

## The approval step clients are expected to apply

A server asking to generate text on the user's model isn't free to do
silently — it still costs tokens and it's still the user's model being used
on the server's behalf. A well-behaved client:

- Shows the user (or at minimum logs, for an automated client) that a
  server is requesting a completion, including the proposed prompt.
- Lets the user approve, deny, or edit the request before it's sent to the
  model — exactly the same "human in the loop" expectation MCP applies to
  tool calls that do something consequential.
- Can apply its own model/size preferences — the server can suggest hints
  (e.g. "a fast, cheap model is fine for this"), but the client decides
  which model actually serves the request.

## How It Actually Works

1. **It's still just JSON-RPC, running in the opposite direction.** A
   `sampling/createMessage` request is sent by the server over the same
   connection a `tools/call` request travels — the server is just the one
   initiating this particular request instead of responding to one.
2. **The client, not the server, decides which model answers.** The
   server's request carries model preferences as *hints* (cost/speed/
   intelligence priorities), not a hard model selection. This is a
   deliberate design choice: it keeps model access, and therefore cost and
   capability, entirely under the user's and client's control.
3. **This is why MCP servers generally don't need LLM API keys of their
   own.** A server that only ever needs text generation as a sub-step of a
   tool can lean entirely on sampling instead of integrating a separate
   model provider — one less credential to manage, one less bill to pay.
4. **It composes with tool calls naturally.** From the model's point of
   view, calling `summarize_url` just returns a summary — it has no idea
   (and doesn't need to know) that the server itself asked another model
   invocation to produce that summary along the way.

## Exercise

Modify `summarize_url` so the sampling request explicitly asks for a
one-sentence summary instead of two, and add a `style: str` parameter to
the tool (e.g. `"neutral"`, `"casual"`) that gets folded into the prompt
sent via `create_message`. Call the tool twice with different `style`
values through the Inspector and confirm the returned summaries actually
differ in tone.
