---
description: "The TypeScript SDK mirrors the Python SDK's decorator-driven shape with registerTool/registerResource calls on an McpServer instance connected to a transport."
---

# 01 · The TypeScript SDK

Everything you built in Level 1 used Python's `FastMCP`. Most of the MCP
ecosystem — editor extensions, Node-based backends, anything that's already a
TypeScript codebase — uses the official TypeScript SDK instead. The concepts
are identical: tools, resources, prompts, a transport connecting a server to
a client. Only the syntax changes.

## Install

```bash
mkdir mcp-ts-demo && cd mcp-ts-demo
npm init -y
npm install @modelcontextprotocol/sdk zod
npm install -D typescript @types/node tsx
npx tsc --init --target es2022 --module nodenext --moduleResolution nodenext
```

`zod` is a schema library the SDK uses to describe tool input shapes — it
plays the same role Python's type hints played with `FastMCP`.

## A minimal server

```typescript
// server.ts
import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import { z } from "zod";

const server = new McpServer({
  name: "ts-demo",
  version: "1.0.0",
});

server.registerTool(
  "add",
  {
    title: "Add two numbers",
    description: "Returns the sum of a and b.",
    inputSchema: { a: z.number(), b: z.number() },
  },
  async ({ a, b }) => ({
    content: [{ type: "text", text: String(a + b) }],
  })
);

const transport = new StdioServerTransport();
await server.connect(transport);
```

Run it with the Inspector, same as in Level 1:

```bash
npx @modelcontextprotocol/inspector npx tsx server.ts
```

Compare this to Python's `FastMCP`:

```python
@mcp.tool()
def add(a: int, b: int) -> int:
    """Returns the sum of a and b."""
    return a + b
```

Python's version infers the schema from type hints and the return value is
just a Python value. TypeScript's version is more explicit — you pass the
schema and build the `content` array yourself — but the protocol-level
behavior (what goes over stdio, what `tools/list` returns, how `tools/call`
is dispatched) is byte-for-byte the same. A client talking to either server
can't tell which language it's written in.

## A small two-tool server

Let's rebuild the spirit of Level 1's notes server, scaled down to two
tools, to see a server with real state:

```typescript
// notes-server.ts
import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import { z } from "zod";

interface Note {
  id: number;
  text: string;
}

const notes: Note[] = [];
let nextId = 1;

const server = new McpServer({ name: "notes-ts", version: "1.0.0" });

server.registerTool(
  "add_note",
  {
    title: "Add a note",
    description: "Stores a new note and returns its id.",
    inputSchema: { text: z.string() },
  },
  async ({ text }) => {
    const note = { id: nextId++, text };
    notes.push(note);
    return { content: [{ type: "text", text: `Added note #${note.id}` }] };
  }
);

server.registerTool(
  "list_notes",
  {
    title: "List notes",
    description: "Returns every stored note.",
    inputSchema: {},
  },
  async () => ({
    content: [
      {
        type: "text",
        text: notes.map((n) => `#${n.id}: ${n.text}`).join("\n") || "(no notes yet)",
      },
    ],
  })
);

const transport = new StdioServerTransport();
await server.connect(transport);
```

The `notes` array lives in the server process's memory for as long as the
process runs — the same lifetime model as the Python version from Level 1.

## When a team picks TypeScript over Python

- **The rest of the codebase is already Node/TypeScript.** A server that
  shares types, utilities, or an existing API client with a Next.js or
  Express app is simpler to keep in the same language.
- **The server needs to run in environments where Node is the standard
  runtime** — serverless functions on platforms built around JavaScript,
  edge runtimes, browser-adjacent tooling.
- **Python wins** when the server's real job is calling into a Python-only
  ecosystem — data science libraries, ML model code, anything built on
  pandas/NumPy/PyTorch. Wrapping that from TypeScript would mean shelling
  out to a Python subprocess anyway, which defeats the point.

Neither SDK is "more official" — both are maintained by Anthropic as
first-class implementations of the same spec. Pick based on what the rest of
your system already looks like.

## Exercise

Add a third tool, `complete_note`, that takes a note `id` (number) and
removes it from the `notes` array, returning a confirmation message — or an
error message if no note with that id exists. Test it with the Inspector:
add two notes, complete one, then list notes and confirm only the other one
remains.
