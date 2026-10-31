---
description: "You can't swap a vector DB or a model in one step — a dual-write period and a shadow-read comparison are what keep a migration from silently breaking search."
---

# 05 · Vector DB Migration Strategies

Two kinds of migration come up constantly in production vector search: moving
from one vector database to another (vendor change, cost, feature need), and
re-embedding an entire corpus because you've switched embedding models
(better quality, bigger context, cheaper inference). Both share the same
risk: you can't just "cut over" — embeddings from different models aren't
compatible with each other, and a new backend might behave subtly
differently under real query load. This lesson covers the pattern that
makes both migrations safe.

## Why you can't just switch

Two models embedding the same sentence produce vectors that are **not
comparable** — different dimensionality, different training objective,
different geometry. If you switch your embedding model but only re-embed
*new* documents going forward, your vector DB now has a corpus of mixed,
incompatible vectors, and queries against the old half will silently return
garbage (or nothing) once your query encoder is the new model. The old
vectors have to be fully re-embedded, not incrementally migrated.

Similarly, switching vector DB backends means re-inserting every vector
into the new system — there's no live migration path most of the time, and
even where bulk-export/import tools exist, you want to validate behavior
before committing.

## The dual-write pattern

During migration, write every new or updated document to **both** the old
and new system simultaneously:

```python
def upsert_document(doc_id: str, text: str, metadata: dict):
    embedding_old = old_model.encode(text)
    old_collection.upsert(ids=[doc_id], embeddings=[embedding_old.tolist()], metadatas=[metadata])

    embedding_new = new_model.encode(text)
    new_collection.upsert(ids=[doc_id], embeddings=[embedding_new.tolist()], metadatas=[metadata])
```

This keeps both systems current while you backfill historical data in the
background, so you never have a point where the new system is missing
recent writes.

## Backfill

Separately, run a batch job that re-embeds and inserts every existing
document into the new system:

```python
def backfill(source_db, target_collection, new_model, batch_size: int = 100):
    offset = 0
    while True:
        batch = source_db.fetch_documents(offset=offset, limit=batch_size)
        if not batch:
            break

        embeddings = new_model.encode([doc["text"] for doc in batch])
        target_collection.upsert(
            ids=[doc["id"] for doc in batch],
            embeddings=embeddings.tolist(),
            metadatas=[doc["metadata"] for doc in batch],
        )
        offset += batch_size
        print(f"Backfilled {offset} documents")
```

Run this as a resumable, rate-limited job — for millions of documents this
can take hours, and embedding API costs or self-hosted GPU time are real
budget items to account for before starting.

## Shadow reads

Once the new system has caught up (dual-write is current, backfill is
complete), start **shadow-reading**: send every real query to both systems,
serve the response from the old (trusted) system, but log both systems'
results for comparison — without the new system affecting what users see
yet.

```python
def search_with_shadow(query: str, user_id: str):
    old_results = old_collection.query(query_embeddings=[old_model.encode(query).tolist()], n_results=10)
    new_results = new_collection.query(query_embeddings=[new_model.encode(query).tolist()], n_results=10)

    log_shadow_comparison(query, old_results, new_results)
    return old_results  # still serving from the trusted system
```

Compare the two result sets using the metrics from lesson 2 (treat the old
system's results as a rough proxy for "ground truth," or better, run a
proper eval set through both). Look specifically for queries where overlap
is low — those are the cases to manually inspect before trusting the new
system with real traffic.

## Cutover and rollback

Once shadow-read comparison looks good across a representative sample of
real traffic (not just your eval set — eval sets miss edge cases that
production traffic surfaces), cut over gradually:

1. **Canary a small percentage** of real query traffic to serve from the
   new system (e.g. 1-5%), keeping dual-write running so both stay current.
2. **Monitor** retrieval-quality signals (click-through on results if you
   have it, or downstream RAG answer quality) for the canary slice
   specifically, not just aggregate latency/error metrics.
3. **Ramp up** the percentage over days, not minutes, watching at each step.
4. **Full cutover**: once at 100%, keep the old system running read-only for
   a defined rollback window (e.g. two weeks) before decommissioning it.
5. **Rollback plan**: if quality regresses post-cutover, flip the serving
   percentage back to the old system immediately — this is why dual-write
   keeps running through the whole canary period, so the old system is
   never stale and rollback is instant rather than requiring a fresh
   backfill under pressure.

## Cutover checklist

- [ ] Dual-write live and verified current on both systems
- [ ] Backfill complete, counts reconciled (same document count in both)
- [ ] Shadow-read comparison run against a sample of real production
      queries, not just the eval set
- [ ] Eval metrics (Recall@K, MRR, NDCG) measured on both systems against
      the same labeled eval set, new system meets or beats old
- [ ] Canary rollout plan with explicit rollback trigger thresholds
- [ ] Old system kept read-available through a defined rollback window
      after full cutover

## Exercise

Design (in writing, you don't need to run it against real infrastructure)
a migration plan for moving your semantic search CLI or RAG retrieval
service from Chroma to a different backend from Level 2 (Qdrant or
pgvector). Write out the dual-write code for your `upsert` path, and define
three concrete numeric thresholds you'd use to decide whether a canary
rollout is safe to continue ramping up, or should roll back.
