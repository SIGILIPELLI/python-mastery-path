---
description: "In a distributed vector database, a delete you just issued might still return the 'deleted' document for a few seconds — that's eventual consistency, not a bug."
---

# 08 · Updates, Deletes & Consistency

## Updates are re-embed-and-upsert

Unlike a traditional database row, you can't "edit a vector" in place when
the underlying text changes — the embedding is a function of the text, so a
changed document needs a freshly computed embedding. The pattern is always:
re-embed the new text, then **upsert** (update-or-insert) by a stable ID.

```python
def update_document(collection, doc_id: str, new_text: str, metadata: dict | None = None):
    new_embedding = model.encode([new_text], normalize_embeddings=True)[0].tolist()
    collection.upsert(
        ids=[doc_id],
        embeddings=[new_embedding],
        documents=[new_text],
        metadatas=[metadata or {}],
    )
```

The critical design decision this depends on: **every document needs a
stable, deterministic ID** that doesn't change when its content does — a
database primary key, a content hash of a stable identifier (not of the
text itself, which changes), or a URL/path. If you don't have a stable ID
scheme, "updating" a document actually means deleting the old one with a
different embedding and never actually replacing it — a silent duplicate
bug that's easy to miss until your corpus mysteriously doubles in size.

## Soft delete vs. hard delete

- **Hard delete** removes the vector and all its metadata immediately and
  irreversibly — `collection.delete(ids=["doc_42"])`. Simple, but there's no
  undo, and in distributed systems it may take a moment to propagate (see
  consistency below).
- **Soft delete** marks a document as deleted via metadata instead of
  removing it, and filters it out at query time:

```python
def soft_delete(collection, doc_id: str):
    collection.update(ids=[doc_id], metadatas=[{"deleted": True}])

def search_excluding_deleted(collection, query, n_results=5):
    return collection.query(
        query_texts=[query],
        n_results=n_results,
        where={"deleted": {"$ne": True}},
    )
```

Soft delete is reversible (undelete is just flipping the flag back) and
preserves an audit trail, but it means every query needs the exclusion
filter, and the "deleted" vectors still consume index space and memory until
a background job actually purges them. Most production systems that need
compliance/audit trails use soft delete with a periodic hard-delete sweep
for anything soft-deleted past a retention window.

## Eventual consistency in distributed vector databases

Managed, horizontally-scaled vector databases (Pinecone, Weaviate Cloud,
distributed Qdrant clusters) typically replicate data across multiple nodes
for availability. A write (insert/update/delete) has to propagate to those
replicas, and — depending on the database's consistency model — a query
that lands on a replica that hasn't yet received the latest write can return
stale results for a short window after the write.

```python
# This sequence can genuinely return the deleted document in some systems
collection.delete(ids=["doc_42"])
results = collection.query(query_texts=["some query"], n_results=5)
# doc_42 might still appear here for a brief period — not a bug, it's propagation lag
```

This is called **eventual consistency**: the system guarantees that, given
enough time with no further writes, all replicas converge to the same
state — but it does not guarantee a read immediately after a write reflects
that write everywhere. If your application has a hard requirement that a
delete must be invisible to the very next read (e.g. "right to be forgotten"
compliance), check your specific vector DB's consistency guarantees and
available options — some offer a "strong consistency" read mode at a latency
cost, used selectively rather than by default.

## Re-indexing when the embedding model changes

Swapping embedding models (upgrading to a better one, or switching
providers) is **not** a metadata update — every existing vector was produced
by the old model's weights, and the new model's vector space is not
comparable to the old one at all. A cosine similarity between an
old-model-embedded query and a new-model-embedded document is meaningless.

```python
def reindex_with_new_model(old_collection, new_collection, new_model, batch_size=256):
    offset = 0
    while True:
        batch = old_collection.get(limit=batch_size, offset=offset, include=["documents", "metadatas"])
        if not batch["ids"]:
            break
        new_embeddings = new_model.encode(batch["documents"], normalize_embeddings=True).tolist()
        new_collection.upsert(
            ids=batch["ids"],
            embeddings=new_embeddings,
            documents=batch["documents"],
            metadatas=batch["metadatas"],
        )
        offset += batch_size
```

The safe rollout pattern: build the new collection fully in parallel (as
above), validate it (recall@k against your eval set, lesson 5) *before*
cutting traffic over, then switch your application's reads to the new
collection — and only delete the old one once you're confident, giving
yourself a rollback path if the new model underperforms in ways your eval
set didn't catch.

## Exercise

Implement `update_document`, `soft_delete`, and `search_excluding_deleted`
against your collection from earlier levels. Insert a document, soft-delete
it, confirm it's excluded from search results but still retrievable by ID
directly (`collection.get(ids=[...])`), then hard-delete it and confirm it's
gone entirely. Finally, write a small script that re-embeds your whole
collection into a new one with a different model and confirm the new
collection's recall@k on your eval set before you'd consider cutting over.
