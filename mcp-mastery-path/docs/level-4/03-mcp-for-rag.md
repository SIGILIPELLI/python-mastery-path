---
description: "Putting a vector database behind an MCP server trades a few milliseconds of indirection for a retrieval tool any MCP host can discover and reuse, not just the one app you wrote it for."
---

# 03 · MCP for RAG: Servers as a Retrieval Layer

Retrieval-augmented generation systems need a way to turn a query into
relevant chunks of content, usually by searching a vector database. Nothing
about that requires MCP — you can call your vector database's client library
directly from inside your application. This lesson is about when putting an
MCP server in front of that retrieval step is worth the extra layer, and
when it isn't.

## The pattern

Instead of your application importing a vector-database client and querying
it in-process, you stand up an MCP server whose tool or resource does that
querying on the application's behalf:

```python
from mcp.server.fastmcp import FastMCP
import chromadb

mcp = FastMCP("knowledge-base")
client = chromadb.PersistentClient(path="./chroma_data")
collection = client.get_or_create_collection("docs")

@mcp.tool()
def search_knowledge_base(query: str, top_k: int = 5) -> list[dict]:
    """Search the knowledge base for chunks relevant to a query.

    Returns a list of {text, source, score} for the top_k most similar
    chunks.
    """
    results = collection.query(query_texts=[query], n_results=top_k)
    return [
        {"text": doc, "source": meta.get("source"), "score": dist}
        for doc, meta, dist in zip(
            results["documents"][0],
            results["metadatas"][0],
            results["distances"][0],
        )
    ]

if __name__ == "__main__":
    mcp.run()
```

If you've worked through the Vector Databases Mastery Path series on this
same site, everything inside that tool body — the embedding, the similarity
search, the index choice — is exactly what that course covers in depth. This
lesson is only about the layer *around* that: should it live behind an MCP
server at all?

## The tradeoff, honestly

**What you gain:**

- **Reusability across hosts.** Any MCP-compatible application — your
  internal chat tool today, a different IDE assistant tomorrow, a teammate's
  side project next month — gets the same retrieval tool for free, with no
  re-integration.
- **Discoverability.** `tools/list` tells a host (and the model) exactly
  what this tool does and what arguments it takes, without anyone reading
  your application's source code.
- **A clean security boundary.** The server process is the only thing that
  needs direct credentials/network access to the vector database; client
  applications never touch it directly.

**What it costs:**

- **An extra network hop and serialization step**, even for a local stdio
  server — meaningful if you're doing many small retrieval calls in a tight
  loop and latency is the dominant constraint.
- **Another process to deploy, monitor, and keep in sync** with your vector
  database's schema and embedding model version.
- **Indirection that can genuinely not be worth it** for a single
  application that will only ever call its own retrieval logic — if nothing
  else will ever need this tool, in-process is simpler and faster, full
  stop.

## When it's worth it

Reach for an MCP retrieval server when the knowledge base is a shared asset
multiple tools or applications should be able to query, when you want the
retrieval step to be independently deployable and scalable from the
application calling it, or when you specifically want a model to be able to
*decide* when to search (as an available tool) rather than always retrieving
on every turn — the tool-call framing gives the model that choice instead of
hard-coding "always retrieve first."

## Exercise

Take a retrieval function you'd otherwise call directly in an application
(or write a small one against any local dataset) and wrap it as an MCP tool
the way the example above does. Then write two or three sentences arguing
honestly for your *specific* use case: is the MCP-server layer actually
worth it here, or would direct in-process integration genuinely be the
better call? There's no "right" answer expected — the point is practicing
making that tradeoff call deliberately instead of reaching for MCP by
default.
