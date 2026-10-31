---
description: "Pinecone's serverless indexes auto-scale storage and compute independently, so you pay for what you store and what you query, not a fixed cluster size."
---

# 01 · Pinecone Fundamentals

Pinecone is a fully managed vector database: you never choose an index algorithm,
size a cluster, or tune `ef_search`. You create an index, upsert vectors, and query.
That simplicity is the entire value proposition — and the entire lesson.

## Getting an API key

Sign up at [pinecone.io](https://www.pinecone.io/) and grab an API key from the
console. Store it as an environment variable rather than hardcoding it:

```bash
export PINECONE_API_KEY="your-key-here"
pip install pinecone
```

## Creating a serverless index

```python
import os
from pinecone import Pinecone, ServerlessSpec

pc = Pinecone(api_key=os.environ["PINECONE_API_KEY"])

pc.create_index(
    name="docs-index",
    dimension=384,  # must match your embedding model's output size
    metric="cosine",
    spec=ServerlessSpec(cloud="aws", region="us-east-1"),
)

index = pc.Index("docs-index")
```

`dimension` and `metric` are fixed at creation time — you can't change them later
without recreating the index. 384 matches `all-MiniLM-L6-v2` from Level 1; if you
switch embedding models, you need a new index.

## Upserting vectors with metadata

```python
from sentence_transformers import SentenceTransformer

model = SentenceTransformer("all-MiniLM-L6-v2")

docs = [
    {"id": "doc-1", "text": "Pinecone is a managed vector database.", "category": "intro"},
    {"id": "doc-2", "text": "HNSW graphs enable fast approximate search.", "category": "internals"},
]

vectors = []
for doc in docs:
    embedding = model.encode(doc["text"]).tolist()
    vectors.append({
        "id": doc["id"],
        "values": embedding,
        "metadata": {"text": doc["text"], "category": doc["category"]},
    })

index.upsert(vectors=vectors)
```

"Upsert" means insert-or-update: if `doc-1` already exists, this overwrites it.
There's no separate "insert" call — every write is idempotent by ID.

## Querying

```python
query_text = "How does managed infrastructure help with vector search?"
query_vector = model.encode(query_text).tolist()

results = index.query(
    vector=query_vector,
    top_k=3,
    include_metadata=True,
)

for match in results["matches"]:
    print(match["score"], match["metadata"]["text"])
```

`score` for a cosine-metric index is a similarity in `[-1, 1]` (higher is better) —
note this is the opposite direction from a distance, which is worth checking per
provider since not all vector DBs report scores the same way.

## Why managed infrastructure matters

Running your own HNSW cluster means capacity planning: how much RAM for the graph,
how many replicas for availability, how to reshard when you outgrow one machine.
Pinecone's serverless tier handles all of that behind the API — storage and query
throughput scale independently, and you're billed per read/write unit and per GB
stored rather than per provisioned node. The tradeoff is less control: you can't
inspect or tune the underlying index structure the way you can with a self-hosted
database (that's Levels 2.5-2.6, coming next with HNSW and IVF+PQ internals).

## Exercise

Create a Pinecone index with `dimension=384` and `metric="cosine"`, upsert the 10
file summaries from your Level 1 semantic search CLI project (reuse the embeddings
you already computed with sentence-transformers), and query it with three different
natural-language questions. Compare the `top_k=3` results against what your Level 1
Chroma-based CLI returned for the same queries — they should mostly agree, since
both are approximating the same cosine-similarity ranking.
