---
description: "Fine-tuning an embedding model doesn't memorize answers — it reshapes the vector space so your actual queries and relevant documents are pulled closer together."
---

# 04 · Embedding Model Selection & Fine-Tuning Basics

## How to pick an embedding model

Every embedding model trades off along the same four axes:

- **Quality** — how well it ranks relevant-vs-irrelevant documents on
  benchmark tasks. The [MTEB leaderboard](https://huggingface.co/spaces/mteb/leaderboard)
  (Massive Text Embedding Benchmark) is the standard reference: it scores
  hundreds of models across retrieval, classification, and clustering tasks.
- **Dimensionality** — `all-MiniLM-L6-v2` produces 384-dim vectors;
  `text-embedding-3-large` can produce up to 3072. Higher dimensionality
  usually means better quality but more storage and slower search.
- **Max sequence length** — how much text one embedding call can see before
  truncating. A model with a 256-token limit silently drops the rest of a
  long chunk; a 512+ token model handles longer chunks without truncation.
- **Latency and cost** — a small local model like `all-MiniLM-L6-v2` (22M
  parameters) embeds thousands of documents per second on a CPU and costs
  nothing per call. A hosted API model may rank higher on MTEB but adds
  network latency and a per-token bill at scale.

```python
# Comparing two models on the same small eval set
from sentence_transformers import SentenceTransformer
import numpy as np

small_model = SentenceTransformer("all-MiniLM-L6-v2")       # 384-dim, fast, free
big_model = SentenceTransformer("all-mpnet-base-v2")         # 768-dim, slower, higher quality

queries = ["how does TLS handshake failure happen"]
docs = [
    "TLS handshakes fail due to cipher mismatch or expired certificates",
    "Our return policy allows 30 days for unopened items",
]

for name, model in [("MiniLM", small_model), ("MPNet", big_model)]:
    q = model.encode(queries, normalize_embeddings=True)[0]
    d = model.encode(docs, normalize_embeddings=True)
    sims = d @ q
    print(name, sims)
```

For most RAG applications, start with a small, fast, open model
(`all-MiniLM-L6-v2` or similar) and only move to something larger/hosted if
your eval set (lesson 5) actually shows it's not good enough — "biggest
model on MTEB" is rarely the right default, since the gap often doesn't
matter for your specific domain and the latency/cost difference is real.

## When fine-tuning is worth it

A general-purpose embedding model is trained on broad web text. If your
domain uses specialized vocabulary — internal product names, legal/medical
jargon, a company's own acronyms — the general model may genuinely not know
which documents are "close" in your domain's sense, no matter how well it
scores on MTEB. That's the signal to fine-tune: your own eval set shows
plateauing recall that re-ranking and better chunking don't fix.

Fine-tuning here means **further training a model on your own
(query, relevant_document) pairs** so it learns your domain's notion of
relevance, without needing labeled negative examples.

```bash
pip install sentence-transformers
```

```python
from sentence_transformers import SentenceTransformer, InputExample, losses
from torch.utils.data import DataLoader

model = SentenceTransformer("all-MiniLM-L6-v2")

# Your own labeled pairs: queries matched to their one correct document
train_examples = [
    InputExample(texts=["how do I reset ERR_CONN_RESET", "ERR_CONN_RESET occurs when the TLS handshake times out"]),
    InputExample(texts=["password recovery steps", "reset your password from the login screen"]),
    # ... hundreds to thousands of real pairs from your own query logs or support tickets
]

train_dataloader = DataLoader(train_examples, shuffle=True, batch_size=16)
train_loss = losses.MultipleNegativesRankingLoss(model)

model.fit(
    train_objectives=[(train_dataloader, train_loss)],
    epochs=3,
    warmup_steps=100,
    output_path="./fine-tuned-domain-model",
)
```

Where do the pairs come from in practice? Query logs paired with the
document the user actually clicked or found useful, support tickets paired
with their resolving KB article, or — if you have none of that yet — an LLM
can bootstrap synthetic (query, document) pairs from your corpus to get
started before you have real usage data.

## How It Actually Works

1. **In-batch negatives.** `MultipleNegativesRankingLoss` needs only
   *positive* pairs — it builds negatives automatically from the rest of the
   batch. For a batch of 16 (query, document) pairs, each query's own
   document is the positive, and the other 15 documents in the batch become
   its negatives for that training step.
2. **The contrastive objective.** The loss pushes each query's embedding
   closer to its true document's embedding (higher cosine similarity) and
   simultaneously pushes it away from the 15 in-batch negatives (lower
   similarity). Over many batches and epochs, this reshapes the embedding
   space so your domain's query-document pairs cluster together.
3. **Why larger batches help.** More in-batch negatives per step means a
   harder, more informative training signal — the model has to distinguish
   the true match from more competitors at once. This is why fine-tuning
   recipes often push batch size as high as GPU memory allows.
4. **What actually changes in the model.** Fine-tuning doesn't memorize your
   documents or "store" answers anywhere — it adjusts the transformer's
   weights so that *the function mapping text to a vector* places your
   domain's related pairs nearer each other than the pretrained weights did.
   The model still generalizes to unseen text; it's just been nudged toward
   your domain's geometry.
5. **The failure mode to watch for.** With too few training pairs or too
   many epochs, the model overfits to your training pairs specifically and
   loses some of its general-purpose quality on anything outside that
   distribution. Always re-run your eval set (next lesson) after
   fine-tuning, including on queries *not* in the training set, before
   deciding to deploy it.

## Exercise

Using sentence-transformers, write 20-30 `InputExample` pairs from a domain
you know well (your own project's docs, a hobby's terminology — anything
with enough specialized vocabulary). Fine-tune `all-MiniLM-L6-v2` for 3
epochs, then compare the fine-tuned model against the original on 5 domain
queries: does the fine-tuned model rank the correct document higher on
queries that use your domain's specific terms?
