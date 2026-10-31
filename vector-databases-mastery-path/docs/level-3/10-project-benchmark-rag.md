---
description: "You don't know if hybrid search or re-ranking actually helped until you measure recall@k and p95 latency before and after on the same labeled eval set."
---

# 10 · Project — Benchmark & Optimize a RAG Pipeline

## The goal

Everything in this level is a tool for answering one question: *did my
change actually make retrieval better, and at what latency cost?* This
project makes you answer that question for real, on your own pipeline,
instead of taking it on faith that hybrid search or re-ranking "should"
help.

You'll take the retrieval service you built in Level 2 (or a similar
multi-document Chroma/Qdrant setup if you skipped straight here), build a
small labeled eval set, measure its baseline quality and speed, apply at
least two improvements from this level, and measure the delta.

## Step 1 — Build a labeled eval set

You need 20-50 `(query, relevant_doc_ids)` pairs, grounded in documents
that actually exist in your corpus. If you don't have real user queries to
draw from yet, write them yourself: pick a document, write a question that
document specifically and uniquely answers, record its ID as the answer.

```python
eval_set = [
    {"query": "...", "relevant_ids": {"doc_17"}},
    # ... 20-50 total, covering a mix of exact-term queries and paraphrased ones
]
```

Deliberately include a few queries that contain exact identifiers (error
codes, product names, specific numbers) — those are the ones hybrid search
is supposed to help with, and you want your eval set capable of showing
that.

## Step 2 — Measure the baseline

Reuse `recall_at_k` and `measure_latency` from lesson 5 against your
*current* pipeline (dense vector search only, no re-ranking, no caching):

```python
baseline_recall = recall_at_k(collection, eval_set, k=5)
baseline_latency = measure_latency(collection, [e["query"] for e in eval_set])

print("BASELINE")
print("recall@5:", baseline_recall)
print("latency:", baseline_latency)
```

Write these numbers down — literally save them to a file or print them
somewhere you won't lose. Everything after this step is measured relative
to this baseline.

## Step 3 — Apply at least two improvements

Pick at least two of the following (more is fine, but measure the effect of
each addition, not just the final combination, so you know what actually
contributed):

- **Hybrid search** (lesson 1): add BM25 + RRF fusion alongside your
  existing dense retrieval.
- **Re-ranking** (lesson 2): retrieve a wider candidate set and re-rank with
  a cross-encoder before returning the final top-k.
- **Better chunking** (lesson 3): re-chunk your corpus with a
  sentence-aware or semantic strategy if you're currently using naive
  fixed-size chunks, and re-index.
- **Caching** (lesson 6): add a semantic cache in front of search.
- **Index parameter tuning** (lesson 5): raise `ef_search`/`nprobe` and
  measure the recall/latency tradeoff directly.

A good combination to demonstrate the clearest story: **hybrid search +
re-ranking**, since the eval set's exact-term queries should show a visible
recall jump specifically attributable to adding BM25, and the re-ranking
step should show an improvement on the paraphrased queries — two different
mechanisms, two different parts of your eval set responding to each.

```python
def improved_search(query, collection, bm25, documents, top_k=5, retrieve_k=30):
    # Stage 1: hybrid retrieval (dense + sparse, fused with RRF)
    dense_ids = [doc_id for doc_id, _ in dense_search(query, top_k=retrieve_k)]
    sparse_ids = [doc_id for doc_id, _ in sparse_search(query, top_k=retrieve_k)]
    fused = rrf_fuse([dense_ids, sparse_ids])
    candidate_ids = [doc_id for doc_id, _ in fused[:retrieve_k]]
    candidates = [documents[i] for i in candidate_ids]

    # Stage 2: cross-encoder re-ranking down to the final top_k
    pairs = [[query, doc] for doc in candidates]
    scores = reranker.predict(pairs)
    ranked = sorted(zip(candidate_ids, candidates, scores), key=lambda t: -t[2])
    return ranked[:top_k]
```

## Step 4 — Measure the delta

Re-run the exact same `recall_at_k` and `measure_latency` measurements
against the improved pipeline, on the exact same eval set:

```python
improved_recall = recall_at_k_custom(improved_search, eval_set, k=5)  # adapt to your new function's signature
improved_latency = measure_latency_custom(improved_search, [e["query"] for e in eval_set])

print("IMPROVED")
print("recall@5:", improved_recall, " (baseline was", baseline_recall, ")")
print("latency:", improved_latency, " (baseline was", baseline_latency, ")")
```

Report both numbers honestly, including if latency got worse — re-ranking
in particular *will* add latency (an extra model forward pass per
candidate), and the real finding of this project is the tradeoff, not just
"recall went up."

## Step 5 — Break it down by query type

The most informative analysis isn't the aggregate recall number — it's
recall split by query type:

```python
exact_term_queries = [e for e in eval_set if looks_like_exact_term(e["query"])]
paraphrase_queries = [e for e in eval_set if not looks_like_exact_term(e["query"])]

print("exact-term recall, baseline vs improved:",
      recall_at_k(collection, exact_term_queries, k=5), "vs",
      recall_at_k_custom(improved_search, exact_term_queries, k=5))
```

This is where you should see the clearest story: hybrid search should move
the needle most on exact-term queries specifically, not uniformly across
everything — if your results don't show that pattern, it's worth
investigating why (a corpus too small to have real keyword-vs-paraphrase
distinction, or an eval set that doesn't actually stress that difference).

## Deliverable

A short write-up (a markdown file in your own notes, not part of this
course) with: your baseline numbers, which improvements you added, the
improved numbers, the recall/latency tradeoff you observed, and the
query-type breakdown. This is the exact kind of before/after evidence a real
team would want before shipping a retrieval change to production — which is
the actual skill this project is teaching.
