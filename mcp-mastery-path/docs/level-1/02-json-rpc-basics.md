---
description: "Every MCP message is a JSON-RPC 2.0 message; a request without an id is a notification, and the server must never reply to one."
---

# 02 · JSON-RPC 2.0: The Wire Protocol Underneath

MCP doesn't invent its own wire format. Every message that flows between an
MCP client and an MCP server is a **JSON-RPC 2.0** message — a small, well
established spec for calling methods and getting results back as JSON.
Understanding JSON-RPC directly demystifies everything MCP does later: tool
calls, resource reads, prompt fetches, even the connection handshake are all
just JSON-RPC requests and responses with MCP-specific method names and
payloads.

## The three message shapes

JSON-RPC 2.0 has exactly three kinds of messages.

**A request** — asks the other side to do something and expects a reply:

```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "tools/call",
  "params": {
    "name": "add",
    "arguments": { "a": 2, "b": 3 }
  }
}
```

**A response** — the reply to a request, matched by `id`, with either a
`result` or an `error`, never both:

```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "result": {
    "content": [{ "type": "text", "text": "5" }]
  }
}
```

**A notification** — a one-way message with no `id` and no reply expected:

```json
{
  "jsonrpc": "2.0",
  "method": "notifications/initialized",
  "params": {}
}
```

That's the entire vocabulary. `method` is always a string naming the
operation. `params` carries whatever arguments that operation needs. `id`
is how a response gets matched back to the request that triggered it —
present on requests and their responses, absent on notifications.

## Core MCP methods, in JSON-RPC terms

Every MCP operation you'll learn in this course is one of these shapes with
a specific `method` name:

| MCP operation | `method` | Request or notification? |
|---|---|---|
| Open a connection | `initialize` | Request |
| Confirm the connection is ready | `notifications/initialized` | Notification |
| List available tools | `tools/list` | Request |
| Call a tool | `tools/call` | Request |
| List available resources | `resources/list` | Request |
| Read a resource | `resources/read` | Request |
| List available prompts | `prompts/list` | Request |
| Get a prompt | `prompts/get` | Request |

You'll meet `initialize` and the three `*/list` + `*/call`-or-`/read`-or-`/get`
pairs properly in the next two lessons. For now, just notice: they're all
plain JSON-RPC requests with an MCP-specific `method` string.

## A full exchange over stdio

Here's what actually crosses the wire for a single tool call, assuming the
connection is already initialized. Each JSON-RPC message is sent as one line
of JSON, terminated by a newline — this matters later when you build a
server, because printing anything else to stdout will break this framing.

Client sends (asking what tools exist):

```json
{"jsonrpc":"2.0","id":2,"method":"tools/list","params":{}}
```

Server replies:

```json
{"jsonrpc":"2.0","id":2,"result":{"tools":[{"name":"add","description":"Add two numbers","inputSchema":{"type":"object","properties":{"a":{"type":"integer"},"b":{"type":"integer"}},"required":["a","b"]}}]}}
```

Client sends (actually calling it):

```json
{"jsonrpc":"2.0","id":3,"method":"tools/call","params":{"name":"add","arguments":{"a":2,"b":3}}}
```

Server replies:

```json
{"jsonrpc":"2.0","id":3,"result":{"content":[{"type":"text","text":"5"}]}}
```

Four messages, two request/response pairs, matched by `id`. Nothing more
exotic is happening underneath any MCP tool call you'll make in this course.

## How It Actually Works

1. **A missing `id` is the entire signal for "notification."** There's no
   separate `type` field distinguishing a request from a notification — the
   spec says: if `id` is present, it's a request and a response is required;
   if `id` is absent, it's a notification and the receiver must not reply.
   `notifications/initialized` is a notification precisely because the
   client doesn't need (and the server must not send) a response to it.

2. **`id` can be a number or a string**, and the sender chooses it — it just
   has to be unique among that sender's currently-outstanding requests so
   responses can be matched back correctly. Most SDKs auto-increment an
   integer counter for you.

3. **Errors are a specific object shape, not just any JSON.** A JSON-RPC
   error response looks like:
   ```json
   {"jsonrpc":"2.0","id":3,"error":{"code":-32602,"message":"Invalid params"}}
   ```
   `code` is a signed integer (the JSON-RPC spec reserves a range of
   negative codes for protocol-level errors like "method not found" or
   "invalid params"; MCP and application code can define their own codes
   outside that reserved range for domain-specific failures), and `message`
   is a short human-readable string. An optional `data` field can carry
   additional structured detail.

4. **Batching exists in the JSON-RPC 2.0 spec** (sending an array of
   requests in one message) but MCP does not use it — every MCP message is
   sent as a single JSON object per line, never an array.

## Exercise

Without running any code, hand-write the four JSON-RPC messages (two
requests, two responses) for a tool call to a tool named `get_weather` that
takes one argument, `city` (a string), and returns the text `"Sunny, 22°C"`.
Use `id: 10` for the `tools/call` request/response pair. You don't need the
`tools/list` exchange this time — just the call itself plus its response.
