---
description: "A vector DB that 'feels fast' and one that actually retrieves the right chunks are different claims — Recall@K, MRR, and NDCG are how you tell them apart."
---

# 02 · Evaluating Retrieval Quality (Recall@K, MRR, NDCG)

Every lesson so far has assumed retrieval works. It doesn't, automatically —
chunking choices, embedding model choices, and index settings all change
what comes back, often in ways that feel fine in a demo and fail silently in
production. This lesson gives you the metrics to measure retrieval quality
instead of eyeballing it, and a labeled eval set to measure it against.

## Building a labeled eval set

Before any metric means anything, you need **queries with known-correct
answers**: for each query, which chunk ID(s) in your corpus should ideally
come back.

```python
eval_set = [
    {
        "query": "How do I reset a user's password via the admin API?",
        "relevant_chunk_ids": {"docs/admin-api.md#chunk-12"},
    },
    {
        "query": "What's the rate limit for the search endpoint?",
        "relevant_chunk_ids": {"docs/api-limits.md#chunk-3", "docs/api-limits.md#chunk-4"},
    },
    # 20-50 of these is a reasonable starting eval set
]
```

Label these by hand (or have domain experts label them) — this is the
single highest-leverage thing you can do for retrieval quality, because
every metric below is only as good as this ground truth.

## Recall@K

**Recall@K** asks: of all the relevant chunks that exist, what fraction did
we get back in our top K results?

$$\text{Recall@K} = \frac{|\text{relevant} \cap \text{retrieved top-K}|}{|\text{relevant}|}$$

```python
def recall_at_k(retrieved_ids: list[str], relevant_ids: set[str], k: int) -> float:
    top_k = set(retrieved_ids[:k])
    if not relevant_ids:
        return 0.0
    return len(top_k & relevant_ids) / len(relevant_ids)

retrieved = ["c3", "c12", "c7", "c4", "c9"]
relevant = {"c12", "c4"}
print(recall_at_k(retrieved, relevant, k=5))  # 1.0 — both relevant chunks are in top 5
print(recall_at_k(retrieved, relevant, k=2))  # 0.5 — only c12 is in top 2
```

Recall@K is the right metric when you care about *completeness* — e.g. a
RAG system that needs every relevant chunk to answer a question fully, not
just one.

## Mean Reciprocal Rank (MRR)

**MRR** cares about how early the *first* relevant result appears, averaged
across queries. It's the right metric when one good result is enough (e.g.
"find the doc that answers this").

$$\text{RR} = \frac{1}{\text{rank of first relevant result}} \qquad \text{MRR} = \frac{1}{|Q|}\sum_{q \in Q} \text{RR}_q$$

```python
def reciprocal_rank(retrieved_ids: list[str], relevant_ids: set[str]) -> float:
    for i, doc_id in enumerate(retrieved_ids, start=1):
        if doc_id in relevant_ids:
            return 1.0 / i
    return 0.0

def mrr(all_retrieved: list[list[str]], all_relevant: list[set[str]]) -> float:
    scores = [reciprocal_rank(r, rel) for r, rel in zip(all_retrieved, all_relevant)]
    return sum(scores) / len(scores)

# Worked example: first relevant chunk at rank 1, 3, and 2 across three queries
example_rrs = [1/1, 1/3, 1/2]
print(sum(example_rrs) / len(example_rrs))  # MRR = 0.611
```

A system that always puts the right answer first scores MRR = 1.0. One that
puts it third on average scores MRR ≈ 0.33.

## NDCG (Normalized Discounted Cumulative Gain)

**NDCG** handles *graded* relevance (not just relevant/irrelevant, but "this
chunk is a perfect match," "this one is tangentially related") and rewards
putting the best results earliest, with a logarithmic rank discount.

$$\text{DCG@K} = \sum_{i=1}^{K} \frac{2^{\text{rel}_i} - 1}{\log_2(i + 1)} \qquad \text{NDCG@K} = \frac{\text{DCG@K}}{\text{IDCG@K}}$$

where IDCG is the DCG of the *ideal* ordering (relevance scores sorted
descending).

```python
import math

def dcg_at_k(relevance_scores: list[int], k: int) -> float:
    return sum(
        (2**rel - 1) / math.log2(i + 2)
        for i, rel in enumerate(relevance_scores[:k])
    )

def ndcg_at_k(relevance_scores: list[int], k: int) -> float:
    ideal = sorted(relevance_scores, reverse=True)
    idcg = dcg_at_k(ideal, k)
    if idcg == 0:
        return 0.0
    return dcg_at_k(relevance_scores, k) / idcg

# Worked example: retrieved results have relevance grades 3, 0, 1, 2, 0
# (3 = perfect match, 0 = irrelevant)
scores = [3, 0, 1, 2, 0]
print(ndcg_at_k(scores, k=5))  # 0.869 — close to ideal, but the rank-2 miss costs us
print(ndcg_at_k(sorted(scores, reverse=True), k=5))  # 1.0 — ideal ordering by definition
```

## Which metric to use when

- **Recall@K** — you need *all* the relevant information (summarization,
  multi-fact answers, compliance-sensitive retrieval where missing a
  relevant doc is a real cost).
- **MRR** — one good hit is enough and you care about *how fast* the user
  (or the LLM) finds it (FAQ search, "find me the doc").
- **NDCG** — you have graded relevance judgments and care about the overall
  quality of the ranking, not just a binary hit/miss (search result pages,
  recommendation).

In practice, run all three against your labeled eval set whenever you
change chunking, the embedding model, or index parameters (`ef_search`,
`nprobe`, re-ranking) from earlier lessons — a change that looks neutral on
one metric can be a regression on another, and only measuring tells you
which.

## How It Actually Works

1. **Why NDCG uses $2^{\text{rel}} - 1$ instead of just `rel`.** The
   exponential gain function means a relevance-3 result is worth
   disproportionately more than three relevance-1 results — it models the
   intuition that one perfect answer beats several mediocre ones, which a
   linear scale would not capture.
2. **Why the log discount, not a linear one.** $\log_2(i+1)$ penalizes rank 2
   vs. rank 1 much more harshly (in relative terms) than it penalizes rank 20
   vs. rank 19 — matching the real-world fact that users (and LLMs reading a
   limited context window) care enormously about the very top results and
   decreasingly about results far down the list.
3. **Why you normalize against the *ideal* DCG, not a fixed maximum.** Two
   queries with different relevance-score distributions (one has five
   perfect matches available, another has only one) aren't directly
   comparable on raw DCG. Dividing by IDCG — the best possible DCG for that
   query's own ground truth — rescales every query to the same 0-1 range,
   so you can average NDCG across queries meaningfully.
4. **Why Recall@K can look great while users are unhappy.** Recall@K only
   measures whether relevant chunks are *somewhere* in the top K — a system
   that recalls everything but buries the best chunk at rank 9 looks perfect
   on Recall@10 while being a poor experience if only the first 3 chunks fit
   in context. This is exactly the blind spot MRR and NDCG are built to
   catch, which is why production evals almost always report more than one
   metric side by side.

## Exercise

Build a 15-query labeled eval set against your own corpus from earlier
lessons (binary relevant/irrelevant labels are fine to start). Run your
current retrieval pipeline against it and compute Recall@5, MRR, and
NDCG@5. Then make one deliberate change — reduce your chunk size by half, or
switch to a smaller embedding model — and re-run the eval. Report which
metric moved the most and whether that matches your intuition about what
the change would do.
