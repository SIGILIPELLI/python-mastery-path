---
description: "Dense embeddings miss exact keyword and ID matches that sparse BM25 catches instantly — hybrid search combines both with Reciprocal Rank Fusion."
---

# 01 · Hybrid Search — Dense + Sparse (BM25)

## Why dense search alone isn't enough

Dense embeddings are great at matching *meaning*. Ask for "how do I reset my
password" and a dense retriever will happily surface a document that says
"recovering account access" — no shared words, same intent.

But dense retrieval is surprisingly bad at exact matches: product SKUs, error
codes, rare proper nouns, part numbers, acronyms. A query like `ERR_CONN_RESET`
or `SKU-48213-B` often gets embedded into a vague "this looks like an error
code" region of space, and the one document that contains that *exact* string
can lose to five documents that are merely topically similar.

Classic keyword search (BM25) is the mirror image: perfect on exact terms,
useless on paraphrase. Hybrid search runs both and merges the results.

## BM25 in five lines

Install `rank_bm25`:

```bash
pip install rank_bm25
```

```python
from rank_bm25 import BM25Okapi

corpus = [
    "Connection reset error ERR_CONN_RESET occurs when the TLS handshake times out",
    "To recover your account, reset your password from the login screen",
    "SKU-48213-B is the replacement part for the model X200 fan assembly",
    "Semantic search uses dense vector embeddings to rank documents by meaning",
]

tokenized_corpus = [doc.lower().split() for doc in corpus]
bm25 = BM25Okapi(tokenized_corpus)

query = "ERR_CONN_RESET"
scores = bm25.get_scores(query.lower().split())
print(scores)
# doc 0 (the exact error code) scores far above the rest
```

BM25 scores each document by term frequency (how often query terms appear)
weighted by inverse document frequency (how rare those terms are across the
whole corpus) and normalized for document length. It has no notion of
meaning — `ERR_CONN_RESET` and `connection reset` are different tokens to it —
but it is unbeatable when the query contains the literal string you need.

## Running dense and sparse side by side

```python
from sentence_transformers import SentenceTransformer
import numpy as np

model = SentenceTransformer("all-MiniLM-L6-v2")
doc_embeddings = model.encode(corpus, normalize_embeddings=True)

def dense_search(query, top_k=4):
    q_emb = model.encode([query], normalize_embeddings=True)[0]
    sims = doc_embeddings @ q_emb
    ranked = np.argsort(-sims)
    return [(int(i), float(sims[i])) for i in ranked[:top_k]]

def sparse_search(query, top_k=4):
    scores = bm25.get_scores(query.lower().split())
    ranked = np.argsort(-scores)
    return [(int(i), float(scores[i])) for i in ranked[:top_k]]

query = "how do I recover my login"
print("dense :", dense_search(query))
print("sparse:", sparse_search(query))
```

For a paraphrased query like this, dense search ranks doc 1 (the password
reset doc) highly even though it shares almost no words with the query.
Sparse search, with no overlapping tokens beyond "my", ranks it poorly. That
asymmetry is exactly why you want both running at once.

## Combining results with Reciprocal Rank Fusion

You now have two ranked lists with incompatible scales — BM25 scores are
unbounded term-frequency weights, cosine similarity is bounded in `[-1, 1]`.
You can't just add them. **Reciprocal Rank Fusion (RRF)** sidesteps the scale
problem entirely by fusing on *rank position*, not raw score.

```python
def rrf_fuse(rankings: list[list[int]], k: int = 60) -> list[tuple[int, float]]:
    """rankings: list of ranked doc-id lists (best first), one per retriever."""
    scores: dict[int, float] = {}
    for ranking in rankings:
        for rank, doc_id in enumerate(ranking):
            scores[doc_id] = scores.get(doc_id, 0.0) + 1.0 / (k + rank + 1)
    return sorted(scores.items(), key=lambda pair: -pair[1])

dense_ids = [doc_id for doc_id, _ in dense_search(query, top_k=4)]
sparse_ids = [doc_id for doc_id, _ in sparse_search(query, top_k=4)]

fused = rrf_fuse([dense_ids, sparse_ids])
print(fused)
```

A document that ranks well in *either* list gets a meaningful score boost; a
document that ranks well in *both* rises to the top. No tuning of relative
weights required — that's the whole appeal of RRF over naive score averaging.

## How It Actually Works

1. **Why rank, not score.** Different retrievers produce scores on
   incomparable scales (and sometimes non-linear ones — BM25 scores for a
   2-word query and a 10-word query aren't directly comparable either). Rank
   position is always comparable: "1st place" means the same thing regardless
   of retriever.
2. **The formula.** For each retriever `r` and each document `d`, RRF
   contributes `1 / (k + rank_r(d) + 1)`. These contributions are summed
   across retrievers. A document absent from a retriever's list simply
   contributes 0 from that retriever.
3. **The constant `k`.** `k` (commonly 60) dampens the difference between
   adjacent ranks. Without it, rank 1 vs. rank 2 would differ by 50% (`1/1`
   vs `1/2`); with `k=60`, it's under 2% (`1/61` vs `1/62`). Larger `k` makes
   fusion more forgiving of a retriever getting the exact top spot wrong by
   one or two positions.
4. **Why it beats weighted score averaging in practice.** Picking weights
   for score averaging (e.g. `0.7 * dense + 0.3 * sparse`) requires tuning
   per-dataset and breaks when one retriever's score distribution shifts.
   RRF needs no such tuning and is remarkably robust across very different
   retrieval signals — it's the default fusion method in most production
   hybrid-search stacks (Elasticsearch, Vespa, Weaviate's hybrid mode).
5. **What it doesn't fix.** RRF assumes each retriever's *ranking* is
   individually decent. If one retriever's list is essentially random, RRF
   will still let its noise dilute the final ranking somewhat — it's a
   merging strategy, not a quality filter. That's what re-ranking (next
   lesson) is for.

## Exercise

Extend the corpus to 12-15 documents mixing exact identifiers (error codes,
SKUs, order numbers) with paraphrasable natural-language content. Write a
`hybrid_search(query, top_k)` function that runs `dense_search` and
`sparse_search` over the full corpus, fuses with `rrf_fuse`, and returns the
top-k fused results. Try three queries — one that's pure keyword, one that's
pure paraphrase, one that's a mix — and confirm hybrid search beats *both*
individual retrievers on the mixed query.
