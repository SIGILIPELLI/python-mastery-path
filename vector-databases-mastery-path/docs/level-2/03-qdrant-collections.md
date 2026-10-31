---
description: "Qdrant separates a point's vector from its payload, so you can filter on payload fields before or during the vector search instead of after it."
---

# 03 · Qdrant: Collections & Payloads

Qdrant is an open-source vector database you can run yourself (Docker, a binary,
or Kubernetes) or use as a managed cloud service. Its core unit is a "point":
an ID, a vector, and a payload (arbitrary JSON metadata).

## Setup

```bash
docker run -d -p 6333:6333 -p 6334:6334 qdrant/qdrant
pip install qdrant-client
```

```python
from qdrant_client import QdrantClient

client = QdrantClient(url="http://localhost:6333")
```

For Qdrant Cloud instead of local Docker, swap in `QdrantClient(url=..., api_key=...)`.

## Creating a collection

```python
from qdrant_client.models import Distance, VectorParams

client.create_collection(
    collection_name="articles",
    vectors_config=VectorParams(size=384, distance=Distance.COSINE),
)
```

`Distance` also supports `EUCLID` and `DOT` — pick based on how your embedding
model was trained (most sentence-transformer models are designed for cosine).

## Upserting points

```python
from qdrant_client.models import PointStruct
from sentence_transformers import SentenceTransformer

model = SentenceTransformer("all-MiniLM-L6-v2")

docs = [
    {"id": 1, "text": "Qdrant payloads hold arbitrary metadata.", "category": "basics"},
    {"id": 2, "text": "HNSW powers Qdrant's default index.", "category": "internals"},
]

points = [
    PointStruct(
        id=doc["id"],
        vector=model.encode(doc["text"]).tolist(),
        payload={"text": doc["text"], "category": doc["category"]},
    )
    for doc in docs
]

client.upsert(collection_name="articles", points=points)
```

A payload is just a dict — any JSON-serializable metadata goes here: timestamps,
tags, nested objects, arrays.

## Payload-filtered queries

```python
from qdrant_client.models import Filter, FieldCondition, MatchValue

query_vector = model.encode("how does metadata storage work").tolist()

results = client.query_points(
    collection_name="articles",
    query=query_vector,
    query_filter=Filter(
        must=[FieldCondition(key="category", match=MatchValue(value="basics"))]
    ),
    limit=5,
)

for point in results.points:
    print(point.score, point.payload["text"])
```

The filter narrows the search to points matching `category == "basics"` *before*
ranking by vector similarity — Qdrant pushes the filter down into the HNSW graph
traversal itself (skipping non-matching nodes during the graph walk) rather than
filtering a result set after the fact, which keeps recall high even with
selective filters on large collections. This is a meaningfully different
implementation strategy from databases that filter post-search, and it's part of
why Qdrant markets itself heavily on filtered-search performance.

## Exercise

Create a Qdrant collection, upsert the 10 Level 1 documents with a `category`
payload field you invent for each, and write a query that combines vector
similarity with a `Filter` requiring a specific category. Then run the identical
vector query with no filter and compare how the ranking changes — specifically
note any document that would have ranked in the unfiltered top-3 but is correctly
excluded by the filter.
