---
description: "A rarely-queried vector doesn't need to live in RAM-backed HNSW — tiered storage puts hot data on fast, expensive paths and cold data on slow, cheap ones, automatically."
---

# 08 · Cost-Performance Tradeoffs at Enterprise Scale

Everything in this course so far optimizes for correctness and speed. At
enterprise scale — tens or hundreds of millions of vectors, sustained query
load, real cloud bills — cost becomes a first-class design constraint
alongside them. This lesson covers the levers teams actually pull.

## Reserved vs. on-demand capacity

Managed vector DB providers typically offer both:

- **On-demand / serverless**: pay per query and per GB stored, scales
  automatically, no capacity planning — good for unpredictable or low/bursty
  traffic, but can cost significantly more per-unit at sustained high
  volume.
- **Reserved / dedicated capacity**: pay a flat rate for provisioned pods or
  nodes regardless of usage, cheaper per-unit at sustained high volume, but
  you pay for idle capacity during traffic troughs and need to actually
  forecast load correctly.

The crossover point depends on your actual query volume and provider
pricing — the general shape, true across most providers, is that reserved
capacity wins once sustained utilization is high enough to justify paying
for always-on capacity; below that, on-demand's pay-per-use model wins
because you're not paying for idle time. Model this explicitly with your
own numbers rather than defaulting to either — most teams start on-demand,
measure real sustained usage for a few weeks, then calculate whether
reserved capacity would have been cheaper at that observed load, and switch
if so.

## Tiered storage: hot, warm, cold

Not every vector in your corpus gets queried equally often. Analytics
almost always show a long tail: a small fraction of documents (recent
content, popular products, frequently-asked questions) account for most
query traffic, while the rest sits essentially idle.

```python
def classify_tier(doc_id: str, last_accessed_days_ago: int, access_count_30d: int) -> str:
    if access_count_30d > 100 or last_accessed_days_ago < 7:
        return "hot"
    elif last_accessed_days_ago < 90:
        return "warm"
    return "cold"
```

- **Hot tier**: fully indexed (HNSW, in-memory or fast SSD), low-latency
  path — this is what most of the course has assumed by default.
  Expensive per-vector, fast.
- **Warm tier**: indexed but on cheaper storage, or indexed with lower-
  resource settings (fewer graph connections, lower `ef_search`) that trade
  a little recall for lower cost.
  Moderate cost, moderate latency.
  (Flat/brute-force index, or an IVF index with fewer, coarser clusters
  from Level 2 — cheap to store, slower to query, acceptable because cold
  data is rarely queried at all.)

Many teams implement this with two (or three) separate collections or
indexes, and a routing layer that checks the hot tier first, falling back
to warm/cold only on a cache miss or for queries explicitly scoped to older
data (e.g. "search my archived tickets").

```python
def tiered_search(query_embedding, top_k=5):
    hot_results = hot_store.search(query_embedding, top_k)
    if len(hot_results) >= top_k and hot_results[0].score > 0.7:
        return hot_results  # good enough match found in the cheap-to-query hot tier

    # Fall back to warm/cold only when the hot tier didn't have a confident match
    warm_results = warm_store.search(query_embedding, top_k)
    return merge_and_rerank(hot_results, warm_results, top_k)
```

## Pre-computing and caching expensive queries

If your query distribution has repeats — common questions, popular search
terms — cache the embedding computation (skip re-calling the embedding
model for an identical query string) and, where acceptable, cache the
*search results themselves* for a short TTL (Level 3's caching lesson
covers this pattern in depth). At enterprise query volume, this alone can
cut embedding-API spend and vector-DB query load substantially, since a
meaningful fraction of real-world query traffic is exact or near-exact
repeats.

## Right-sizing dimensionality

Higher-dimensional embeddings aren't always worth their cost. A 1536-
dimension embedding costs 4x the storage and query compute of a
384-dimension one, for a quality gain that's often much smaller than 4x,
especially past a model-specific point of diminishing returns. Two levers:

- **Choose a smaller model** if your eval metrics (lesson 2) show
  acceptable quality at a smaller embedding size — don't default to the
  largest available model without measuring whether you need it.
- **Matryoshka truncation** (covered in depth in lesson 9): with a model
  trained for it, you can truncate a full embedding down to a smaller
  prefix of its dimensions and still get a usable, if slightly less
  accurate, embedding — letting you dynamically trade dimensionality for
  cost per-query or per-tier, using the *same* model and the *same*
  original embeddings, rather than maintaining two different models.

```python
# A matryoshka-style model: truncate the embedding before storage/indexing
full_embedding = model.encode("some document text")  # e.g. 768 dims
truncated_for_warm_tier = full_embedding[:128]        # cheaper to store and index
truncated_for_warm_tier = truncated_for_warm_tier / np.linalg.norm(truncated_for_warm_tier)
```

## Putting it together

A realistic enterprise cost model combines several of these at once: hot
tier on reserved capacity with full-dimension embeddings for the top 5% of
frequently-queried documents, warm tier on cheaper on-demand infrastructure
with truncated (matryoshka) embeddings for the long tail, aggressive query
result caching in front of both, and a tiering job that re-classifies
documents periodically as access patterns shift (yesterday's cold document
can become tomorrow's hot one after a product launch or news event).

## Exercise

Taking your RAG retrieval service from Level 2, sketch (in writing) a
two-tier design: define the exact criteria you'd use to classify a document
as hot vs. cold, what index/storage configuration you'd use for each tier,
and roughly estimate (using any provider's published pricing, or rough
order-of-magnitude numbers) how much cheaper the two-tier design would be
than treating 100% of your corpus as hot, assuming an 80/20 access pattern
(80% of queries touch 20% of documents).
