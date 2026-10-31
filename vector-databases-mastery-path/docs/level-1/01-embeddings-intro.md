---
description: "Embeddings pack meaning into dense numeric vectors, so sentences with similar meaning end up near each other in vector space even when they share no words at all."
---

# 01 · What Are Embeddings & Why Vector Search

## The problem with keyword search

Classic search (grep, SQL `LIKE`, full-text indexes) matches on *words*. That
breaks the moment two pieces of text mean the same thing but say it
differently:

- "My laptop won't turn on" vs. "device fails to power up" — zero shared
  keywords, same problem.
- "Apple released a new phone" vs. "apple pie recipe" — shares the word
  "apple", completely different topics.

Keyword matching can't tell these apart because it never represents *meaning*
— only strings.

## What an embedding actually is

An **embedding** is a fixed-length list of numbers (a vector) produced by a
model that has learned to place semantically similar inputs close together
and dissimilar inputs far apart. For text, a sentence like `"a sleepy cat"`
might become something like:

```python
[0.12, -0.44, 0.08, ..., 0.31]   # e.g. 384 numbers for a small model
```

The individual numbers mean nothing on their own — you can't point to
dimension 57 and say "that's catness." What matters is *relative position*:
vectors for related concepts cluster together in this high-dimensional space.

## A worked example (toy vectors, no model yet)

To build intuition before touching a real embedding model, imagine a
pretend 2D "meaning space" where we've hand-placed a few sentences:

```python
import numpy as np

# Pretend embeddings — hand-picked to illustrate the idea, not real output
vectors = {
    "my laptop won't turn on":        np.array([0.9, 0.8]),
    "device fails to power up":       np.array([0.85, 0.75]),   # similar MEANING
    "apple released a new phone":     np.array([-0.6, 0.5]),
    "apple pie recipe":                np.array([-0.5, -0.9]),  # similar WORD, different meaning
}

def euclidean(a, b):
    return np.linalg.norm(a - b)

query = vectors["my laptop won't turn on"]
for text, vec in vectors.items():
    print(f"{text:35s} distance={euclidean(query, vec):.3f}")
```

```text
my laptop won't turn on            distance=0.000
device fails to power up           distance=0.071
apple released a new phone         distance=1.517
apple pie recipe                   distance=2.102
```

"device fails to power up" lands almost on top of the laptop complaint —
despite sharing *no words* with it. Meanwhile "apple released a new phone"
and "apple pie recipe" share a word but sit far apart from each other, and
both sit far from the laptop sentences. That's the whole idea of vector
search: **distance in embedding space approximates distance in meaning.**

## Why this course exists

Once you can turn any piece of content — a sentence, a paragraph, an image,
a product description — into a vector, a huge number of problems reduce to
one operation: **"find the vectors nearest to this one."**

- **Semantic search**: embed a user's query, find the nearest document
  chunks.
- **RAG (Retrieval-Augmented Generation)**: embed a question, retrieve the
  most relevant chunks, hand them to an LLM as context.
- **Recommendations**: embed a user's history, find nearby items.
- **Deduplication / clustering**: group vectors that sit close together.

A **vector database** is just a system purpose-built to store millions (or
billions) of these vectors and answer "find the nearest ones" queries fast.
That's what the rest of this course is about: generating real embeddings,
understanding how "nearest" is measured, and running that search at scale
using real vector databases.

## Exercise

Without writing any code, sketch (on paper or in a comment block) three
pairs of sentences:

1. A pair that means the same thing but shares **no** keywords.
2. A pair that shares a keyword but means **different** things.
3. A pair that is both keyword-similar **and** meaning-similar.

For each pair, predict whether a keyword search engine and a vector search
engine would consider them "similar," and write one sentence explaining why
they'd disagree (or agree) in each case. You'll verify these predictions
with a real model in Lesson 5.
