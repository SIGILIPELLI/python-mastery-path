---
description: "Chroma's where filter narrows candidates by metadata BEFORE vector similarity ranks them, so a query can be both semantically relevant and exactly scoped — e.g. 'this meaning, but only from 2024, only in the billing category.'"
---

# 09 · Metadata Filtering

Pure vector similarity answers "what's semantically closest?" but real
applications usually need to combine that with hard constraints: only
search *this* user's documents, only *this* category, only documents newer
than a given date. That's what metadata filtering is for.

## Attaching metadata on insert

```python
import chromadb

client = chromadb.PersistentClient(path="./chroma_data")
collection = client.get_or_create_collection(name="support_tickets")

collection.add(
    ids=["t1", "t2", "t3", "t4"],
    documents=[
        "Customer can't log in after password reset.",
        "Invoice total looks wrong for last month's subscription.",
        "App crashes when uploading a profile photo.",
        "Refund requested for duplicate charge on credit card.",
    ],
    metadatas=[
        {"category": "auth", "year": 2024, "priority": "high"},
        {"category": "billing", "year": 2024, "priority": "medium"},
        {"category": "bug", "year": 2023, "priority": "high"},
        {"category": "billing", "year": 2024, "priority": "high"},
    ],
)
```

Each item in `metadatas` must line up positionally with the matching id in
`ids` — Chroma stores them together.

## Filtering with `where`

```python
results = collection.query(
    query_texts=["money was charged twice"],
    n_results=5,
    where={"category": "billing"},
)

for doc, meta, dist in zip(
    results["documents"][0], results["metadatas"][0], results["distances"][0]
):
    print(f"{dist:.4f}  {meta}  {doc}")
```

This only ranks and returns documents where `category == "billing"` —
vector similarity still determines the *order* within that filtered set, but
anything outside the filter is excluded entirely before ranking happens.

## Combining multiple conditions

```python
# Billing issues from 2024 only
results = collection.query(
    query_texts=["money was charged twice"],
    n_results=5,
    where={
        "$and": [
            {"category": "billing"},
            {"year": 2024},
        ]
    },
)
```

Chroma supports comparison operators too:

```python
# High priority items only
where={"priority": {"$eq": "high"}}

# Anything from 2024 or later
where={"year": {"$gte": 2024}}

# Either billing OR auth category
where={"$or": [{"category": "billing"}, {"category": "auth"}]}
```

## Filtering on document text itself

Separate from metadata filtering, `where_document` filters on substring
matches in the raw document text, and can be combined with `where`:

```python
results = collection.query(
    query_texts=["login problem"],
    n_results=5,
    where={"year": 2024},
    where_document={"$contains": "password"},
)
```

## Deleting by metadata filter

Filters aren't just for queries — they also work with `.delete()`, useful
for bulk cleanup:

```python
# Remove every low-priority item from 2023
collection.delete(where={"$and": [{"priority": "low"}, {"year": 2023}]})
```

## Why this matters for real systems

Almost every production use of vector search needs this. A few concrete
examples:

- **Multi-tenant SaaS**: `where={"customer_id": current_customer.id}` so one
  customer's semantic search never surfaces another customer's documents.
- **RAG over a knowledge base with access control**: `where={"visibility":
  "public"}` or `where={"team": current_user.team}`.
- **Time-scoped search**: "find similar support tickets, but only from the
  last 90 days" — combine a date filter with the similarity query.

Without metadata filtering, you'd have to run the vector query first,
over-fetch a huge number of results, then filter in application code —
wasteful and error-prone. Filtering during the query itself is both faster
and correct by construction.

## Exercise

Extend the `support_tickets` collection with 6 more tickets covering at
least 3 categories, 2 different years, and a mix of priorities. Write three
queries:

1. A semantic query combined with a single metadata filter.
2. A semantic query combined with an `$and` of two metadata conditions.
3. A semantic query combined with an `$or` across two categories.

For each, print the results and manually verify every returned item
actually satisfies the filter you specified.
