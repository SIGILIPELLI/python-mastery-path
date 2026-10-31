---
description: "Recall drift — your retriever quietly getting worse as your corpus grows or your users' phrasing shifts — is invisible unless you log and re-measure it on a schedule."
---

# 07 · Monitoring & Observability for Vector Search

## What breaks silently in production

A vector search system doesn't throw errors when it's returning mediocre
results — it just... returns mediocre results. Unlike a crashed API call,
degraded retrieval quality produces no exception, no 500 status code,
nothing in your error logs. You find out from a frustrated user, or you
don't find out at all. Observability here means deliberately watching
things that don't announce themselves.

## What to monitor

- **Query latency** (p50/p95/p99, per the previous lesson) — watch for
  gradual creep as your index grows, not just hard failures.
- **Error rates** — timeouts, connection failures, malformed queries (empty
  strings, queries exceeding a model's max token length).
- **Index size and memory** — HNSW graphs and IVF indexes grow with your
  corpus; watch memory usage so you catch an approaching capacity ceiling
  before it causes an outage, not after.
- **Recall drift** — the quality metric from lesson 5, measured *repeatedly
  over time*, not just once at launch. A corpus that grows, an embedding
  model that gets silently upgraded by a hosted API, or a shift in the kind
  of questions users ask can all erode recall without any infrastructure
  alarm going off.
- **Zero-result and low-confidence-result rates** — queries where the top
  result's similarity score is below a sane threshold are a proxy for "the
  system had nothing good to say," worth tracking as its own rate over time.

## Structured logging for offline analysis

Log every query with enough structure to analyze later — not just
`"query succeeded"`, but what was asked, what came back, and how confident
the system was:

```python
import logging
import json
import time

logger = logging.getLogger("vector_search")

def logged_search(collection, query, n_results=5):
    start = time.perf_counter()
    result = collection.query(query_texts=[query], n_results=n_results)
    latency_ms = (time.perf_counter() - start) * 1000

    distances = result.get("distances", [[]])[0]
    log_entry = {
        "query": query,
        "n_results": n_results,
        "returned_ids": result["ids"][0],
        "top_distance": distances[0] if distances else None,
        "latency_ms": round(latency_ms, 2),
        "timestamp": time.time(),
    }
    logger.info(json.dumps(log_entry))
    return result
```

Structured (JSON) logs like this can be shipped to any log aggregation
system (Elasticsearch, Datadog, CloudWatch Logs Insights) and queried later:
"show me all queries from the last week with `top_distance` below 0.3" is
exactly the kind of offline analysis that catches a retrieval quality
problem your dashboards never surfaced as an alert.

## Metrics instrumentation with Prometheus

Logs are good for forensic analysis of individual queries; metrics are good
for dashboards and alerting on aggregate trends.

```bash
pip install prometheus-client
```

```python
from prometheus_client import Histogram, Counter, start_http_server

SEARCH_LATENCY = Histogram(
    "vector_search_latency_seconds",
    "Time spent on vector search queries",
    buckets=[0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0],
)
SEARCH_ERRORS = Counter("vector_search_errors_total", "Failed vector search queries")
LOW_CONFIDENCE_RESULTS = Counter(
    "vector_search_low_confidence_total",
    "Queries whose top result fell below the confidence threshold",
)

def instrumented_search(collection, query, n_results=5, confidence_threshold=0.3):
    with SEARCH_LATENCY.time():
        try:
            result = collection.query(query_texts=[query], n_results=n_results)
        except Exception:
            SEARCH_ERRORS.inc()
            raise

    distances = result.get("distances", [[]])[0]
    if distances and distances[0] > confidence_threshold:
        LOW_CONFIDENCE_RESULTS.inc()
    return result

start_http_server(8000)  # Prometheus scrapes metrics from :8000/metrics
```

With this running, a Grafana dashboard can plot p95 latency, error rate, and
the low-confidence-result rate over time — and you can alert when any of
them crosses a threshold, turning "silent degradation" into "a page at
2am," which, perhaps counterintuitively, is exactly the improvement you want.

## Scheduled recall re-measurement

The single most important observability practice for retrieval quality
specifically: **don't just measure recall@k once at launch — re-run your
eval set on a schedule** (nightly, or on every deploy) and track the trend.

```python
# A simple scheduled job (run via cron, Airflow, or a CI pipeline)
def nightly_recall_check(collection, eval_set, alert_threshold=0.85):
    score = recall_at_k(collection, eval_set, k=5)  # from lesson 5
    logger.info(json.dumps({"metric": "nightly_recall_at_5", "value": score, "timestamp": time.time()}))
    if score < alert_threshold:
        # page someone, post to Slack, whatever your alerting path is
        raise RuntimeError(f"Recall@5 dropped to {score:.3f}, below threshold {alert_threshold}")
```

This is the only reliable way to catch the scenario from the top of this
lesson: a corpus growing in a way that dilutes relevance, or an upstream
embedding API quietly changing, before a human notices the symptoms.

## Exercise

Add Prometheus instrumentation (`SEARCH_LATENCY`, `SEARCH_ERRORS`,
`LOW_CONFIDENCE_RESULTS`) to your search function from earlier lessons. Run
50 varied queries through it, including a few you expect to have no good
answer in your corpus, and inspect `/metrics` to confirm the histogram and
counters populated as expected. Then write the `nightly_recall_check`
function against your eval set from lesson 5 and confirm it raises when you
artificially lower the threshold above your current score.
