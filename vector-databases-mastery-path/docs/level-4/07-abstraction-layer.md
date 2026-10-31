---
description: "An abstract VectorStore interface means a vendor migration (lesson 5) touches one adapter class instead of every call site in your application."
---

# 07 · Building a Vector DB Abstraction Layer

Every lesson in this course has used a specific backend's native API
directly — `collection.add()` for Chroma, `client.upsert()` for Qdrant,
`index.upsert()` for Pinecone. That's fine for learning each one, but a real
application coupled directly to a specific vendor's API pays for it the
moment you need to migrate (lesson 5), support a second backend, or test
against an in-memory fake instead of a real database in CI. This lesson
builds a thin abstraction layer that fixes that.

## Designing the interface

Define the operations your *application* actually needs, independent of
any backend's specific method names or parameter shapes:

```python
from abc import ABC, abstractmethod
from dataclasses import dataclass

@dataclass
class SearchResult:
    id: str
    score: float
    metadata: dict

class VectorStore(ABC):
    @abstractmethod
    def upsert(self, ids: list[str], embeddings: list[list[float]], metadatas: list[dict]) -> None:
        ...

    @abstractmethod
    def search(self, query_embedding: list[float], top_k: int, filters: dict | None = None) -> list[SearchResult]:
        ...

    @abstractmethod
    def delete(self, ids: list[str]) -> None:
        ...
```

Keep this interface as small as your application genuinely needs — resist
adding every method a specific backend happens to support. The point of an
abstraction is that it's the *intersection* of what you need, not the union
of everything every backend can do; the moment you add a method only one
backend can implement, you've lost the portability you built this for.

## The Chroma adapter

```python
import chromadb

class ChromaVectorStore(VectorStore):
    def __init__(self, path: str, collection_name: str):
        client = chromadb.PersistentClient(path=path)
        self._collection = client.get_or_create_collection(collection_name)

    def upsert(self, ids, embeddings, metadatas):
        self._collection.upsert(ids=ids, embeddings=embeddings, metadatas=metadatas)

    def search(self, query_embedding, top_k, filters=None):
        results = self._collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k,
            where=filters,
        )
        return [
            SearchResult(id=i, score=1 - d, metadata=m)  # Chroma returns distance; flip to a similarity-style score
            for i, d, m in zip(results["ids"][0], results["distances"][0], results["metadatas"][0])
        ]

    def delete(self, ids):
        self._collection.delete(ids=ids)
```

## The Qdrant adapter

```python
from qdrant_client import QdrantClient
from qdrant_client.models import PointStruct, Filter, FieldCondition, MatchValue

class QdrantVectorStore(VectorStore):
    def __init__(self, url: str, collection_name: str):
        self._client = QdrantClient(url=url)
        self._collection = collection_name

    def upsert(self, ids, embeddings, metadatas):
        points = [
            PointStruct(id=i, vector=e, payload=m)
            for i, e, m in zip(ids, embeddings, metadatas)
        ]
        self._client.upsert(collection_name=self._collection, points=points)

    def search(self, query_embedding, top_k, filters=None):
        qdrant_filter = None
        if filters:
            qdrant_filter = Filter(must=[
                FieldCondition(key=k, match=MatchValue(value=v)) for k, v in filters.items()
            ])
        hits = self._client.search(
            collection_name=self._collection,
            query_vector=query_embedding,
            limit=top_k,
            query_filter=qdrant_filter,
        )
        return [SearchResult(id=str(h.id), score=h.score, metadata=h.payload) for h in hits]

    def delete(self, ids):
        self._client.delete(collection_name=self._collection, points_selector=ids)
```

Notice the two adapters already had to paper over real differences: Chroma
returns a *distance* (lower is better) while Qdrant's default returns a
*similarity score* (higher is better) — the `score=1 - d` line in the
Chroma adapter normalizes this so application code can always assume
"higher score is better," regardless of backend. Filter syntax is
completely different between the two (`where={"key": "value"}` dict vs. a
`Filter`/`FieldCondition` object graph) — the adapter's job is exactly to
absorb differences like these so nothing above the interface has to know
about them.

## Using the abstraction

```python
def build_rag_context(store: VectorStore, query_embedding: list[float], tenant_id: str) -> str:
    results = store.search(query_embedding, top_k=5, filters={"owner_id": tenant_id})
    return "\n\n".join(r.metadata["text"] for r in results)

# Swap backends by changing one line — nothing else in the application changes
store = ChromaVectorStore(path="./db", collection_name="docs")
# store = QdrantVectorStore(url="http://localhost:6333", collection_name="docs")

context = build_rag_context(store, query_embedding, tenant_id="acme-corp")
```

This is also what makes migrations (lesson 5) tractable: the dual-write
pattern becomes "call `upsert` on two `VectorStore` instances" instead of
rewriting every insert call site in the codebase to know about two
different vendor SDKs.

## What this does and doesn't buy you

It buys you: portability for standard CRUD + filtered search, easy testing
(a trivial in-memory `VectorStore` implementation for unit tests, with no
real database needed), and a clean seam for the migration patterns in
lesson 5.

It does **not** buy you: automatic access to backend-specific features
behind the common interface (HNSW parameter tuning, Qdrant's advanced
payload indexing, Pinecone's sparse-dense hybrid queries) — those need
either backend-specific escape hatches on top of the abstraction, or
acceptance that you're using the lowest common denominator of what your
chosen backends support. Most teams add a narrow, explicitly-named
escape-hatch method (e.g. `store.raw_client()`) for the rare call site that
genuinely needs backend-specific behavior, rather than bloating the shared
interface to cover every vendor's special case.

## Exercise

Write a third adapter, `InMemoryVectorStore`, that implements the same
`VectorStore` interface using nothing but a Python list and NumPy for
brute-force cosine similarity (Level 1, lesson 4) — no external database at
all. Write one test function that runs the same three operations (`upsert`,
`search`, `delete`) against all three adapters (Chroma, Qdrant if you have
it running, and your in-memory one) and asserts they return consistent
results, proving the abstraction actually holds across implementations.
