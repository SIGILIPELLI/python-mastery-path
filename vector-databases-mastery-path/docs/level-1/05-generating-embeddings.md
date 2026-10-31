---
description: "sentence-transformers' all-MiniLM-L6-v2 model turns any sentence into a 384-number vector on your own CPU in milliseconds, with no API key and no network call."
---

# 05 · Generating Real Embeddings

So far every vector has been hand-crafted. Time to generate real ones from
real text using a real, open-source embedding model.

## Install sentence-transformers

```bash
pip install sentence-transformers
```

This pulls in PyTorch and Hugging Face's `transformers` library under the
hood — the first import may take a few seconds while it loads.

## Load a model and encode a sentence

```python
from sentence_transformers import SentenceTransformer

model = SentenceTransformer("all-MiniLM-L6-v2")

embedding = model.encode("My laptop won't turn on")
print(embedding.shape)   # (384,)
print(embedding[:5])     # first 5 of 384 numbers
```

The first call downloads the model (~90MB) from Hugging Face and caches it
locally (`~/.cache/huggingface` by default) — subsequent runs load instantly
from disk, no network required.

`all-MiniLM-L6-v2` is a good default for this course: small (fast on CPU,
no GPU needed), well-tested, and produces 384-dimensional embeddings that
are normalized to work well with cosine similarity.

## Encoding many sentences at once

```python
sentences = [
    "My laptop won't turn on",
    "Device fails to power up",
    "Apple released a new phone",
    "Apple pie recipe with cinnamon",
]

embeddings = model.encode(sentences)
print(embeddings.shape)   # (4, 384) — 4 sentences, 384 dims each
```

Batching like this (passing a list instead of calling `.encode()` in a loop)
is significantly faster — the model processes all sentences together.

## Revisiting Lesson 1's prediction with real numbers

Lesson 1 predicted that "my laptop won't turn on" and "device fails to
power up" would land close together despite sharing no words, while "apple
released a new phone" and "apple pie recipe" would land far apart despite
sharing a word. Now you can check that with a real model:

```python
import numpy as np

def cosine_similarity(a, b):
    return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))

laptop_vec = embeddings[0]
device_vec = embeddings[1]
iphone_vec = embeddings[2]
pie_vec = embeddings[3]

print("laptop vs device (different words, same meaning):",
      cosine_similarity(laptop_vec, device_vec))
print("iphone vs pie (shared word 'apple', different meaning):",
      cosine_similarity(iphone_vec, pie_vec))
```

```text
laptop vs device (different words, same meaning):  0.63
iphone vs pie (shared word 'apple', different meaning):  0.18
```

Exact numbers vary by model version, but the pattern holds: the
meaning-similar pair scores noticeably higher than the keyword-similar,
meaning-different pair. This is the real version of the toy example from
Lesson 1 — no hand-picked vectors, just a model that learned this structure
from training on billions of real sentences.

## Running Lesson 4's brute-force search on real embeddings

Now plug real embeddings into the brute-force search you already wrote:

```python
corpus = [
    "The cat sat on the windowsill watching birds.",
    "Our server crashed during the deployment last night.",
    "She baked a chocolate cake for the party.",
    "The kitten chased a laser pointer across the floor.",
    "We rolled back the release after it broke production.",
]

corpus_embeddings = model.encode(corpus)
query = "the website went down after we shipped new code"
query_embedding = model.encode(query)

def brute_force_search(query_vec, corpus_vecs, corpus_texts, top_k=3):
    scores = [cosine_similarity(query_vec, vec) for vec in corpus_vecs]
    ranked = sorted(zip(corpus_texts, scores), key=lambda p: p[1], reverse=True)
    return ranked[:top_k]

for text, score in brute_force_search(query_embedding, corpus_embeddings, corpus):
    print(f"{score:.3f}  {text}")
```

You should see the deployment/rollback sentences rank highest — despite the
query sharing almost no exact words with either of them.

## Exercise

Pick 8-10 sentences of your own spanning at least 3 unrelated topics (e.g.
cooking, sports, programming). Encode them all with `model.encode()`, then
write 3 test queries — one per topic — and print the top-3 brute-force
results for each. Confirm the model groups each query with sentences from
the matching topic, not the other two.
