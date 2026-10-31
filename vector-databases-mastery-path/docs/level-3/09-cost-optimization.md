---
description: "Quantizing vectors from 32-bit floats to 8-bit integers cuts storage (and often cost) 4x with only a small, usually acceptable, hit to recall."
---

# 09 · Cost Optimization at Scale

## What actually drives vector DB cost

At meaningful scale (tens of millions of vectors and up), cost comes from a
few distinct places, and they don't all respond to the same fix:

- **Storage** — raw vector bytes, plus index overhead (HNSW graphs
  typically add 20-50% on top of raw vector storage for the graph edges),
  plus metadata.
- **Write/compute operations** — inserts, upserts, and deletes, especially
  on managed/serverless pricing where each operation has a cost.
- **Query operations** — each search call, sometimes billed per-query,
  sometimes bundled into compute-time pricing.
- **Embedding generation** — if you use a hosted embedding API rather than
  a local model, every document (and every query) you embed is a metered
  API call, and for a large or frequently re-indexed corpus this can
  dwarf the vector DB's own bill.

## Serverless vs. reserved/dedicated pricing

Most managed vector DBs (Pinecone, Qdrant Cloud, Weaviate Cloud) offer both:

- **Serverless** — pay per operation and per GB stored, no idle capacity to
  provision. Cost scales directly with usage, which is cheap at low/bursty
  volume but can get expensive per-unit at sustained high volume.
- **Reserved/dedicated** — pay a fixed rate for provisioned
  compute/memory regardless of how much you actually use. Cheaper per-unit
  at high, steady volume, but you're paying for idle capacity during quiet
  periods.

The crossover point is a function of your actual query/write volume and how
steady it is — a workload with predictable, high, constant traffic usually
favors reserved; a spiky or low-volume workload usually favors serverless.
The only reliable way to know which is cheaper for *you* is to estimate both
against your real (or realistically projected) traffic, not a vendor's
example numbers.

## Dimensionality reduction

A smaller embedding dimension means less storage per vector and faster
distance computation (fewer multiply-adds per comparison), at some cost to
representational quality.

```python
from sklearn.decomposition import PCA
import numpy as np

# Reduce 768-dim embeddings to 256-dim, fit on a representative sample
pca = PCA(n_components=256)
reduced_sample = pca.fit(sample_embeddings)  # fit once on a large enough sample

def reduce_embedding(full_embedding: np.ndarray) -> np.ndarray:
    reduced = pca.transform([full_embedding])[0]
    return reduced / np.linalg.norm(reduced)  # re-normalize after reduction
```

Some embedding models are explicitly trained to support this natively —
**Matryoshka embeddings** (covered in the next lesson) produce vectors
where the first N dimensions are already a valid, independently useful
lower-dimensional embedding, so you can truncate instead of needing a
separate PCA step.

## Quantization

Quantization reduces the *precision* of each number in a vector rather than
the count of numbers — storing each dimension in fewer bits.

- **Float32 → int8 (scalar quantization)**: roughly 4x storage reduction.
  Each dimension is mapped from its float range into 256 discrete levels.
  Recall impact is typically small (often under 1-2 percentage points) if
  done carefully with a calibrated range.
- **Binary quantization**: each dimension becomes a single bit (sign only).
  This is roughly 32x storage reduction compared to float32, with a larger
  recall hit, but is fast enough to use as a cheap first-pass filter before
  a more precise re-scoring step on the original float vectors.

```python
def quantize_int8(vector: np.ndarray, vmin: float, vmax: float) -> np.ndarray:
    scale = 255.0 / (vmax - vmin)
    return np.clip(((vector - vmin) * scale), 0, 255).astype(np.uint8)
```

Most managed vector databases (Qdrant, Weaviate) support quantization as a
built-in index option rather than requiring you to hand-roll it — the
pattern above is to understand the mechanism, not to reimplement it in
production.

## Caching to cut embedding-API spend

If you're embedding with a hosted API (rather than a free local model),
every repeat or near-duplicate text you re-embed is paying twice for the
same work. The embedding cache from lesson 6 (`lru_cache` or Redis, keyed by
exact text) directly reduces this cost line — and for corpora with a lot of
near-duplicate content (templated documents, boilerplate sections repeated
across many files), de-duplicating identical chunks before embedding at all
is often the single biggest lever:

```python
def dedupe_before_embedding(chunks: list[str]) -> tuple[list[str], dict[int, int]]:
    """Returns unique chunks plus a mapping from original index to unique index."""
    seen: dict[str, int] = {}
    unique_chunks = []
    index_map = {}
    for i, chunk in enumerate(chunks):
        if chunk not in seen:
            seen[chunk] = len(unique_chunks)
            unique_chunks.append(chunk)
        index_map[i] = seen[chunk]
    return unique_chunks, index_map
```

## Exercise

Take your corpus from an earlier level and estimate its actual storage cost
two ways: full float32 embeddings vs. int8-quantized. Compute the size
reduction. Then measure recall@5 (from lesson 5) on both — the full-precision
version and a simulated int8-quantized version using the `quantize_int8`
function above (quantize, then dequantize back to float before comparing, to
simulate the precision loss) — and report how much recall you actually lose
for the storage savings.
