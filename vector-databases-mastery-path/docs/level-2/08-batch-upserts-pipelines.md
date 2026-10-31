---
description: "A deterministic ID derived from content (not an auto-increment counter) is what makes re-running an embedding pipeline safe instead of duplicating everything."
---

# 08 · Batch Upserts & Data Pipelines

Every lesson so far has upserted one or two vectors at a time for clarity. Real
pipelines embed and write thousands to millions of vectors, and doing that
one-at-a-time is slow and fragile. This lesson covers batching, idempotency, and
a reusable ETL shape.

## Why batching matters

A single upsert call has fixed per-request overhead (network round-trip, server-
side bookkeeping) on top of the actual write. Batch requests amortize that
overhead across many vectors:

```python
# Slow: one network round-trip per vector
for doc in docs:
    index.upsert(vectors=[build_vector(doc)])

# Fast: one round-trip per batch
BATCH_SIZE = 100
for i in range(0, len(docs), BATCH_SIZE):
    batch = docs[i:i + BATCH_SIZE]
    index.upsert(vectors=[build_vector(d) for d in batch])
```

Most databases document a recommended batch size (Pinecone suggests keeping
batches under ~2MB of payload; Qdrant and Weaviate have similar guidance) —
check before assuming bigger is always better, since oversized batches can hit
request size limits or timeout.

## Idempotent upserts via deterministic IDs

If you re-run an embedding pipeline (say, after fixing a bug in your chunking
logic), you want it to *overwrite* the old vectors for the same source content,
not create duplicates alongside them. The fix is to derive each vector's ID
deterministically from its source, instead of using an auto-incrementing counter
or a random UUID:

```python
import hashlib

def deterministic_id(source_path: str, chunk_index: int) -> str:
    raw = f"{source_path}::{chunk_index}"
    return hashlib.sha256(raw.encode()).hexdigest()[:24]
```

Running the pipeline twice over the same file now produces the same IDs both
times, so the second run's upserts cleanly replace the first run's vectors
instead of piling up duplicates. This matters enormously in practice — it's the
difference between a pipeline you can safely re-run and one you have to
carefully track state for externally.

## A simple ETL pipeline pattern

```python
from sentence_transformers import SentenceTransformer

model = SentenceTransformer("all-MiniLM-L6-v2")

def chunk_text(text: str, chunk_size: int = 500, overlap: int = 50) -> list[str]:
    chunks = []
    start = 0
    while start < len(text):
        chunks.append(text[start:start + chunk_size])
        start += chunk_size - overlap
    return chunks

def process_source(source_path: str, source_text: str) -> list[dict]:
    chunks = chunk_text(source_text)
    embeddings = model.encode(chunks)  # batch-encodes all chunks at once
    return [
        {
            "id": deterministic_id(source_path, i),
            "values": embeddings[i].tolist(),
            "metadata": {"source": source_path, "chunk_index": i, "text": chunks[i]},
        }
        for i in range(len(chunks))
    ]

def run_pipeline(sources: dict[str, str], index, batch_size: int = 100):
    all_vectors = []
    for path, text in sources.items():
        all_vectors.extend(process_source(path, text))

    for i in range(0, len(all_vectors), batch_size):
        batch = all_vectors[i:i + batch_size]
        index.upsert(vectors=batch)
```

Note `model.encode(chunks)` is called once per source on the *whole list* of
chunks, not once per chunk — sentence-transformers batches encoding internally
and is dramatically faster that way than calling `.encode()` in a loop.

## Handling partial batch failures

A batch of 100 can fail entirely (network error, rate limit) or partially
(some databases report per-item errors within a batch response). A simple and
robust retry strategy:

```python
import time

def upsert_with_retry(index, vectors: list[dict], max_retries: int = 3):
    for attempt in range(max_retries):
        try:
            index.upsert(vectors=vectors)
            return
        except Exception as e:
            if attempt == max_retries - 1:
                raise
            time.sleep(2 ** attempt)  # exponential backoff: 1s, 2s, 4s
```

Because upserts are idempotent (same deterministic ID → same result), retrying a
whole failed batch is always safe — you'll never end up with duplicates from a
retry, only from a genuinely new ID.

## Exercise

Extend the pipeline above to process a folder of `.txt` files (reuse your Level 1
project's input folder), write it to the vector database of your choice from
this level, then run the *exact same pipeline a second time with no changes to
the input files* and confirm via the database's item count (e.g. Qdrant's
collection info, or `index.describe_index_stats()` in Pinecone) that no
duplicate vectors were created.
