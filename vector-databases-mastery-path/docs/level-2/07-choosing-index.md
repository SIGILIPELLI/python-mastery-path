---
description: "The right index choice is really a question about your recall floor and your RAM budget — pick the point on that curve first, then pick the database."
---

# 07 · Choosing the Right Index

You now know four production databases and the two dominant index families
behind them. This lesson is the decision framework for picking between them on
a real project.

## The index decision tree

```
Dataset fits comfortably in RAM as a full HNSW graph?
  ├─ Yes → use HNSW (best recall/latency for the memory you're already paying for)
  └─ No, RAM-constrained or huge scale (100M+ vectors)
        → use IVF+PQ (trade some recall for ~16-32x memory reduction)

Write-heavy workload (constant inserts/updates, low tolerance for rebuild lag)?
  → lean toward IVF (cheaper incremental inserts into existing clusters)
     or a managed service that hides rebalancing from you (Pinecone)

Need exact results, not approximate (small dataset, correctness-critical)?
  → brute-force / flat index is fine under ~100K-1M vectors on modern hardware
```

Recall requirement matters more than most people assume up front: a recommendation
system tolerating occasional "good enough" neighbors can run `ef_search`/`nprobe`
low and go faster; a legal or medical retrieval system that needs the *actual*
nearest match for every query should bias toward higher `ef`/`nprobe` or
brute-force, accepting the latency cost.

## Comparing the four databases from this level

| | Pinecone | Weaviate | Qdrant | pgvector |
|---|---|---|---|---|
| **Hosting** | Managed only (serverless) | Managed or self-hosted | Managed or self-hosted | Self-hosted (any Postgres) or managed Postgres |
| **Default index** | Proprietary (HNSW-like, hidden) | HNSW | HNSW | HNSW or IVFFlat (your choice) |
| **Native hybrid search** | Sparse-dense hybrid support | Yes, `alpha`-tunable | Yes (via sparse vectors) | No (would need separate full-text search + join) |
| **Payload/metadata filtering** | Yes | Yes | Yes, with graph-level filter push-down | Yes, via ordinary SQL `WHERE` |
| **Pricing model** | Per read/write unit + storage | Self-host: infra cost; managed: usage-based | Self-host: infra cost; managed: usage-based | Whatever you already pay for Postgres |
| **Best fit** | Teams that want zero ops | Teams wanting schema + hybrid search built in | Teams wanting self-hosted control + strong filtering | Teams whose data is already relational and don't want a second database |

## A practical heuristic

For most new projects, start with the simplest option that meets your recall and
latency needs, and only move to something more specialized when you hit a real
limit:

1. **Under ~1M vectors, already using Postgres** → pgvector. No new
   infrastructure, transactional consistency with your other data.
2. **Need managed, zero-ops, scaling to tens of millions** → Pinecone.
3. **Need self-hosted control, heavy payload filtering, or on-prem requirements** →
   Qdrant.
4. **Need schema validation and native hybrid search out of the box** → Weaviate.
5. **Hundreds of millions+ vectors, RAM-constrained** → look beyond this level's
   four options toward IVF+PQ-first systems (Milvus, FAISS-backed custom
   services) — the previous lesson's tradeoff becomes unavoidable at this scale.

None of these choices are permanent or mutually exclusive — many real systems use
pgvector for a transactional "source of truth" table and periodically sync a
subset into a dedicated vector database for high-QPS semantic search, getting
both consistency and scale.

## Exercise

Take three hypothetical projects — (a) a startup's in-app search over 50,000
product listings already stored in Postgres, (b) a company needing exact-match
legal document retrieval over 2 million contracts with strict accuracy
requirements, (c) a consumer app expecting 500 million user-generated posts
within two years — and write one paragraph each justifying a specific database +
index choice from this lesson's framework, citing the actual constraint (scale,
recall, ops burden, existing infra) that drove your answer.
