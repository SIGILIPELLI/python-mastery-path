---
description: "CLIP embeds images and text into the same vector space, so a text query like 'a dog running on a beach' can retrieve photos directly — no caption needed."
---

# 04 · Multi-Modal Vector Search

Every embedding so far has come from text. **Multi-modal** embedding models
map *different kinds of input* — text and images, most commonly — into the
**same shared vector space**, so a text query's embedding lands near the
embeddings of images it actually describes. This is what powers "search
your photo library by typing a description" and image-based product
search.

## CLIP: a joint embedding space

CLIP (Contrastive Language-Image Pre-training) is trained on (image,
caption) pairs with a contrastive objective: push the embedding of an image
and its correct caption close together, and push it away from captions of
*other* images in the same training batch. The result is a single
embedding space where text and images are directly comparable by cosine
similarity, even though they're completely different kinds of data.

```bash
pip install sentence-transformers pillow
```

```python
from sentence_transformers import SentenceTransformer
from PIL import Image

model = SentenceTransformer("clip-ViT-B-32")

# Embed images and text into the SAME vector space
image_embedding = model.encode(Image.open("beach_dog.jpg"))
text_embedding = model.encode("a dog running on a beach")

import numpy as np
cosine_sim = np.dot(image_embedding, text_embedding) / (
    np.linalg.norm(image_embedding) * np.linalg.norm(text_embedding)
)
print(cosine_sim)  # high similarity if the image matches the description
```

## Storing and querying across modalities

Store image embeddings in your vector DB exactly like text embeddings —
the DB doesn't care what produced the vector, only its dimensionality.

```python
import chromadb

client = chromadb.PersistentClient(path="./multimodal_db")
collection = client.get_or_create_collection("photos")

image_paths = ["beach_dog.jpg", "mountain_sunset.jpg", "city_street.jpg"]
embeddings = [model.encode(Image.open(p)).tolist() for p in image_paths]

collection.add(
    ids=[f"img-{i}" for i in range(len(image_paths))],
    embeddings=embeddings,
    metadatas=[{"path": p} for p in image_paths],
)

# Query with TEXT, get back IMAGES
query_embedding = model.encode("a dog running on a beach").tolist()
results = collection.query(query_embeddings=[query_embedding], n_results=2)
print(results["metadatas"])  # [{'path': 'beach_dog.jpg'}, ...]
```

The query pipeline is identical to the text-to-text pipeline from Level 1 —
embed the query, run `collection.query()`, get back nearest neighbors. The
only difference is *what* produced each embedding, which is invisible to
the vector DB itself. This is also why multi-modal search composes cleanly
with everything else in this course: metadata filtering, hybrid search, and
re-ranking all still apply, as long as a cross-encoder re-ranker (Level 3)
supports image-text pairs if you want re-ranking on top.

## Image-to-image and mixed queries

Because images and text share the space, you can also query with an image
to find similar images (reverse image search), or combine both — e.g.
average a text embedding and an image embedding to search for "images like
this one, but more X":

```python
def combined_query(model, image_path: str, text_hint: str, weight: float = 0.5):
    img_emb = model.encode(Image.open(image_path))
    text_emb = model.encode(text_hint)
    combined = weight * img_emb + (1 - weight) * text_emb
    combined = combined / np.linalg.norm(combined)
    return collection.query(query_embeddings=[combined.tolist()], n_results=5)

results = combined_query(model, "mountain_sunset.jpg", "but with snow")
```

## Beyond CLIP

`open_clip` (an open-source reimplementation with many more model variants
and training datasets) is a common alternative when you need larger models
or specific domain fine-tunes:

```bash
pip install open_clip_torch
```

```python
import open_clip
import torch

model, _, preprocess = open_clip.create_model_and_transforms(
    "ViT-B-32", pretrained="laion2b_s34b_b79k"
)
tokenizer = open_clip.get_tokenizer("ViT-B-32")

image = preprocess(Image.open("beach_dog.jpg")).unsqueeze(0)
text = tokenizer(["a dog running on a beach"])

with torch.no_grad():
    image_features = model.encode_image(image)
    text_features = model.encode_text(text)
```

Newer multi-modal models (e.g. SigLIP, and video/audio-extending variants)
follow the same contrastive joint-embedding idea, just with different
training data and sometimes additional modalities beyond image and text.

## How It Actually Works

1. **Why contrastive training produces a shared space at all.** CLIP's loss
   function doesn't just reward matching pairs being close — it simultaneously
   pushes every *non-matching* pair in the training batch apart, for both
   image→text and text→image directions. Trained over hundreds of millions
   of pairs, this forces the model to organize the space around *semantic
   content* rather than modality — "dogness" and "beachness" become
   directions in the space that both images and text can express, rather
   than text and images living in separate clusters.
2. **Why this breaks down for very fine-grained or unusual queries.** CLIP's
   training data is internet image-caption pairs, which skew toward common,
   well-captioned subjects. Queries needing fine-grained distinctions
   (exact species of bird, specific industrial part numbers) or OCR-style
   reading of text *inside* images are often poorly represented — the joint
   space is only as good as what was contrastively trained, and niche
   domains usually need a fine-tuned or domain-specific multi-modal model
   rather than off-the-shelf CLIP.
3. **Why the same dimensionality and distance metric rules from Level 1-2
   still apply.** A CLIP embedding is still just a vector — cosine
   similarity, HNSW indexing, quantization, all of it works unmodified.
   Multi-modal search isn't a different kind of vector database problem, it's
   the same vector database problem with a different embedding function in
   front of it.

## Exercise

Build a small multi-modal collection from 10-15 images you have locally
(any mix of subjects). Embed them with `clip-ViT-B-32`, store them in
Chroma, and run three text queries describing different images. Then try
one query describing something *not* in your collection and check what
comes back — note how the model still returns its "closest" guesses even
when nothing is actually a good match, and consider how you'd use a
similarity-score threshold (not just top-k) to detect "no good match" cases.
