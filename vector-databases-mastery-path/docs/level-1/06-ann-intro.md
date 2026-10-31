---
description: "Approximate Nearest Neighbor search deliberately skips checking most vectors — trading a tiny, tunable amount of recall for orders-of-magnitude faster queries at scale."
---

# 06 · Intro to Approximate Nearest Neighbor Search

## The core trade-off

Lesson 4 showed that brute-force search is O(n) — every query has to touch
every vector. **Approximate Nearest Neighbor (ANN)** search breaks that rule
on purpose: it pre-organizes vectors into a data structure that lets a query
skip over most of the dataset, at the cost of occasionally missing the
*true* single best match in exchange for something nearly as good, much
faster.

"Approximate" sounds risky, but in practice a well-tuned ANN index finds the
true top-k results (or something essentially as relevant) 95-99%+ of the
time — a trade nearly every production system is happy to make for a
10-100x speedup.

## Why organization beats brute checking

Think about how you'd find a word in a dictionary. You don't read every
page — you flip to roughly the right letter, then narrow down. That's only
possible because the dictionary is *organized* (alphabetically). Unorganized
data forces a linear scan; organized data lets you skip straight to the
relevant region.

ANN indexes do the same thing for vector space: they build a structure at
insert time so that at query time, you can jump straight to the
neighborhood that's likely to contain the nearest vectors, instead of
visiting every single one.

## A quick taste: clustering as a crude ANN

One of the simplest ANN ideas — group vectors into clusters, and at query
time only search the clusters nearest the query, not all of them:

```python
import numpy as np
from sklearn.cluster import KMeans   # pip install scikit-learn

rng = np.random.default_rng(0)
dataset = rng.normal(size=(10_000, 64))
dataset /= np.linalg.norm(dataset, axis=1, keepdims=True)

# Partition into 50 clusters at "index build" time
kmeans = KMeans(n_clusters=50, random_state=0).fit(dataset)
cluster_centers = kmeans.cluster_centers_
cluster_labels = kmeans.labels_

def ann_cluster_search(query, top_clusters=3, top_k=5):
    # Step 1: find the nearest cluster centers (fast — only 50 comparisons)
    center_sims = cluster_centers @ query
    nearest_clusters = np.argsort(center_sims)[::-1][:top_clusters]

    # Step 2: only brute-force search WITHIN those clusters
    candidate_mask = np.isin(cluster_labels, nearest_clusters)
    candidates = dataset[candidate_mask]
    candidate_indices = np.where(candidate_mask)[0]

    sims = candidates @ query
    top = np.argsort(sims)[::-1][:top_k]
    return candidate_indices[top], sims[top]

query = rng.normal(size=(64,))
query /= np.linalg.norm(query)

indices, scores = ann_cluster_search(query)
print(list(zip(indices, scores)))
```

Instead of 10,000 comparisons, this does roughly `50 + (10,000/50 * 3)` ≈
650 — about **15x fewer comparisons**, at the cost of occasionally missing a
true nearest neighbor that happened to fall just outside the 3 clusters
searched. (This exact technique, done properly, is called **IVF** —
Inverted File Index — and you'll build it for real in Level 2, Lesson 6.)

## How It Actually Works

Real production ANN indexes (like **HNSW** — Hierarchical Navigable Small
World graphs, used by Chroma, Pinecone, Weaviate, Qdrant, and pgvector) take
this idea much further. You'll implement and tune HNSW in depth in Level 2,
Lesson 5 — but the intuition is worth building now:

1. **Vectors become nodes in a graph**, connected to a handful of their
   nearest neighbors — not to everything, just a small set of "close
   friends."
2. **The graph has multiple layers**, like a highway system. The top layer
   has very few nodes with long-range connections (the highways); lower
   layers have progressively more nodes with short-range connections (the
   side streets).
3. **A query starts at the top layer** and greedily moves toward whichever
   connected node is closest to the query — covering large distances in
   very few hops, the same way you'd take a highway before exiting onto
   local roads.
4. **It drops down a layer each time it stops improving**, repeating the
   greedy walk on a denser layer, until it's walked all the way down to the
   bottom (densest) layer and converged on a small set of very close
   candidates.
5. **Total comparisons per query end up roughly logarithmic in dataset
   size** (`O(log n)`) instead of linear (`O(n)`) — which is *why* HNSW
   search on a billion vectors can still return results in single-digit
   milliseconds, something no brute-force approach could ever do.
6. **The "approximate" part**: because the walk is greedy (always move
   toward the locally-closest neighbor) rather than exhaustive, it can get
   stuck in a locally-good-but-not-globally-best region — missing the true
   best match in a small fraction of queries. Tuning parameters (search
   width, number of layers) let you trade recall for speed.

## Exercise

Modify the clustering example above to measure **recall**: run
`ann_cluster_search` for 50 random queries, and for each one also run true
brute-force search (`dataset @ query`, full sort) to get the real top-5.
Compute what fraction of the ANN result's top-5 indices actually appear in
the true top-5. Then re-run with `top_clusters=1` and `top_clusters=10` and
observe how recall changes as you search more (or fewer) clusters.
