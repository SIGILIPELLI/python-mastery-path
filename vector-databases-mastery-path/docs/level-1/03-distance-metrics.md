---
description: "Cosine similarity is just the dot product of two normalized vectors — which is why nearly every production vector database normalizes embeddings and uses dot product internally for speed."
---

# 03 · Distance Metrics (Cosine, Euclidean, Dot Product)

Every vector search boils down to "how far apart are these two vectors?" —
but "far apart" can mean different things. This lesson covers the three
metrics you'll see in every vector database you touch.

## Euclidean distance (L2)

Straight-line distance between two points, generalized to N dimensions:

```python
import numpy as np

def euclidean_distance(a, b):
    return np.linalg.norm(a - b)

a = np.array([1.0, 2.0, 3.0])
b = np.array([2.0, 1.0, 4.0])
print(euclidean_distance(a, b))   # sqrt(1+1+1) ≈ 1.732
```

Euclidean distance cares about **absolute position**, including magnitude.
Two vectors pointing in the exact same direction but with different lengths
will have nonzero Euclidean distance between them.

## Dot product

```python
def dot_product(a, b):
    return np.dot(a, b)

print(dot_product(a, b))   # 1*2 + 2*1 + 3*4 = 16
```

The dot product gets *larger* as vectors point in more similar directions
and have larger magnitudes — it's a similarity measure, not a distance (bigger
= more similar, unlike the distances above where smaller = more similar).

## Cosine similarity

Cosine similarity measures the **angle** between two vectors, ignoring their
magnitude entirely:

```python
def cosine_similarity(a, b):
    return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))

a = np.array([1.0, 2.0, 3.0])
b = np.array([2.0, 4.0, 6.0])   # same direction as a, just scaled 2x
print(cosine_similarity(a, b))   # 1.0 — identical direction, "perfectly similar"
print(euclidean_distance(a, b))  # 3.74 — but far apart in Euclidean terms!
```

This is why cosine is the default for text embeddings: two embeddings for
"I love this product" and "I LOVE THIS PRODUCT!!!" might differ in magnitude
(different word counts, different emphasis) but should still be judged as
pointing in nearly the same semantic direction.

Cosine similarity ranges from `-1` (opposite) through `0` (unrelated/
orthogonal) to `1` (identical direction).

## When to use which

| Metric | Use when... |
|---|---|
| **Cosine** | Default for text embeddings — direction (meaning) matters, magnitude doesn't |
| **Euclidean** | Absolute position matters — e.g. spatial coordinates, some image embeddings |
| **Dot product** | You've already normalized every vector to unit length — then it equals cosine, but is cheaper to compute |

Every vector database you'll use in this course (Chroma, Pinecone, Weaviate,
Qdrant, pgvector) lets you pick a metric per collection/index — usually
`cosine`, `l2` (Euclidean), or `dotproduct`/`ip` (inner product).

## How It Actually Works

Why does normalizing a vector make dot product behave exactly like cosine
similarity?

1. **Cosine similarity's formula is `(a · b) / (‖a‖ ‖b‖)`.** It's the dot
   product, scaled down by both vectors' magnitudes.
2. **If both vectors are already unit length** (`‖a‖ = 1` and `‖b‖ = 1`),
   the denominator becomes `1 * 1 = 1`, so the formula collapses to just
   `a · b` — the raw dot product.
3. **This means: normalize once, compare cheaply forever.** A production
   vector database can normalize every embedding exactly once at insert
   time, then use the plain dot product (a single fused multiply-add loop,
   extremely cheap on modern CPUs/GPUs with SIMD instructions) for every
   future comparison — instead of recomputing two `norm()` calls on every
   single query-to-vector comparison.
4. **This is why most embedding models (including `sentence-transformers`
   models you'll use in Lesson 5) ship with a `normalize_embeddings=True`
   option** — so you can store unit vectors and let the database use the
   fastest possible similarity operation while still getting cosine
   semantics.
5. **Verify it yourself:**

```python
def normalize(v):
    return v / np.linalg.norm(v)

a = np.array([1.0, 2.0, 3.0])
b = np.array([2.0, 1.0, 4.0])

cos_sim = cosine_similarity(a, b)
dot_of_normalized = np.dot(normalize(a), normalize(b))

print(cos_sim, dot_of_normalized)   # same value, two different routes
```

## Exercise

Using the 4 toy documents from Lesson 2 (`documents` dict with
`[animals, technology, food, sports]` dimensions), write a function that
computes the cosine similarity of `doc1` against `doc2`, `doc3`, and `doc4`.
Print the results sorted from most to least similar, and in a one-line
comment explain whether the ranking matches what you'd intuitively expect
given the documents' themes.
