---
description: "Recall@k tells you if your retriever finds the right documents at all; p95/p99 latency tells you if it does it fast enough under real concurrent load."
---

# 05 · Benchmarking & Performance Tuning

## Two different questions

"Is my vector search good?" is actually two separate questions that need
separate measurements:

1. **Quality** — does it return the right documents? (recall@k)
2. **Speed** — how fast does it return them, especially under load?
   (latency percentiles)

Tuning one often costs you the other — that's the whole reason to measure
both before touching any settings.

## Measuring recall@k against ground truth

You need a small labeled eval set: a list of `(query, relevant_doc_ids)`
pairs where you (or domain experts) have manually decided what *should* come
back.

```python
eval_set = [
    {"query": "how does TLS handshake failure happen", "relevant_ids": {"doc_17", "doc_42"}},
    {"query": "password recovery steps", "relevant_ids": {"doc_3"}},
    # ... 30-100 labeled examples, more is better
]

def recall_at_k(collection, eval_set, k=5):
    hits = 0
    for example in eval_set:
        results = collection.query(query_texts=[example["query"]], n_results=k)
        returned_ids = set(results["ids"][0])
        if returned_ids & example["relevant_ids"]:
            hits += 1
    return hits / len(eval_set)

print("recall@5:", recall_at_k(collection, eval_set, k=5))
```

This version counts a query as a "hit" if *any* relevant document appears in
the top-k — useful when one correct answer is enough. For queries with
multiple relevant documents, you'll often also want a stricter metric:

```python
def mean_recall_fraction_at_k(collection, eval_set, k=5):
    total = 0.0
    for example in eval_set:
        results = collection.query(query_texts=[example["query"]], n_results=k)
        returned_ids = set(results["ids"][0])
        relevant = example["relevant_ids"]
        total += len(returned_ids & relevant) / len(relevant)
    return total / len(eval_set)
```

This measures *what fraction* of all relevant documents you retrieved, not
just whether you got at least one — important when a query genuinely has 3
correct documents and you only want credit for finding all of them.

## Measuring latency percentiles

Average latency hides the problem. If 99 queries take 10ms and 1 query takes
2 seconds, your average looks fine (~30ms) but one in a hundred users has a
terrible experience. Percentiles expose this:

```python
import time
import numpy as np

def measure_latency(collection, queries, n_results=5):
    timings = []
    for query in queries:
        start = time.perf_counter()
        collection.query(query_texts=[query], n_results=n_results)
        timings.append((time.perf_counter() - start) * 1000)  # ms

    timings = np.array(timings)
    return {
        "p50": float(np.percentile(timings, 50)),
        "p95": float(np.percentile(timings, 95)),
        "p99": float(np.percentile(timings, 99)),
        "max": float(timings.max()),
    }

print(measure_latency(collection, [e["query"] for e in eval_set] * 10))
```

**p50** (median) tells you the typical experience. **p95/p99** tell you the
experience your worst-off users actually have — the numbers that matter for
an SLA, because "average" latency is not what any individual slow request
feels like.

## Load testing with concurrency

Single-threaded timing understates real-world latency, because production
traffic is concurrent and a vector DB's index has shared resources (memory
bandwidth, lock contention) that degrade under parallel load.

```python
import concurrent.futures
import time

def load_test(collection, queries, concurrency=20, total_requests=200):
    def one_query(q):
        start = time.perf_counter()
        collection.query(query_texts=[q], n_results=5)
        return (time.perf_counter() - start) * 1000

    with concurrent.futures.ThreadPoolExecutor(max_workers=concurrency) as pool:
        work = [queries[i % len(queries)] for i in range(total_requests)]
        timings = list(pool.map(one_query, work))

    import numpy as np
    arr = np.array(timings)
    return {"p50": np.percentile(arr, 50), "p95": np.percentile(arr, 95), "p99": np.percentile(arr, 99)}

print(load_test(collection, [e["query"] for e in eval_set], concurrency=20, total_requests=200))
```

For a heavier, more realistic load test against an HTTP-based vector DB
(Pinecone, Qdrant, Weaviate over their REST/gRPC APIs), a dedicated tool like
`locust` lets you ramp concurrent users gradually and watch latency degrade
as load increases, which a simple thread pool script won't show you as
clearly.

## Tuning the recall/latency tradeoff

Most ANN indexes expose a runtime parameter that trades recall for latency
directly:

- **HNSW**: `ef_search` (sometimes called `ef` at query time) — how many
  candidate nodes to examine per layer during the graph traversal. Higher
  `ef_search` = better recall, higher latency.
- **IVF**: `nprobe` — how many of the index's cluster partitions to search.
  Higher `nprobe` = better recall, higher latency, same idea as `ef_search`.

```python
# Qdrant example: raising ef_search at query time
client.query_points(
    collection_name="docs",
    query=query_vector,
    search_params={"hnsw_ef": 256},  # default is often 128; higher = more recall, slower
    limit=5,
)
```

The right value is whatever satisfies your latency budget while keeping
recall@k above your quality bar on your eval set — there's no universally
correct number, which is exactly why you benchmark both together rather than
guessing one in isolation.

## Exercise

Build a 20-example eval set for your Chroma/Qdrant collection from earlier
levels. Measure recall@5 and p50/p95/p99 latency at the index's default
settings. Then raise the recall/latency tradeoff parameter (`ef_search` or
equivalent) and re-measure both. Plot or tabulate how recall and p95 latency
move together as you increase it — find the point of diminishing returns
where more latency stops buying meaningfully better recall.
