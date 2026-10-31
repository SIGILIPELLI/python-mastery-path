---
description: "A namespace query only ever searches that namespace's vectors, so 1,000 tenants sharing one Pinecone index cost the same per-query as one tenant alone."
---

# 09 · Namespaces, Sharding & Multi-Tenancy

Building a product used by many customers (a SaaS app, not a single internal
tool) raises a question none of the previous lessons addressed: how do you keep
Customer A's vectors from ever appearing in Customer B's search results — and
do it without provisioning a separate database per customer?

## Namespaces: logical isolation within one index

Pinecone's answer is namespaces — a partition key built into the upsert and
query calls:

```python
# Each tenant's vectors live in their own namespace
index.upsert(vectors=tenant_a_vectors, namespace="tenant-a")
index.upsert(vectors=tenant_b_vectors, namespace="tenant-b")

# A query against one namespace never sees another namespace's vectors
results = index.query(vector=query_vector, top_k=5, namespace="tenant-a")
```

Crucially, a query scoped to `namespace="tenant-a"` has the same latency whether
there are 10 namespaces or 10,000 sharing the index — the namespace boundary is
enforced at the index level, not implemented as a metadata filter applied after
search. This matters for predictable multi-tenant performance.

Qdrant and Weaviate don't have a dedicated "namespace" primitive with that exact
name, but achieve the same isolation two ways:

- **Metadata/payload filtering**: tag every point with `tenant_id` and always
  filter by it (Qdrant's filtered search pushes this into the HNSW traversal
  itself — see lesson 3 — so it stays reasonably fast, but it's not a hard
  architectural boundary the way a namespace is).
- **One collection per tenant**: Qdrant and Weaviate collections are cheap enough
  to create many of, so some teams give each tenant (or tenant tier) its own
  collection instead — this is architecturally closer to Pinecone namespaces.

## Sharding for scale

Sharding splits a dataset across multiple machines when it's too large (or too
high-throughput) for one node. Two common strategies:

1. **Hash-based sharding**: route each vector to a shard based on a hash of its
   ID. Simple, spreads load evenly, but a query normally has to fan out to
   *every* shard (since any shard could hold the nearest neighbor) and merge
   results — more network overhead per query.
2. **Tenant-based sharding**: route all of one tenant's vectors to the same
   shard (e.g. `shard = hash(tenant_id) % num_shards`). Queries for a given
   tenant only hit one shard — much cheaper per query — but shard sizes can grow
   unevenly if tenants vary wildly in size (a "hot shard" problem), and a single
   huge tenant can still outgrow one shard.

Managed services (Pinecone, Weaviate Cloud, Qdrant Cloud) handle sharding
internally and mostly invisibly; self-hosting at real scale means choosing and
operating one of these strategies yourself.

## One-index-per-tenant vs. shared-index-with-filter

| | One index per tenant | Shared index + namespace/filter |
|---|---|---|
| **Isolation** | Strongest (physically separate) | Strong (logically separate) |
| **Cost at scale with many small tenants** | High (per-index overhead × tenant count) | Low (overhead amortized) |
| **Noisy-neighbor risk** | None (fully isolated) | Low with true namespaces, higher with filter-only isolation |
| **Operational complexity** | High (manage N indexes) | Low (manage 1 index) |
| **Good fit** | Few large tenants, strict isolation requirements (e.g. regulated data) | Many small-to-medium tenants, cost-sensitive |

A common pattern: shared index with namespaces for most tenants, with an escape
hatch to a dedicated index for a handful of enterprise customers who require
stronger isolation guarantees or have outgrown what a shared index can serve
efficiently.

## Exercise

Using Pinecone (or Qdrant with a `tenant_id` payload filter, if you don't have a
Pinecone account), simulate 3 tenants by upserting the same 10 Level 1 documents
three times into three different namespaces (or with three different
`tenant_id` values), each with slightly different metadata per "tenant." Query
one namespace/tenant and confirm you never see another tenant's documents in the
results — then intentionally query *without* the namespace/filter and observe
all three tenants' documents mixed together, to see concretely what isolation
is actually preventing.
