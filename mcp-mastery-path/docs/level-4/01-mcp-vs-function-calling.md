---
description: "An MCP tool isn't a new way for a model to call functions — at request time it gets flattened into the exact same function-calling schema the model API already expects."
---

# 01 · MCP vs. Function Calling vs. LangChain Tools

If you've used an LLM API's "function calling" or "tool use" feature before,
MCP can look redundant at first glance — doesn't the model already know how to
call tools? The confusion is understandable, but the two sit at different
layers, and a popular framework abstraction sits at a third. This lesson
draws the lines precisely.

## Function calling: a model-API-level feature

Function/tool calling is a capability of the model's own API. You send the
model a list of tool definitions (name, description, JSON Schema for
arguments) alongside your prompt. The model, instead of just emitting text,
can emit a structured request to call one of those tools:

```json
{
  "type": "tool_use",
  "name": "get_weather",
  "input": {"city": "Austin"}
}
```

Your application code is entirely responsible for: supplying that tool list,
noticing the model asked for a tool call, actually running the corresponding
function, and feeding the result back into the conversation so the model can
continue. The model API has no idea where `get_weather`'s implementation
lives, how it's authenticated, or whether it's even safe to run. That's 100%
on you, and it's the same amount of "on you" whether you have one tool or a
hundred.

## MCP: a protocol for exposing and discovering those tools

MCP doesn't replace function calling — it standardizes the *other* side of
the equation: how an application discovers what tools exist, what they do,
how to call them, and how to get data and reusable prompts from external
systems, all through one consistent protocol instead of bespoke code per
integration.

A host application (say, an IDE assistant) connects to one or more MCP
servers, asks each one "what tools do you have?" via `tools/list`, and gets
back exactly the kind of tool definitions a model's function-calling API
wants: name, description, JSON Schema. The host then hands those definitions
to the model as part of its normal function-calling flow. When the model asks
to call one, the host routes that call to the right MCP server via
`tools/call`, gets the result back over the protocol, and feeds it to the
model — using the exact same function-calling mechanism it always has.

MCP is the plumbing that fills the tool list and executes the calls. Function
calling is still the thing the model API actually does.

## Where LangChain Tools fit in

Frameworks like LangChain define their own `Tool` abstraction — a Python
object with a name, description, and a callable — used to build agents
within that framework. A LangChain `Tool` isn't a competing protocol; it's a
framework-internal interface. The practical relationship is:

```python
from langchain_mcp_adapters.tools import load_mcp_tools
from mcp import ClientSession

async def build_langchain_tools(session: ClientSession):
    # Connects to an MCP server, lists its tools, and wraps each one
    # as a LangChain Tool the framework's agent loop can call directly.
    tools = await load_mcp_tools(session)
    return tools
```

An adapter like this connects to an MCP server, calls `tools/list`, and
wraps each MCP tool as a LangChain `Tool` whose underlying implementation
calls `tools/call` on the MCP session. LangChain gets to keep its own agent
abstractions; MCP gets to be the thing that actually talks to the external
system. The same pattern repeats across other frameworks (LlamaIndex,
AutoGen, and others each ship or support similar MCP adapters) — MCP servers
become a portable backend any of them can plug into, instead of writing a
GitHub integration once per framework.

## When each is the right choice

- **Just need the model to call a couple of functions you already wrote, in
  one app, with no reuse goal?** Plain function calling is simpler — don't
  reach for MCP just because it exists.
- **Building or using a tool/data integration you want any MCP-compatible
  host to be able to use** (your own app today, a different app tomorrow,
  someone else's app ever) — that's exactly what MCP is for.
- **Already committed to a framework like LangChain for agent orchestration,
  but want your tools to also work outside that framework?** Build an MCP
  server, then use the framework's MCP adapter to pull those tools in. You
  get framework-native usage and portability at the same time.

## How It Actually Works

The path from "you wrote an MCP tool" to "the model actually calls it" runs
through several translations, not one:

1. **Your server defines a tool.** With the Python SDK's `@mcp.tool()`
   decorator, your function's type hints and docstring become a JSON Schema
   tool definition the server can report.
2. **The host asks for the list.** On connecting, the host's MCP client
   sends `tools/list`; the server responds with every registered tool's
   name, description, and `inputSchema` (plain JSON Schema).
3. **The host reshapes that into the model API's format.** Every model
   provider has its own expected tool-definition shape even though most are
   JSON-Schema-based — field names and wrapping differ slightly between, say,
   Claude's API and another provider's. The host (or an SDK's model adapter
   layer) does this reshaping; MCP's `inputSchema` is the common source of
   truth it reshapes *from*.
4. **The model emits a call in its own API's native format** — it never sees
   MCP at all, only the function-calling format it was given.
5. **The host maps the call back to MCP.** It matches the model's tool-call
   name back to the originating server and sends a `tools/call` request with
   the model-supplied arguments.
6. **The result comes back over MCP, then gets reshaped again** into
   whatever "tool result" format the model API expects, and the model
   continues the conversation.

MCP never talks to the model directly. It's the standardized layer the host
sits between to avoid writing that discovery-and-execution plumbing once per
integration per model provider.

## Exercise

Pick any two tools from a server you built in an earlier level (or write two
small ones now). Write out, by hand, what each tool's `inputSchema` looks
like as returned by `tools/list`. Then write a short paragraph for each
tool describing in plain English what you'd expect a host to need to change
to present that same schema to a specific model API of your choice (you
don't need real API docs open — reason about what a model-facing function
definition typically needs: a name, a description, and the parameters). This
is the translation step from "How It Actually Works" — the point is to see
concretely that MCP's schema and the model's function-calling schema are
related but not identical formats.
