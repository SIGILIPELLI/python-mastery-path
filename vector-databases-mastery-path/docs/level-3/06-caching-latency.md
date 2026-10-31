---
description: "A semantic cache matches queries by meaning instead of exact text, so paraphrased repeat questions still hit the cache instead of re-running a full search."
---

# 06 · Caching & Latency Optimization

## What's worth caching in a RAG pipeline

A typical query touches several expensive steps: embed the query (a model
forward pass), search the vector DB (an ANN traversal), sometimes re-rank
(another model forward pass), and often call an LLM with the retrieved
context (the most expensive step of all). Caching at any of these layers
avoids redoing work that's likely to repeat — and in most real traffic,
query repetition is much higher than people expect (common questions, retry
clicks, near-duplicate phrasing).

## Exact-match query caching

The simplest cache: hash the normalized query text and cache the full
result.

```python
import hashlib
import json

class ExactQueryCache:
    def __init__(self):
        self._store = {}

    def _key(self, query: str) -> str:
        normalized = query.strip().lower()
        return hashlib.sha256(normalized.encode()).hexdigest()

    def get(self, query: str):
        return self._store.get(self._key(query))

    def set(self, query: str, result):
        self._store[self._key(query)] = result

cache = ExactQueryCache()

def cached_search(collection, query, n_results=5):
    if hit := cache.get(query):
        return hit
    result = collection.query(query_texts=[query], n_results=n_results)
    cache.set(query, result)
    return result
```

For production, back this with Redis (`SETEX` with a TTL) instead of an
in-memory dict, so the cache survives restarts and is shared across
multiple app instances:

```python
import redis
import json

r = redis.Redis(host="localhost", port=6379)

def cached_search_redis(collection, query, n_results=5, ttl_seconds=3600):
    key = "qcache:" + hashlib.sha256(query.strip().lower().encode()).hexdigest()
    if cached := r.get(key):
        return json.loads(cached)
    result = collection.query(query_texts=[query], n_results=n_results)
    r.setex(key, ttl_seconds, json.dumps(result))
    return result
```

Exact-match caching catches identical repeat queries but misses the far more
common case: the *same intent*, worded slightly differently ("reset my
password" vs. "how do I reset my password" vs. "password reset steps").

## Semantic caching

A semantic cache stores past queries' *embeddings* alongside their results,
and on a new query, checks whether any cached query is similar enough (above
a similarity threshold) to reuse.

```python
import numpy as np

class SemanticCache:
    def __init__(self, model, threshold: float = 0.95):
        self.model = model
        self.threshold = threshold
        self.entries = []  # list of (embedding, query_text, result)

    def get(self, query: str):
        if not self.entries:
            return None
        q_emb = self.model.encode([query], normalize_embeddings=True)[0]
        sims = [float(q_emb @ e[0]) for e in self.entries]
        best_idx = int(np.argmax(sims))
        if sims[best_idx] >= self.threshold:
            return self.entries[best_idx][2]
        return None

    def set(self, query: str, result):
        q_emb = self.model.encode([query], normalize_embeddings=True)[0]
        self.entries.append((q_emb, query, result))

semantic_cache = SemanticCache(model, threshold=0.95)

def cached_search_semantic(collection, query, n_results=5):
    if hit := semantic_cache.get(query):
        return hit
    result = collection.query(query_texts=[query], n_results=n_results)
    semantic_cache.set(query, result)
    return result
```

The threshold matters a lot: too low (e.g. 0.80) and you'll serve a cached
answer for a genuinely different question; too high (e.g. 0.99) and you'll
rarely get a cache hit at all. 0.92-0.97 is a common practical range for
`all-MiniLM-L6-v2`-style models, but always tune it against your own eval
set rather than trusting a default — "close enough" is domain-specific.

Note the cost tradeoff: a semantic cache check *itself* requires computing
the query embedding, so it only pays off when it saves something more
expensive than that (the vector DB search, re-ranking, or an LLM call) — it
isn't free, it's cheaper-than-the-alternative.

## Embedding caching

If the same piece of text gets embedded repeatedly — common with chunk
re-indexing jobs, or user-facing autocomplete that re-embeds partial
queries — cache the embedding itself, keyed by the exact text:

```python
from functools import lru_cache

@lru_cache(maxsize=10_000)
def embed_cached(text: str) -> tuple:
    return tuple(model.encode([text], normalize_embeddings=True)[0])
```

`lru_cache` is process-local and fine for a single service instance; for
multi-instance deployments, the same Redis pattern as above works —
`embcache:<sha256 of text>` → the embedding bytes.

## Connection pooling and batching

Two more latency wins that aren't about caching at all:

- **Connection pooling.** Opening a new connection to a hosted vector DB
  (Pinecone, Qdrant Cloud) per request adds TCP/TLS handshake overhead on
  every call. Reuse a client instance across requests instead of
  constructing one per query — most client SDKs pool connections
  automatically if you reuse the client object.
- **Batching.** If your application needs to embed or query many items at
  once (e.g. re-indexing, or a bulk recommendation job), batch them into one
  `encode()`/`query()` call instead of looping one at a time. A model
  forward pass over a batch of 32 is dramatically faster per-item than 32
  separate forward passes, because it better utilizes the hardware (CPU
  vectorization or GPU parallelism) in one shot.

```python
# Slow: one embedding call per text
embeddings = [model.encode([t])[0] for t in texts]

# Fast: one batched call for all texts
embeddings = model.encode(texts, batch_size=32)
```

## Exercise

Add a semantic cache in front of your search function from earlier levels.
Run a batch of 20 queries where some are near-paraphrases of each other
(e.g. "how do I reset my password" and "steps to recover my account login").
Measure the cache hit rate at threshold 0.90 vs 0.97, and check whether any
hits at the lower threshold returned results for a genuinely different
question — that's your signal for where the threshold needs to sit for your
own data.
