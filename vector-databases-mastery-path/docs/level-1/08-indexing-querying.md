---
description: "Chroma's PersistentClient reopens the exact same collection, with every vector still indexed, just by pointing at the same path on disk — no separate save step required."
---

# 08 · Indexing & Querying Basics

With the fundamentals from Lesson 7 in place, this lesson goes one level
deeper into the Chroma operations you'll use in nearly every real project:
controlling result count, reading back similarity scores, updating and
deleting entries, and confirming your data really does persist.

## Controlling how many results come back

`n_results` (sometimes called `top_k` in other databases) controls how many
matches you get per query:

```python
results = collection.query(
    query_texts=["production incident"],
    n_results=5,     # default is 10 if you omit it
)
```

You can also query with multiple texts in one call — Chroma returns one
result set per query, batched:

```python
results = collection.query(
    query_texts=["production incident", "something about pets"],
    n_results=3,
)

for i, query_text in enumerate(["production incident", "something about pets"]):
    print(f"\nResults for: {query_text}")
    for doc, dist in zip(results["documents"][i], results["distances"][i]):
        print(f"  {dist:.4f}  {doc}")
```

## Reading distances and understanding the scale

Chroma's default distance metric is squared Euclidean (`l2`) unless you
configure the collection otherwise. **Lower distance = more similar** — the
opposite direction from cosine *similarity*, where higher means more
similar. Don't mix these up when sorting results manually.

You can set the distance metric explicitly at collection creation:

```python
collection = client.get_or_create_collection(
    name="my_collection",
    metadata={"hnsw:space": "cosine"},   # options: "l2", "cosine", "ip"
)
```

Chroma uses an HNSW index under the hood (the same algorithm you got an
intuition for in Lesson 6) — `hnsw:space` controls which distance function
that index is built around.

## Updating entries

```python
collection.update(
    ids=["doc1"],
    documents=["The cat sat on the windowsill, intently watching two birds."],
)
```

`update()` requires the `ids` to already exist. To insert-or-replace in one
call regardless of whether the id exists yet, use `upsert()` instead:

```python
collection.upsert(
    ids=["doc5"],
    documents=["A new document that may or may not already exist."],
)
```

## Deleting entries

```python
collection.delete(ids=["doc3"])

# Or delete everything matching a metadata filter (covered fully in Lesson 9):
collection.delete(where={"category": "spam"})
```

## Checking what's in a collection

```python
print(collection.count())          # how many items are stored

peek = collection.peek(limit=3)     # sample a few items without a real query
print(peek["ids"])
```

## Verifying persistence across restarts

Because `PersistentClient` writes to disk, you can close your Python process
entirely and reopen the same data later — this is the entire point of using
a persistent client instead of the in-memory one:

```python
# Run 1 — insert data, then exit the process entirely
import chromadb
client = chromadb.PersistentClient(path="./chroma_data")
collection = client.get_or_create_collection(name="persisted_demo")
collection.add(ids=["a"], documents=["This should still be here next time."])
print("inserted, count =", collection.count())
```

```python
# Run 2 — a completely fresh process, pointed at the same path
import chromadb
client = chromadb.PersistentClient(path="./chroma_data")
collection = client.get_or_create_collection(name="persisted_demo")
print("count after reopening:", collection.count())   # 1 — nothing lost
print(collection.get(ids=["a"]))
```

No explicit "save" call is needed — Chroma writes to the on-disk path as you
go. This matters because in any real application, your ingestion script and
your query-serving process (e.g. a web API) are usually separate Python
processes, sometimes on separate deploys — they only share data because
they point at the same persistent path.

## Exercise

Starting from the `my_notes` collection you built in Lesson 7's exercise:
update one document's text, upsert one brand-new document, delete one
document you no longer want, and confirm the final `collection.count()`
matches what you expect by hand. Then close your Python session completely,
reopen it, reconnect to the same `PersistentClient` path, and verify the
collection still contains exactly those changes.
