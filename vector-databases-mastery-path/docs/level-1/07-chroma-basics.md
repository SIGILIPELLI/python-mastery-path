---
description: "Chroma can auto-embed your text for you via a built-in embedding function, so collection.add(documents=[...]) works with zero manual embedding calls."
---

# 07 · Your First Vector DB: Chroma

Everything so far has lived in plain Python lists and NumPy arrays. Time to
use an actual vector database — **Chroma**, a free, open-source, embedded
vector database that runs in-process (no server to stand up), making it the
easiest place to start.

## Install Chroma

```bash
pip install chromadb
```

## Create a persistent client

```python
import chromadb

client = chromadb.PersistentClient(path="./chroma_data")
```

`PersistentClient` writes to disk at the given path, so your data survives
between runs. (There's also `chromadb.Client()` for a purely in-memory
instance that disappears when the process exits — fine for quick
experiments, not for anything you want to keep.)

## Create a collection

A **collection** in Chroma is roughly the equivalent of a table — a named
group of vectors plus their metadata and original text.

```python
collection = client.get_or_create_collection(name="my_first_collection")
```

`get_or_create_collection` is idiomatic here — it creates the collection the
first time you run your script and reuses it on every subsequent run,
instead of erroring out on "already exists."

## Adding documents

Chroma can embed text for you automatically — pass `documents` (raw text)
and it uses a built-in default embedding model behind the scenes, no manual
`model.encode()` call required:

```python
collection.add(
    ids=["doc1", "doc2", "doc3", "doc4"],
    documents=[
        "The cat sat on the windowsill watching birds.",
        "Our server crashed during the deployment last night.",
        "She baked a chocolate cake for the party.",
        "The kitten chased a laser pointer across the floor.",
    ],
)
```

Chroma's default embedding function downloads a small sentence-transformers
model the first time you call `.add()` — similar to what you used directly
in Lesson 5.

### Using your own embeddings instead

If you'd rather control embedding generation yourself (e.g. to reuse the
exact model from Lesson 5, or a different one later in this course), pass
`embeddings` directly instead of letting Chroma compute them:

```python
from sentence_transformers import SentenceTransformer

model = SentenceTransformer("all-MiniLM-L6-v2")
texts = [
    "The cat sat on the windowsill watching birds.",
    "Our server crashed during the deployment last night.",
]
vectors = model.encode(texts).tolist()   # Chroma wants plain Python lists

collection.add(
    ids=["doc1", "doc2"],
    documents=texts,
    embeddings=vectors,
)
```

Either approach works — this course will mostly let Chroma auto-embed for
simplicity, and switch to manual embeddings when a lesson needs a specific
model.

## Querying

```python
results = collection.query(
    query_texts=["the website went down after we shipped new code"],
    n_results=2,
)

for doc, distance in zip(results["documents"][0], results["distances"][0]):
    print(f"{distance:.4f}  {doc}")
```

```text
0.6123  Our server crashed during the deployment last night.
1.1872  The cat sat on the windowsill watching birds.
```

Notice `query_texts` (not `query_embeddings`) — Chroma embeds your query
text with the same embedding function it used for `.add()`, so you never
have to manually embed a query when you're letting Chroma handle embedding.

## Putting it together

```python
import chromadb

client = chromadb.PersistentClient(path="./chroma_data")
collection = client.get_or_create_collection(name="my_first_collection")

if collection.count() == 0:
    collection.add(
        ids=["doc1", "doc2", "doc3", "doc4"],
        documents=[
            "The cat sat on the windowsill watching birds.",
            "Our server crashed during the deployment last night.",
            "She baked a chocolate cake for the party.",
            "The kitten chased a laser pointer across the floor.",
        ],
    )

results = collection.query(query_texts=["pets playing"], n_results=2)
print(results["documents"][0])
```

The `collection.count() == 0` check keeps this script idempotent — run it
twice and you won't get duplicate-ID errors from calling `.add()` again on
data that's already there.

## Exercise

Create a new persistent Chroma collection called `my_notes`. Add at least 6
documents of your own text (a mix of 2-3 clearly different topics). Write
three different queries — one that should clearly match each topic — and
print the top-2 results for each, confirming they come from the expected
topic group.
