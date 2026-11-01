---
description: "A transport's entire job is carrying JSON-RPC messages in both directions — everything above it in MCP doesn't know or care whether that happens over stdio, HTTP, or a WebSocket."
---

# 02 · Building a Custom Transport

Every MCP message — a tool call, a resource read, a progress notification —
is the same JSON-RPC 2.0 payload no matter how it physically travels between
client and server. stdio and Streamable HTTP are the two transports the spec
and official SDKs ship out of the box, but the protocol layer above them
doesn't actually care how bytes move. This lesson builds a third one.

## Why you'd need a custom transport

The built-in transports cover the overwhelming majority of real use cases —
local subprocess (stdio) and remote HTTP (Streamable HTTP). You'd reach for a
custom transport mainly when:

- You're embedding an MCP client in a **browser**, where raw TCP and
  subprocess spawning aren't available, but a `WebSocket` is.
- You need to carry MCP messages over an **existing messaging system** your
  infrastructure already uses (an internal message bus, for instance), and
  bridging through HTTP would be an unnecessary extra hop.
- You're prototyping **transport-level behavior** the spec doesn't define
  yet and want to experiment before proposing it upstream.

## The transport interface

Both SDKs define a transport as something that can send and receive
JSON-RPC messages asynchronously — in the Python SDK, concretely, a
transport is responsible for producing a pair of async read/write streams
that the protocol layer reads messages from and writes messages to. A
custom transport's job is just to implement that pairing over whatever
underlying channel you're using.

```python
import asyncio
import json
import websockets
from mcp.shared.message import SessionMessage
from mcp.types import JSONRPCMessage

async def websocket_client_streams(uri: str):
    """Open a WebSocket and expose it as the (read_stream, write_stream)
    pair the MCP ClientSession expects."""
    ws = await websockets.connect(uri)

    read_queue: asyncio.Queue = asyncio.Queue()
    write_queue: asyncio.Queue = asyncio.Queue()

    async def pump_incoming():
        async for raw in ws:
            message = JSONRPCMessage.model_validate_json(raw)
            await read_queue.put(SessionMessage(message))

    async def pump_outgoing():
        while True:
            session_message = await write_queue.get()
            raw = session_message.message.model_dump_json(exclude_none=True)
            await ws.send(raw)

    asyncio.create_task(pump_incoming())
    asyncio.create_task(pump_outgoing())
    return read_queue, write_queue
```

This is a sketch, not a drop-in SDK class — the exact stream types and
session wiring are worth checking against the SDK version you're using, since
the low-level transport interface is one of the more actively evolving
corners of the SDKs. The shape that matters conceptually: **one coroutine
pumping inbound frames into a queue the session reads from, one pumping
outbound messages the session writes onto the wire.**

## Server-side: the mirror image

A WebSocket server transport does the same job in reverse — accept a
connection, decode each incoming frame as a `JSONRPCMessage`, hand it to the
server's message-handling loop, and encode outgoing messages (responses,
notifications) back onto the socket:

```python
import websockets
from mcp.server.lowlevel import Server
from mcp.types import JSONRPCMessage

async def handle_connection(websocket, mcp_server: Server):
    async def read_stream():
        async for raw in websocket:
            yield JSONRPCMessage.model_validate_json(raw)

    async def write_message(message: JSONRPCMessage):
        await websocket.send(message.model_dump_json(exclude_none=True))

    await mcp_server.run(read_stream(), write_message, mcp_server.create_initialization_options())
```

Everything your server already registered — tools, resources, prompts — works
unchanged. Only the bytes-in, bytes-out mechanism is new.

## How It Actually Works

A transport implementation has exactly one contract to honor, regardless of
language or SDK version:

1. **Preserve message boundaries.** Each JSON-RPC message must arrive at the
   other end as a complete, independent unit — WebSocket frames and
   newline-delimited stdio both give you this for free; a raw TCP stream
   would not, and you'd need your own framing (length-prefixing, for
   example).
2. **Preserve ordering per direction**, but don't assume request/response
   pairs are strictly interleaved — notifications and requests for different
   in-flight calls can be mixed on the wire, and the `id` field is what
   lets the session layer match a response back to its request, not arrival
   order.
3. **Be bidirectional and duplex-capable.** A server can send the client
   requests too (an elicitation request or a `sampling/createMessage` call,
   for instance), so a transport that only supports client-to-server
   messages — some naive HTTP polling designs — isn't sufficient for a fully
   capable connection.
4. **Surface connection lifecycle events** (closed, errored) so the session
   layer above can clean up and the host can decide whether to reconnect.
5. **Everything above this layer — initialization, capability negotiation,
   tool calls — is written against the abstract read/write stream
   interface, not against stdio or HTTP specifically.** That's precisely
   why a correctly implemented custom transport is a drop-in swap: no other
   part of your server or client code changes.

## Exercise

Using the WebSocket sketches above as a starting point, get a minimal
round trip working: a WebSocket server transport wrapping a `FastMCP`
server with one trivial tool, and a WebSocket client transport that
connects, calls `initialize`, lists tools, and calls the one tool. You
don't need TLS or auth for this exercise — just prove the message pump in
both directions actually carries a real tool call end to end.
