---
description: "Product quantization can shrink a 384-dimension float32 vector from 1.5KB to under 100 bytes by replacing each chunk of it with a codebook lookup ID."
---

# 06 · IVF & Product Quantization

HNSW (previous lesson) trades memory for speed: the whole graph lives in RAM.
At billion-vector scale, that memory bill gets enormous. IVF (Inverted File
Index) and Product Quantization (PQ) are a different pair of tricks — often used
together — that trade a little accuracy for dramatically less memory and, for
IVF, fewer distance computations per query.

## Inverted File Index (IVF): cluster first, search locally

1. **Build time**: run k-means clustering on a sample of your vectors to produce
   `nlist` cluster centroids (e.g. `nlist=1024`). Every vector in the dataset is
   then assigned to its nearest centroid — this is its "inverted list."
2. **Query time**: compare the query vector against only the `nlist` centroids
   (cheap — there are far fewer centroids than vectors), find the `nprobe`
   closest centroids, and only search the vectors inside *those* lists.

```python
import faiss
import numpy as np

d = 384
nlist = 1024
quantizer = faiss.IndexFlatL2(d)
index = faiss.IndexIVFFlat(quantizer, d, nlist)

vectors = np.random.random((100_000, d)).astype("float32")
index.train(vectors)   # runs k-means to find centroids
index.add(vectors)

index.nprobe = 16       # search the 16 nearest clusters out of 1024
distances, ids = index.search(np.random.random((1, d)).astype("float32"), k=5)
```

If a dataset has 10 million vectors spread across 1024 clusters (~10,000 vectors
each) and you set `nprobe=16`, you're scanning roughly 160,000 vectors instead of
10 million — a ~60x reduction, at the cost of possibly missing a true neighbor
that happened to land in a nearby-but-unsearched cluster (this is IVF's source of
approximation, distinct from HNSW's).

## Product Quantization (PQ): compress the vectors themselves

IVF reduces *how many* vectors you compare against. PQ reduces *how expensive*
each comparison is, by compressing each vector.

1. Split each `d`-dimensional vector into `m` equal-length subvectors (e.g. a
   384-dim vector split into `m=8` subvectors of 48 dimensions each).
2. For each of the `m` subvector positions, run k-means independently to learn a
   small codebook of (commonly) 256 centroids.
3. Store each original vector as just `m` codebook indices (e.g. 8 bytes total —
   one byte per subvector, since 256 centroids fit in a `uint8`) instead of
   `d` floats (384 × 4 bytes = 1536 bytes).

```python
m = 8          # number of subvector chunks
nbits = 8      # bits per code → 2^8 = 256 centroids per chunk
pq_index = faiss.IndexIVFPQ(quantizer, d, nlist, m, nbits)
pq_index.train(vectors)
pq_index.add(vectors)
```

Distance between a query and a compressed vector is computed approximately using
precomputed lookup tables between the query's subvectors and each chunk's
codebook — not by decompressing back to full floats, which is what makes PQ fast
*and* memory-cheap simultaneously, not just memory-cheap.

## How It Actually Works

- **Why cluster first (IVF)**: a flat/brute-force scan is `O(n)` per query. IVF
  turns that into `O(nlist)` (compare against centroids) `+ O(n/nlist * nprobe)`
  (scan only the probed lists) — a large win when `nlist` is well-chosen relative
  to `n`.
- **The `nprobe` tradeoff**: `nprobe=1` only searches the single nearest cluster —
  fast but misses any true neighbor whose cluster boundary happened to separate
  it from the query. Increasing `nprobe` toward `nlist` approaches brute-force
  accuracy at brute-force cost; there's no free lunch, only a slider.
  "Boundary problem": a query near a cluster edge may have its true nearest
  neighbor sitting just across that edge in an unsearched cluster — this is IVF's
  main failure mode, and why `nprobe > 1` is almost always used in practice.
  "Boundary problem" is why real deployments rarely use `nprobe=1`.
- **Why PQ compression doesn't ruin accuracy outright**: subvector codebooks are
  trained on real data distribution (via k-means), so the quantization error per
  chunk is small relative to the chunk's own variance — not uniform random noise.
  Still, PQ alone (without IVF) is a lossy approximation of distance, so
  recall drops somewhat versus exact float comparison; this is the accuracy half
  of the tradeoff, paid for 16-32x memory reduction.
- **IVF+PQ together**: the combination (`IndexIVFPQ` above) is the classic
  "fits in RAM at billion-scale" recipe — IVF narrows the candidate set, PQ makes
  each candidate comparison and each vector's storage footprint tiny. This is
  roughly what Pinecone, Milvus, and FAISS-backed systems use under the hood at
  very large scale, often layered with additional re-ranking against exact
  vectors for the final top candidates to recover some of PQ's lost precision.
- **HNSW vs. IVF+PQ, operationally**: HNSW generally wins on recall and query
  latency when memory isn't the binding constraint. IVF+PQ wins when the
  dataset is too large to fit as a full-precision graph in available RAM — the
  classic scale-vs-accuracy fork in the road (this sets up next lesson's
  decision framework).

## Exercise

Using FAISS (`pip install faiss-cpu`), build both an `IndexHNSWFlat` and an
`IndexIVFPQ` over the same 100,000-vector synthetic dataset. Measure index
memory footprint (`faiss` indexes can be written to disk with `faiss.write_index`
— compare file sizes), query latency for 100 queries, and recall@10 against a
brute-force `IndexFlatL2` ground truth. Report which index you'd pick for a
10-million-vector dataset with a 2GB RAM budget, and why.
