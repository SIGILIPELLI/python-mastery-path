---
description: "Chunk too small and you lose context; chunk too large and one irrelevant sentence can drown out the one that mattered in the averaged embedding."
---

# 03 · Chunking Strategies for Retrieval Quality

## Why chunking matters as much as the model

A 50-page PDF can't be embedded as one vector and usefully searched — the
embedding would be an average of everything in the document, diluting any
specific fact a query might be looking for. So every real system splits
documents into **chunks** before embedding. How you split has a bigger
effect on retrieval quality than which embedding model you pick.

Two failure modes to keep in mind:

- **Chunks too small** — a sentence fragment without its surrounding context
  ("...which fixes the issue.") is technically retrievable but useless once
  retrieved, and the LLM reading it has no idea what "the issue" was.
- **Chunks too large** — the one relevant sentence gets averaged in with
  nine irrelevant ones, so the chunk's embedding doesn't actually land near
  queries about that one sentence anymore.

## Fixed-size chunking

The simplest approach: split by character or token count, with overlap so
you don't sever a sentence exactly at a chunk boundary.

```python
def fixed_size_chunks(text: str, chunk_size: int = 500, overlap: int = 50):
    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunks.append(text[start:end])
        start = end - overlap  # step back so chunks overlap
    return chunks
```

Overlap (commonly 10-20% of chunk size) means a fact split across two chunks
by bad luck still appears whole in at least one of them. The downside: fixed
boundaries ignore sentence and paragraph structure entirely — a chunk can
start mid-sentence.

## Sentence- and paragraph-aware chunking

Better: split on structure first, then pack sentences/paragraphs into chunks
up to a target size.

```python
import re

def sentence_aware_chunks(text: str, max_chars: int = 500):
    sentences = re.split(r"(?<=[.!?])\s+", text.strip())
    chunks, current = [], ""
    for sentence in sentences:
        if len(current) + len(sentence) > max_chars and current:
            chunks.append(current.strip())
            current = ""
        current += sentence + " "
    if current.strip():
        chunks.append(current.strip())
    return chunks
```

This never cuts a sentence in half. In practice, most production systems
chunk at the paragraph level first (splitting on blank lines or markdown
headers) and only fall back to sentence-level splitting for paragraphs that
exceed the max size on their own.

## Semantic chunking

The most content-aware approach: embed each sentence, then split wherever
the similarity between *adjacent* sentences drops sharply — the idea being
that a topic shift in the text shows up as a drop in embedding similarity
between consecutive sentences.

```python
import numpy as np
from sentence_transformers import SentenceTransformer

model = SentenceTransformer("all-MiniLM-L6-v2")

def semantic_chunks(text: str, drop_threshold: float = 0.3):
    sentences = re.split(r"(?<=[.!?])\s+", text.strip())
    if len(sentences) < 2:
        return [text]

    embeddings = model.encode(sentences, normalize_embeddings=True)
    sims = [float(embeddings[i] @ embeddings[i + 1]) for i in range(len(embeddings) - 1)]

    chunks, current = [], [sentences[0]]
    for i, sim in enumerate(sims):
        if sim < drop_threshold:
            chunks.append(" ".join(current))
            current = []
        current.append(sentences[i + 1])
    chunks.append(" ".join(current))
    return chunks
```

This is noticeably slower (every sentence needs an embedding) and the
threshold needs tuning per-domain, but it tends to produce chunks that align
with actual topic boundaries rather than an arbitrary character count —
useful for long-form documents like reports or transcripts where a fixed
size would frequently split a self-contained idea in two.

## Choosing chunk size for your retriever

A rough starting point, assuming you embed with a model like
`all-MiniLM-L6-v2` (256-token context) or a larger model (512+ tokens):

| Chunk size | Good for | Risk |
|---|---|---|
| 100-200 tokens | FAQ-style, precise fact lookup | loses surrounding context |
| 300-500 tokens | general-purpose RAG | the sweet spot for most document types |
| 800+ tokens | summarization-style retrieval | embedding dilutes specific facts |

Always test empirically (lesson 5 covers how) — the "right" chunk size is
whatever maximizes recall@k on your own eval set, not a number from a blog
post.

## Exercise

Take a multi-paragraph document (a few pages of prose — a README, an
article). Chunk it three ways: fixed-size (500 chars, 50 overlap),
sentence-aware (500 chars), and semantic. For each chunking strategy, embed
the chunks and run the same 3 queries against each resulting chunk set.
Compare: which strategy puts the actually-relevant chunk in the top result
most consistently? Note any case where a fixed-size chunk split a fact in
half and hurt a query's result.
