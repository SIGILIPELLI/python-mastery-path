---
description: "A cross-encoder scores the query and document together in one forward pass, which is why it's slower but far more accurate than embedding similarity alone."
---

# 02 · Re-ranking with Cross-Encoders

## The two-stage pattern

Every retriever you've used so far — Chroma, Pinecone, Qdrant, pgvector — is
a **bi-encoder**: the query and each document are embedded *independently*,
then compared with cosine similarity or dot product. That's what makes them
fast — document embeddings are precomputed once, and a query only needs one
new embedding plus a nearest-neighbor lookup.

But independence has a cost: the model never sees the query and a specific
document *together*. It can't notice "this document mentions the right topic
but answers the opposite question" — it only sees two points in space and a
distance between them.

The fix used in nearly every production RAG and search system is a two-stage
pipeline:

1. **Retrieve** a wide net of candidates (say, top 50) cheaply with your
   existing bi-encoder vector search.
2. **Re-rank** those 50 with a slower, much more accurate **cross-encoder**
   that looks at the query and each document jointly, then keep only the
   top 5-10 for your LLM or user.

## Re-ranking with a cross-encoder

```bash
pip install sentence-transformers
```

```python
from sentence_transformers import CrossEncoder

reranker = CrossEncoder("cross-encoder/ms-marco-MiniLM-L-6-v2")

query = "What causes a connection reset error during a TLS handshake?"

candidates = [
    "Connection reset error ERR_CONN_RESET occurs when the TLS handshake times out before both sides agree on a cipher suite.",
    "To recover your account, reset your password from the login screen using the forgot-password link.",
    "SKU-48213-B is the replacement part for the model X200 fan assembly.",
    "TLS handshakes can fail due to clock skew, mismatched cipher suites, or an expired certificate.",
]

pairs = [[query, doc] for doc in candidates]
scores = reranker.predict(pairs)

ranked = sorted(zip(candidates, scores), key=lambda pair: -pair[1])
for doc, score in ranked:
    print(f"{score:.3f}  {doc[:70]}")
```

The two TLS-related documents (0 and 3) score far above the password-reset
and SKU documents — and crucially, the model can distinguish between "causes
a connection reset" (doc 0) and "handshake failures in general" (doc 3) in a
way plain embedding similarity often can't, because it reads them side by
side with the query rather than comparing two independently-computed points.

## Wiring it into a retrieval pipeline

```python
def search_and_rerank(query, collection, retrieve_k=50, final_k=5):
    # Stage 1: cheap, wide retrieval from your vector DB
    results = collection.query(query_texts=[query], n_results=retrieve_k)
    candidates = results["documents"][0]

    # Stage 2: precise, narrow re-ranking
    pairs = [[query, doc] for doc in candidates]
    scores = reranker.predict(pairs)

    ranked = sorted(zip(candidates, scores), key=lambda pair: -pair[1])
    return ranked[:final_k]
```

Note the shape: retrieve wide, rank narrow. If you retrieve only 5 candidates
from the vector DB and re-rank those 5, you've only reordered — you gain
nothing if the *actually* best document wasn't in the top 5 to begin with.
Retrieving 50-100 candidates before re-ranking is what gives the cross-encoder
room to rescue a document the bi-encoder under-ranked.

## How It Actually Works

1. **Bi-encoder architecture.** Two independent forward passes: `embed(query)`
   and `embed(document)`, each producing a fixed-size vector with no
   knowledge of the other input. Similarity is a cheap vector operation
   computed *after* both embeddings exist — this is why they can be
   precomputed and indexed for millions of documents.
2. **Cross-encoder architecture.** One forward pass: the query and document
   are concatenated (typically `[CLS] query [SEP] document [SEP]`) and fed
   through the transformer *together*. Every token of the query can attend
   to every token of the document, and vice versa, at every layer. The model
   outputs a single relevance score directly — there's no embedding to
   compare, no vector space at all.
3. **Why this makes cross-encoders slower.** Because the document
   representation depends on the specific query, nothing can be precomputed.
   Scoring N documents against a query means N full forward passes through
   the transformer, every single time. That's why cross-encoders re-rank
   tens of candidates, not millions.
4. **Why this makes cross-encoders more accurate.** Joint attention lets the
   model pick up on negation, specificity, and relational cues ("causes X"
   vs. "related to X in general") that two independently-pooled embeddings
   simply discard. In practice, cross-encoders consistently beat bi-encoders
   on reranking benchmarks like MS MARCO by a wide margin.
5. **The practical rule of thumb.** Retrieve ~10-20x more candidates than you
   actually need with the fast bi-encoder, then let the cross-encoder cut
   that down to your final result count. This gets you most of the accuracy
   of "score everything with a cross-encoder" at a tiny fraction of the
   latency cost.

## Exercise

Build on your Chroma collection from Level 1/2. Write `search_and_rerank`
as shown, retrieving `retrieve_k=30` candidates and re-ranking to `final_k=5`.
Pick a query where you suspect the bi-encoder's raw top-5 and the re-ranked
top-5 will differ, print both lists side by side, and note which documents
moved and why that makes sense given what a cross-encoder can see that a
bi-encoder can't.
