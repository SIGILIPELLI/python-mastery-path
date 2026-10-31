---
description: "Weaviate's hybrid search blends BM25 keyword scores with vector similarity using a single alpha knob — alpha=0 is pure keyword, alpha=1 is pure vector."
---

# 02 · Weaviate: Schemas & Hybrid Search

Weaviate is a vector database with a schema-first design: you define collections
with typed properties up front, and it can generate embeddings for you or accept
your own. Its standout feature is hybrid search done natively, not bolted on.

## Setup

```bash
pip install weaviate-client
```

Run locally with Docker for this lesson:

```bash
docker run -d -p 8080:8080 -p 50051:50051 \
  cr.weaviate.io/semitechnologies/weaviate:1.25.0
```

```python
import weaviate

client = weaviate.connect_to_local()
```

## Defining a collection schema

```python
import weaviate.classes as wvc

client.collections.create(
    name="Article",
    properties=[
        wvc.config.Property(name="title", data_type=wvc.config.DataType.TEXT),
        wvc.config.Property(name="body", data_type=wvc.config.DataType.TEXT),
        wvc.config.Property(name="category", data_type=wvc.config.DataType.TEXT),
    ],
    vectorizer_config=wvc.config.Configure.Vectorizer.none(),
)
```

Unlike Chroma or Pinecone (which treat metadata as a loose dict), Weaviate wants a
declared schema with types — closer to a database table than a free-form document
store. This gives you type-checking on filters at query time.

## Bring-your-own-vectors vs. built-in vectorization

With `Vectorizer.none()` above, you supply vectors yourself (e.g. from
sentence-transformers). Weaviate also supports built-in vectorizer modules
(OpenAI, Cohere, HuggingFace) that embed text for you on insert — convenient, but
it means Weaviate's server needs network access to that embedding provider.
This lesson uses bring-your-own-vectors to keep things explicit and provider-agnostic.

```python
from sentence_transformers import SentenceTransformer

model = SentenceTransformer("all-MiniLM-L6-v2")
articles = client.collections.get("Article")

text = "Hybrid search blends keyword and semantic signals."
articles.data.insert(
    properties={"title": "Hybrid Search 101", "body": text, "category": "search"},
    vector=model.encode(text).tolist(),
)
```

## Hybrid search with `alpha`

```python
query_vector = model.encode("how do you combine keyword and vector search").tolist()

response = articles.query.hybrid(
    query="combine keyword and vector search",
    vector=query_vector,
    alpha=0.5,
    limit=5,
)

for obj in response.objects:
    print(obj.properties["title"])
```

`alpha` is the blend weight between the two scoring methods:

- `alpha=0.0` — pure BM25 keyword search (exact term matching, classic full-text search)
- `alpha=1.0` — pure vector similarity (semantic, ignores exact wording)
- `alpha=0.5` — an even blend; a common starting point

Weaviate runs both searches, normalizes each score to `[0, 1]`, and combines them
as `alpha * vector_score + (1 - alpha) * keyword_score` (the actual fusion algorithm
—`relativeScoreFusion` or `rankedFusion`— is configurable, but this is the mental
model). The practical reason hybrid matters: pure vector search can miss an exact
product code, acronym, or proper noun that a user typed verbatim, because
embeddings represent meaning, not exact tokens. Keyword search catches that; vector
search catches paraphrases and synonyms that keyword search misses.

## Exercise

Insert the same 10 documents you used in your Level 1 CLI project into a Weaviate
`Article` collection, with real embeddings. Run the same query three times with
`alpha=0`, `alpha=0.5`, and `alpha=1`, and compare the top-3 results at each
setting. Find (or construct) one document title that contains an exact keyword
your query uses but is semantically unrelated, and show how `alpha` shifts whether
it ranks highly.
