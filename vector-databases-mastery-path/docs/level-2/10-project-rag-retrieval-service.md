---
description: "A retrieval service that can't tell you which source a result came from isn't multi-source — it's two pipelines pretending to be one."
---

# 10 · Project — Multi-Source RAG Retrieval Service

This level's capstone: build a small web service that ingests documents from two
different source types, stores them with source-tracking metadata, and exposes
a search endpoint that queries across both — the retrieval half of a real RAG
(Retrieval-Augmented Generation) system.

## What you're building

A FastAPI service with two responsibilities:

1. **Ingestion**: pull content from (a) local `.txt` files and (b) a web page's
   text content, chunk and embed both, and upsert them into one Qdrant
   collection (or a pgvector table) with a `source_type` field (`"file"` or
   `"web"`) and a `source_ref` field (file path or URL).
2. **Retrieval**: a `/search` endpoint that takes a query string and an optional
   `source_type` filter, embeds the query, and returns the top-k matching chunks
   with their source metadata.

Example usage once built:

```bash
curl -X POST http://localhost:8000/ingest/file -d '{"path": "./docs/notes.txt"}'
curl -X POST http://localhost:8000/ingest/web -d '{"url": "https://example.com/article"}'

curl "http://localhost:8000/search?q=how+does+batching+work&source_type=file&top_k=3"
```

Example response shape:

```json
{
  "query": "how does batching work",
  "results": [
    {
      "text": "Batch requests amortize per-request overhead across many vectors...",
      "source_type": "file",
      "source_ref": "./docs/notes.txt",
      "score": 0.81
    }
  ]
}
```

## Suggested structure

```
rag_service/
├── main.py            # FastAPI app, routes
├── ingest.py          # chunk_text(), fetch_web_text(), process_source()
├── store.py           # Qdrant/pgvector client setup, upsert(), search()
└── models.py          # Pydantic request/response schemas
```

## Guided pieces

**Embedding and chunking** — reuse your Level 2 lesson 8 pipeline pattern
(`chunk_text`, deterministic IDs via `hashlib`, batch encode with
sentence-transformers) almost as-is; add a `source_type` and `source_ref` field
to each chunk's payload.

**Fetching web text** — a minimal approach using `requests` + a plain-text
extraction library:

```python
import requests
from bs4 import BeautifulSoup

def fetch_web_text(url: str) -> str:
    response = requests.get(url, timeout=10)
    soup = BeautifulSoup(response.text, "html.parser")
    for tag in soup(["script", "style", "nav", "footer"]):
        tag.decompose()
    return soup.get_text(separator="\n", strip=True)
```

(`pip install beautifulsoup4 requests`)

**The `/search` endpoint shape** (fill in the body yourself, using Qdrant's
`Filter`/`FieldCondition` from lesson 3 for the optional `source_type` filter):

```python
from fastapi import FastAPI, Query

app = FastAPI()

@app.get("/search")
def search(q: str, source_type: str | None = None, top_k: int = 5):
    # 1. embed q with sentence-transformers
    # 2. build a Qdrant Filter if source_type is provided
    # 3. call client.query_points(...) with the filter
    # 4. shape the response as {query, results: [...]}
    ...
```

## What's left to you

- The two `/ingest/*` route handlers that tie `ingest.py` to `store.py`.
- Deciding and implementing chunk size/overlap for web content (web pages
  often need different chunking than clean `.txt` files — think about headers,
  nav boilerplate, and whitespace noise you'll pick up from `get_text()`).
- Deduplication behavior if the same URL or file is ingested twice (apply
  lesson 8's deterministic-ID idempotency here).
- Error handling for a URL that fails to fetch or a file that doesn't exist —
  decide what the API should return.

## Exercise

Stand up the service, ingest at least 3 local files and 2 web pages, and run
five queries that should retrieve from the files and five that should retrieve
from the web pages (pick content accordingly). Verify with the `source_type`
filter that scoping to one source type actually excludes the other — the same
verification approach as lesson 3's filtering exercise, now applied end-to-end
through your own API instead of directly against the database client.
