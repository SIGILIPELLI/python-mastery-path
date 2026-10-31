---
description: "HNSW's top layer has almost no nodes on purpose — it exists purely so search can take a few huge jumps across the whole graph before zooming in."
---

# 05 · How HNSW Actually Works

Every database you've used so far (Chroma, Pinecone, Qdrant, pgvector's HNSW
index) defaults to the same algorithm under the hood: Hierarchical Navigable
Small World graphs. Level 1 introduced the idea conceptually. This lesson goes
inside it.

## The problem HNSW solves

Brute-force search (Level 1, lesson 4) compares your query against every vector:
`O(n)`. A flat navigable small-world graph — a single layer where each vector
links to its nearest neighbors — turns search into a greedy graph walk, which is
much faster on average, but can still take many hops to cross a large, spread-out
graph, and can get stuck in a locally-good-but-globally-wrong region. HNSW fixes
both by stacking multiple layers of that graph on top of each other.

## Building the layers

Each vector is inserted into layer 0 (the bottom layer, containing *all* vectors)
and, with exponentially decreasing probability, into higher layers too. A rough
mental model with branching factor-like decay:

```
Layer 2:        •                       •              (very few nodes)
Layer 1:        •        •      •       •      •       (some nodes)
Layer 0:  • • •  • •  • • • •  •  • • •  • • • •  • •   (every node)
```

Layer 0 has every vector and dense, short-range links. Each layer up has
exponentially fewer vectors and longer-range links. The top layer might have
only a handful of nodes — just enough to act as highway on-ramps into the rest
of the graph.

## Searching: greedy descent through layers

1. Start at a fixed entry point in the top layer.
2. **Greedy search within the current layer**: repeatedly move to whichever
   neighbor is closer to the query than your current position, until no neighbor
   improves (a local minimum for this layer).
3. **Drop down one layer**, using the local minimum you just found as the new
   starting point.
4. Repeat the greedy search at the new layer. Because the previous layer narrowed
   you down to roughly the right neighborhood, this layer's greedy search only
   needs a few more hops to refine further.
5. Continue until you've done a final greedy search at layer 0, maintaining a
   candidate list of the `ef_search` best vectors seen, and return the top `k`.

This is why the top layer can be sparse and still useful: it's not trying to be
accurate, it's trying to get you to roughly the right region of the graph in a
handful of long jumps, so that lower layers only need short jumps to refine.

## How It Actually Works

- **`M` (max connections per node)**: how many neighbor links each node keeps per
  layer. Higher `M` means denser graphs, better recall, more memory, slower
  inserts. Typical values: 12-48.
- **`ef_construction`**: how large a candidate list is explored while *building*
  the graph (choosing which neighbors to link). Higher values build a
  higher-quality graph at the cost of slower index construction.
- **`ef_search`**: how large a candidate list is explored while *querying*.
  Higher values improve recall (closer to true nearest neighbors) at the cost of
  slower queries. This is the main knob you tune at query time without rebuilding
  the index — most databases expose it directly (Qdrant's `hnsw_ef`, pgvector's
  `hnsw.ef_search` session setting).
- **Why it's "approximate"**: greedy search can still terminate at a local
  minimum that isn't the true global nearest neighbor, especially with `ef`
  values set low. Recall (the fraction of true top-k results actually returned)
  typically lands in the 95-99.9% range for reasonable settings — good enough for
  nearly every real application, and the gap closes as `ef` increases.
- **Insertion cost**: every insert runs a search (to find where to link the new
  node) plus graph updates at multiple layers, which is why HNSW indexes are
  noticeably slower to build than to query, and why very write-heavy workloads
  sometimes prefer IVF-based indexes (next lesson) or batch rebuilding.
- **Memory**: the full graph — all nodes' neighbor lists across all layers —
  typically lives in RAM for query speed, which is why HNSW memory usage scales
  with `M` and vector count, and is often the dominant cost driver for
  self-hosted vector databases at scale.

## Exercise

In Qdrant (lesson 3) or pgvector (lesson 4), create two collections/indexes over
the same 10,000+ vector dataset (synthetic random vectors are fine for this) —
one with a low `ef_search`/`M` and one with a high value — and measure both query
latency and recall@10 (compare each approximate result set against a brute-force
ground truth computed with NumPy, as in Level 1 lesson 4). Report the
latency/recall tradeoff you observe.
