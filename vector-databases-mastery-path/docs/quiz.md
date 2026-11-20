---
title: "Final Quiz"
description: "Quiz for the free Vector Databases Mastery Path: check what you learned across all four levels, with answers and explanations."
---

# Final Quiz

Ten questions drawn from all four levels of this course. You need **70% (7 out of 10)** to pass —
you can retake it as many times as you like. Your best result is saved in this browser.

<div id="mp-quiz-root"></div>

<script type="application/json" id="mp-quiz-data">
[
  {
    "level": 1,
    "topic": "Distance Metrics (Cosine, Euclidean, Dot Product)",
    "question": "Why does cosine similarity reduce to a plain dot product once both vectors are normalized to unit length?",
    "options": [
      "Normalization removes all information about direction, leaving only magnitude, which a dot product measures directly.",
      "Cosine similarity's formula divides the dot product by both vectors' magnitudes; if both magnitudes are exactly 1, that division becomes a no-op, leaving the raw dot product.",
      "Vector databases redefine 'dot product' internally to always mean cosine similarity, regardless of normalization.",
      "Normalized vectors can only be compared using Euclidean distance, not dot product, so databases default to dot product for unnormalized ones instead."
    ],
    "correctIndex": 1,
    "explanation": "Cosine similarity = (a\u00b7b)/(\u2016a\u2016\u2016b\u2016). When \u2016a\u2016=\u2016b\u2016=1, the denominator is 1, so the formula collapses to the plain dot product \u2014 letting a database normalize once at insert time and then use the cheapest possible operation for every future comparison."
  },
  {
    "level": 1,
    "topic": "Brute-Force Similarity Search",
    "question": "A dataset that takes about 5ms to brute-force search at 10,000 vectors would take roughly how long at 100,000,000 vectors, and why?",
    "options": [
      "Still about 5ms \u2014 modern CPUs parallelize vector math well enough that dataset size barely matters.",
      "Roughly 10,000x longer (tens of seconds), because brute-force search is O(n): doubling the dataset doubles the work, with no shortcuts.",
      "Roughly 100x longer, because vector databases automatically distribute brute-force search across available CPU cores in proportion to dataset size.",
      "Impossible to estimate without knowing the number of dimensions, since dimensionality \u2014 not dataset size \u2014 is what determines brute-force search time."
    ],
    "correctIndex": 1,
    "explanation": "Brute-force search compares the query against every stored vector, so its cost scales linearly (O(n)) with dataset size \u2014 a 10,000x larger dataset takes roughly 10,000x longer, which is exactly the wall that motivates trading a little accuracy for an ANN index's sublinear search time."
  },
  {
    "level": 1,
    "topic": "Metadata Filtering",
    "question": "In Chroma, when you call collection.query(query_texts=[...], where={'category': 'billing'}), what actually happens to documents that don't match the where filter?",
    "options": [
      "They're included in the similarity ranking first, then removed from the final results list before it's returned to you.",
      "They're excluded from candidates before similarity ranking happens, so vector similarity only ever ranks documents that already satisfy the filter.",
      "They lower the similarity score of every other document proportionally, to penalize the collection for containing off-topic data.",
      "Chroma ignores where filters when query_texts is also provided, applying them only to query_embeddings-based queries."
    ],
    "correctIndex": 1,
    "explanation": "The where filter narrows the candidate set before the vector similarity ranking runs \u2014 anything outside the filter never enters the ranking at all, rather than being computed and then discarded afterward."
  },
  {
    "level": 2,
    "topic": "How HNSW Actually Works",
    "question": "In an HNSW index, what does raising ef_search (e.g. Qdrant's hnsw_ef) actually change, and what's the cost?",
    "options": [
      "It rebuilds the graph with more connections per node, improving recall permanently at the cost of a slower index build.",
      "It widens the candidate list explored during each query's greedy search, improving recall at the cost of slower queries \u2014 with no index rebuild required.",
      "It increases the number of layers in the graph, giving queries more highway-like shortcuts to the right region.",
      "It controls how many vectors are stored per shard, trading memory for query throughput."
    ],
    "correctIndex": 1,
    "explanation": "ef_search is a query-time parameter: a larger candidate list means the greedy search considers more options before settling, improving recall at the cost of latency \u2014 unlike M or ef_construction, it requires no rebuild and is the main knob tuned live."
  },
  {
    "level": 2,
    "topic": "IVF & Product Quantization",
    "question": "In an IVF index, why does setting nprobe=1 (searching only the single nearest cluster) risk missing the true nearest neighbor, even though that cluster is the closest one to the query?",
    "options": [
      "IVF's k-means clustering step is randomized, so the 'nearest' cluster assignment is often wrong to begin with.",
      "A query can sit near a cluster boundary, with its true nearest neighbor just across that boundary in an adjacent, unsearched cluster.",
      "nprobe=1 disables product quantization entirely, so distances are computed incorrectly for all candidates.",
      "IVF only stores centroids, not actual vectors, so nprobe=1 can't retrieve real results at all \u2014 only centroid approximations."
    ],
    "correctIndex": 1,
    "explanation": "Cluster boundaries are drawn by k-means on the overall data distribution, not tailored to every individual query \u2014 a query near a boundary can have its genuinely closest vector sitting in the next cluster over, which nprobe=1 never looks at. This is why real deployments almost always use nprobe > 1."
  },
  {
    "level": 2,
    "topic": "Namespaces, Sharding & Multi-Tenancy",
    "question": "Why does a Pinecone query scoped to one namespace stay fast regardless of how many other namespaces share the same index, in a way that naive metadata-filter-based tenant isolation doesn't automatically guarantee?",
    "options": [
      "Namespaces are enforced as a hard boundary at the index level itself, so a query only ever touches that namespace's own data \u2014 it isn't implemented as a filter applied after searching everything.",
      "Pinecone automatically creates a separate physical server for every namespace behind the scenes.",
      "Namespaces compress vectors more aggressively than the default index, cutting query cost regardless of tenant count.",
      "Metadata filters and namespaces are actually the same mechanism in Pinecone, just with different names in the API."
    ],
    "correctIndex": 0,
    "explanation": "A namespace-scoped query is confined to that namespace's own data at the index level, so its cost doesn't grow with how many other namespaces exist \u2014 whereas naive metadata filtering can still involve touching a shared structure before the filter is applied, unless the database specifically optimizes for it."
  },
  {
    "level": 3,
    "topic": "Hybrid Search \u2014 Dense + Sparse (BM25)",
    "question": "When combining a dense (cosine similarity) ranked list and a sparse (BM25) ranked list, why does Reciprocal Rank Fusion combine them by rank position instead of just averaging their raw scores?",
    "options": [
      "BM25 and cosine similarity scores live on different, incomparable scales \u2014 rank position ('1st place') means the same thing regardless of which retriever produced it, while raw scores don't.",
      "Raw scores are computationally more expensive to combine than rank positions, so RRF trades a small amount of accuracy for speed.",
      "BM25 doesn't actually produce numeric scores, only a sorted order, so there's no score to combine with cosine similarity in the first place.",
      "Averaging scores would require retraining both the dense and sparse models jointly, which RRF avoids."
    ],
    "correctIndex": 0,
    "explanation": "BM25's scores are unbounded term-frequency weights and cosine similarity is bounded in [-1, 1] \u2014 you can't meaningfully add or average values on two different scales. Rank position is always comparable across retrievers, which is exactly what RRF exploits, with no per-dataset weight tuning required."
  },
  {
    "level": 3,
    "topic": "Re-ranking with Cross-Encoders",
    "question": "Why can a bi-encoder's document embeddings be precomputed and indexed for millions of documents, while a cross-encoder can't work that way at all?",
    "options": [
      "A bi-encoder produces smaller embeddings than a cross-encoder, so only bi-encoder output is small enough to store.",
      "A bi-encoder embeds the query and each document independently, so a document's embedding never depends on the query \u2014 a cross-encoder processes query and document together in one pass, so its output is specific to that one pair and can't be computed ahead of time.",
      "Cross-encoders are a newer architecture that hasn't yet been optimized for batch precomputation, but likely will be in future releases.",
      "Bi-encoders only work with short documents, which is what makes precomputing their embeddings practical at scale."
    ],
    "correctIndex": 1,
    "explanation": "A cross-encoder's score for a given document depends on the specific query it's paired with \u2014 concatenating them and running one joint forward pass \u2014 so there's no document-only representation to precompute. A bi-encoder's independence between query and document embedding is exactly what it sacrifices in accuracy for the ability to index ahead of time."
  },
  {
    "level": 4,
    "topic": "Emerging Trends \u2014 Matryoshka & Binary Quantization",
    "question": "Why can you truncate a Matryoshka-trained embedding from 768 to 128 dimensions and still get a usable result, when truncating an ordinarily-trained 768-dimension embedding the same way badly degrades quality?",
    "options": [
      "Matryoshka models store a separate, smaller model internally for every supported dimension, and truncation just selects which one to use.",
      "Ordinary embeddings are trained with the loss computed only on the full vector; Matryoshka training additionally computes the same contrastive loss at several shorter prefix lengths, forcing every prefix to be independently meaningful.",
      "Truncating any embedding works equally well; the 'Matryoshka' name just refers to how the vectors are packaged for storage, not to anything about training.",
      "Matryoshka embeddings are always stored pre-sorted by importance after training, regardless of model architecture, so any model's output can be truncated this way."
    ],
    "correctIndex": 1,
    "explanation": "Matryoshka training sums the contrastive loss at multiple truncation lengths (e.g. 768, 256, and 64 dimensions, all from the same vector) during training itself, forcing the model to front-load the most important information into the earliest dimensions \u2014 a property an ordinarily-trained model's output simply doesn't have."
  },
  {
    "level": 4,
    "topic": "Emerging Trends \u2014 Matryoshka & Binary Quantization",
    "question": "After binary-quantizing embeddings to 1 bit per dimension for a fast first-pass search, why is a second, full-precision re-ranking pass necessary rather than optional?",
    "options": [
      "Binary quantization is reversible, so the re-rank pass is just a formality to double-check the math, not to recover lost information.",
      "Collapsing every dimension to a single bit loses enough information that many genuinely different vectors end up with similar or identical bit patterns, meaningfully lowering recall versus full-precision search \u2014 the re-rank pass recovers most of that lost accuracy on a small shortlist.",
      "Hamming distance can only be computed on pairs of vectors from the same original collection, so a second pass is required to compare across collections.",
      "The first pass only returns cluster centroids, never real candidate vectors, so a second pass is required to fetch any actual results at all."
    ],
    "correctIndex": 1,
    "explanation": "1-bit-per-dimension resolution is coarse enough that distinct vectors can collapse to the same or very similar bit patterns, which measurably hurts recall versus full-precision comparison. Re-scoring only the shortlist (hundreds of candidates, not millions) with full-precision vectors recovers most of that accuracy cheaply, which is why production systems treat this second pass as required, not optional."
  }
]
</script>
