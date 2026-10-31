---
description: "Brute-force search checks every single vector for every query — correct and simple, but its O(n) cost is exactly the problem every vector database index exists to solve."
---

# 04 · Brute-Force Similarity Search

## The simplest possible vector search

Before touching a real database, build the search algorithm every vector
database is secretly approximating under the hood: compare your query
against *every* stored vector, and return the closest ones.

```python
import numpy as np

documents = {
    "doc1": np.array([0.9, 0.1, 0.0, 0.0]),
    "doc2": np.array([0.8, 0.2, 0.1, 0.0]),
    "doc3": np.array([0.0, 0.9, 0.1, 0.0]),
    "doc4": np.array([0.0, 0.0, 0.1, 0.9]),
    "doc5": np.array([0.85, 0.15, 0.05, 0.0]),
}

def cosine_similarity(a, b):
    return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))

def brute_force_search(query, documents, top_k=3):
    scored = [
        (name, cosine_similarity(query, vec))
        for name, vec in documents.items()
    ]
    scored.sort(key=lambda pair: pair[1], reverse=True)
    return scored[:top_k]

query = np.array([0.88, 0.12, 0.0, 0.0])   # "about animals"
results = brute_force_search(query, documents, top_k=3)
for name, score in results:
    print(f"{name}: {score:.4f}")
```

```text
doc5: 0.9999
doc1: 0.9937
doc2: 0.9802
```

That's it — this is a real, correct nearest-neighbor search. Every vector
database's job is ultimately to return exactly this ranking, just faster.

## Scaling it up with pure NumPy

For a slightly larger, more realistic dataset, do it in one vectorized pass
instead of a Python loop — this is how you'd actually write it outside a
toy example:

```python
import numpy as np

rng = np.random.default_rng(seed=42)
n_docs, dims = 10_000, 128

# Simulate 10,000 random "document" vectors
dataset = rng.normal(size=(n_docs, dims))
dataset = dataset / np.linalg.norm(dataset, axis=1, keepdims=True)  # normalize each row

query = rng.normal(size=(dims,))
query = query / np.linalg.norm(query)

# One matrix-vector multiply computes similarity to ALL 10,000 vectors at once
similarities = dataset @ query          # shape (10000,)
top_k = 5
top_indices = np.argsort(similarities)[::-1][:top_k]

for idx in top_indices:
    print(f"doc #{idx}: similarity={similarities[idx]:.4f}")
```

Because every vector is pre-normalized, `dataset @ query` is a single dot
product per row — cosine similarity computed for all 10,000 documents in one
NumPy call.

## Timing it

```python
import time

start = time.perf_counter()
similarities = dataset @ query
elapsed = time.perf_counter() - start
print(f"Searched {n_docs} vectors in {elapsed*1000:.2f} ms")
```

On a laptop, 10,000 128-dimensional vectors search in a few milliseconds.
Feels instant. The problem starts when `n_docs` grows.

## Why this doesn't scale

Brute force is **O(n)**: double the number of vectors, double the search
time, no exceptions. That's fine at 10,000 vectors. It stops being fine at
real-world scale:

| Dataset size | Rough brute-force search time* |
|---|---|
| 10,000 vectors | ~1-5 ms |
| 1,000,000 vectors | ~100-500 ms |
| 100,000,000 vectors | ~10-50 seconds |
| 1,000,000,000 vectors | minutes |

*Rough order-of-magnitude, single machine, single query — actual numbers
depend on dimensionality and hardware.

A production RAG system or recommendation engine needs to answer queries in
tens of milliseconds, against collections that can hold hundreds of millions
to billions of vectors, often with many queries per second concurrently.
Linear scan simply cannot keep up — you can't compute a billion dot products
per query, per second, no matter how fast your CPU is.

This is exactly the gap that **Approximate Nearest Neighbor (ANN)** search
fills — trading a small amount of accuracy for a massive speedup by *not*
checking every vector. You'll get your first real taste of how in Lesson 6,
and the full mechanics (HNSW, IVF, product quantization) in Level 2.

## Exercise

Extend the timing experiment above: run the same brute-force search at
`n_docs = 1_000`, `10_000`, `100_000`, and `1_000_000` (keep `dims = 128`),
timing each with `time.perf_counter()`. Plot or print the results and
confirm the relationship between `n_docs` and search time is roughly
linear, as the O(n) label predicts.
