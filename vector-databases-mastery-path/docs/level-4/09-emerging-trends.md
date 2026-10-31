---
description: "Matryoshka embeddings let you truncate a vector from 768 to 128 dimensions and still get a usable result, because the model was trained to put the most important information first."
---

# 09 · Emerging Trends — Matryoshka & Binary Quantization

The previous lesson mentioned both of these as cost levers — this lesson
goes into how they actually work, because both rely on a specific training
or encoding trick, not just "store less data and hope it's fine."

## Matryoshka Representation Learning

Named after Russian nesting dolls, **Matryoshka Representation Learning**
(MRL) trains an embedding model so that *every prefix* of the full
embedding — not just the complete vector — is itself a usable embedding.
A 768-dimension Matryoshka embedding's first 128 dimensions, taken alone,
already encode a coarser but legitimate representation of the same input;
its first 256 dimensions encode a somewhat better one, and so on up to the
full 768.

```python
from sentence_transformers import SentenceTransformer

# Matryoshka-trained models commonly support truncate_dim directly
model = SentenceTransformer("nomic-ai/nomic-embed-text-v1.5", trust_remote_code=True)

full = model.encode("vector databases are useful", normalize_embeddings=False)
print(full.shape)  # (768,)

model_truncated = SentenceTransformer(
    "nomic-ai/nomic-embed-text-v1.5", trust_remote_code=True, truncate_dim=128
)
truncated = model_truncated.encode("vector databases are useful")
print(truncated.shape)  # (128,)
```

If a model doesn't expose a `truncate_dim` parameter but is known to be
Matryoshka-trained, you can truncate manually — take the first N dimensions
and re-normalize:

```python
def matryoshka_truncate(embedding: np.ndarray, dims: int) -> np.ndarray:
    truncated = embedding[:dims]
    return truncated / np.linalg.norm(truncated)
```

This is categorically different from truncating an *ordinary* embedding
model's output, which would just throw away arbitrary, equally-important
information and badly degrade quality — Matryoshka training specifically
teaches the model to front-load the most semantically important
information into the earliest dimensions during training, which is what
makes truncation viable at all.

## Using Matryoshka dimensions as a cost lever

Store the full embedding once, and serve different dimensionalities to
different tiers (tying back to lesson 8's hot/warm/cold design) without
maintaining separate models or re-embedding anything:

```python
def tier_embedding(full_embedding: np.ndarray, tier: str) -> np.ndarray:
    dims = {"hot": 768, "warm": 256, "cold": 64}[tier]
    return matryoshka_truncate(full_embedding, dims)
```

A common production pattern: use a small truncated dimension for a fast
first-pass retrieval over the *entire* corpus, then re-rank the top
candidates using the full-dimension embedding (or a cross-encoder from
Level 3) for final precision — getting most of the speed of a small
embedding with most of the accuracy of a large one.

## Binary and scalar quantization

A standard embedding stores each dimension as a 32-bit float. **Scalar
quantization** reduces each dimension to 8 bits (mapping the float range to
256 buckets); **binary quantization** goes further, reducing each dimension
to a single bit (is this dimension's value above or below zero/the mean).

```python
def binary_quantize(embedding: np.ndarray) -> np.ndarray:
    return (embedding > 0).astype(np.uint8)  # 1 bit per dimension, packed by caller

def scalar_quantize_int8(embedding: np.ndarray, min_val: float, max_val: float) -> np.ndarray:
    scaled = (embedding - min_val) / (max_val - min_val)  # normalize to [0, 1]
    return (scaled * 255).astype(np.uint8)
```

Binary quantization shrinks storage 32x versus float32 (1 bit vs. 32 bits
per dimension) and lets distance computation use **Hamming distance**
(count differing bits, a CPU-level operation via XOR + popcount) instead of
floating-point cosine similarity — dramatically faster at scale.

```python
def hamming_distance(a: np.ndarray, b: np.ndarray) -> int:
    return int(np.count_nonzero(a != b))
```

The obvious cost: binary-quantizing throws away a lot of information, so
recall drops relative to full-precision search. The standard mitigation is
a **two-stage pipeline**: use binary quantization for a cheap, extremely
fast first pass over the whole corpus to get a candidate shortlist (e.g.
top 200), then re-score only that shortlist with full-precision float32
vectors for the final top-k. Several production vector DBs (Qdrant,
Weaviate) support this pattern natively via configuration rather than
requiring you to hand-roll it.

```python
def two_stage_search(query_embedding, top_k=10, candidate_pool=200):
    query_binary = binary_quantize(query_embedding)
    candidates = binary_index.search(query_binary, top_k=candidate_pool)  # fast, approximate

    candidate_full_vectors = fetch_full_precision(candidates)
    rescored = [
        (c.id, cosine_similarity(query_embedding, v))
        for c, v in zip(candidates, candidate_full_vectors)
    ]
    rescored.sort(key=lambda x: x[1], reverse=True)
    return rescored[:top_k]
```

## Combining both

Matryoshka and quantization are independent, stackable levers: you can
binary-quantize a *truncated* 128-dimension Matryoshka embedding for an
extremely cheap first-pass filter, then re-rank candidates using the full
768-dimension float32 embedding. This two-dimensional cost/quality knob
(dimensionality × precision) is increasingly how large-scale production
systems (billions of vectors) stay both fast and affordable — full-size,
full-precision search simply doesn't fit the latency or cost budget at that
scale, and both of these techniques exist specifically to make large-scale
approximate search cheap without abandoning accuracy at the final ranking
step.

## How It Actually Works

1. **Why Matryoshka training works at all.** The training loss sums the
   standard contrastive loss computed independently at *several*
   dimensionalities (e.g. loss at 768 dims + loss at 256 dims + loss at 64
   dims, all from the same underlying vector, just truncated to different
   lengths). This forces the optimizer to find a representation where
   *every* prefix length is independently good — which is a much stronger
   constraint than ordinary training, and is exactly why you can't get this
   property by truncating a conventionally-trained embedding after the
   fact.
2. **Why Hamming distance on binary vectors is so much faster than
   cosine similarity on floats.** Hamming distance between two bit-packed
   vectors reduces to a single XOR instruction plus a hardware population-
   count instruction, both of which operate on 64 bits at a time with
   dedicated CPU instructions — versus cosine similarity's floating-point
   multiply-accumulate over every dimension. At billion-vector scale, this
   difference compounds into a real, measurable throughput gain for the
   first-pass candidate generation step.
3. **Why the two-stage re-rank is necessary, not optional.** Binary
   quantization's 1-bit-per-dimension resolution means many genuinely
   different vectors collapse to the same or very similar bit patterns —
   recall on the raw binary index alone is meaningfully worse than
   full-precision search. The re-ranking step recovers most of that lost
   precision cheaply, because it only has to run full-precision comparison
   on a small shortlist (hundreds) instead of the entire corpus (millions
   or billions).

## Exercise

Take embeddings from your semantic search CLI (Level 1) and implement
binary quantization plus the two-stage re-rank pipeline above against your
existing corpus. Compare Recall@10 (lesson 2) between plain full-precision
search and the two-stage binary-quantized pipeline with a candidate pool of
50. Report whether the quality loss is noticeable at your corpus size, and
how it might change at 1000x the corpus size.
