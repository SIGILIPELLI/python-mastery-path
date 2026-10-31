---
description: "Chunking a document before embedding it — rather than embedding the whole file as one vector — is the difference between a search tool that returns a precise snippet and one that just returns 'yes, it's somewhere in this file.'"
---

# 10 · Project — Semantic Search CLI

Time to combine everything from this level into one working tool: a
command-line semantic search engine over your own text files.

## What you're building

A CLI with two commands:

```bash
# 1. Index every .txt file in a folder
python search_cli.py index ./my_notes

# 2. Search across everything you've indexed
python search_cli.py search "how do I reset my vpn connection"
```

Example expected output for `search`:

```text
$ python search_cli.py search "how do I reset my vpn connection"

1. [0.847] notes/it-setup.txt
   "...if the VPN client won't connect, try restarting the adapter
   and re-entering your credentials before escalating to IT..."

2. [0.621] notes/onboarding.txt
   "...network access requires connecting through the company VPN,
   which you'll set up during your first week..."
```

## Requirements

1. **`index <folder>`** walks a folder, reads every `.txt` file, splits each
   file into chunks (don't embed a whole file as one vector — see "Why
   chunking matters" below), embeds each chunk with `sentence-transformers`,
   and stores them in a **persistent** Chroma collection with metadata
   recording which file (and roughly which position in it) each chunk came
   from.
2. **`search <query>`** embeds the query, runs it against the persisted
   collection, and prints the top-5 results: similarity score, source
   filename, and a snippet of the matching chunk.
3. Running `index` twice on the same folder should not duplicate entries
   (reuse Lesson 8's `upsert` or clear-and-rebuild, your choice — just avoid
   silent duplicates).
4. Use Python's `argparse` or `sys.argv` to make this a real CLI, not just
   two separate scripts.

## Why chunking matters

If you embed an entire 2,000-word file as a single vector, that vector ends
up representing the *average* meaning of the whole file — a single
paragraph about VPN setup buried inside a much longer onboarding document
gets diluted into near-meaninglessness. Splitting a file into smaller
chunks (e.g. every ~3-5 sentences, or every paragraph) before embedding
means each chunk's vector represents one coherent idea, and your search can
point directly at the relevant paragraph instead of just "somewhere in this
file." You'll go much deeper on chunking strategy in Level 3, Lesson 3 —
for this project, a simple paragraph-or-fixed-size split is enough.

## Suggested structure

```python
# search_cli.py
import argparse
import pathlib
import chromadb
from sentence_transformers import SentenceTransformer

MODEL_NAME = "all-MiniLM-L6-v2"
DB_PATH = "./search_cli_data"
COLLECTION_NAME = "notes"
CHUNK_SIZE = 500   # characters; tune as you like

model = SentenceTransformer(MODEL_NAME)
client = chromadb.PersistentClient(path=DB_PATH)


def chunk_text(text, chunk_size=CHUNK_SIZE):
    """Split text into roughly chunk_size-character pieces, breaking on
    paragraph boundaries where possible."""
    # Your implementation — paragraphs first, then fall back to a hard
    # character split for any paragraph longer than chunk_size.
    ...


def cmd_index(folder):
    collection = client.get_or_create_collection(name=COLLECTION_NAME)
    txt_files = pathlib.Path(folder).glob("**/*.txt")

    for file_path in txt_files:
        text = file_path.read_text(encoding="utf-8")
        chunks = chunk_text(text)
        embeddings = model.encode(chunks).tolist()

        ids = [f"{file_path}::{i}" for i in range(len(chunks))]
        metadatas = [{"source": str(file_path), "chunk_index": i} for i in range(len(chunks))]

        collection.upsert(
            ids=ids,
            documents=chunks,
            embeddings=embeddings,
            metadatas=metadatas,
        )
    print(f"Indexed {sum(1 for _ in pathlib.Path(folder).glob('**/*.txt'))} files.")


def cmd_search(query, top_k=5):
    collection = client.get_or_create_collection(name=COLLECTION_NAME)
    query_embedding = model.encode(query).tolist()

    results = collection.query(query_embeddings=[query_embedding], n_results=top_k)

    for rank, (doc, meta, distance) in enumerate(
        zip(results["documents"][0], results["metadatas"][0], results["distances"][0]), start=1
    ):
        similarity = 1 - distance   # rough conversion if using l2; adjust for your metric
        snippet = doc[:200].replace("\n", " ")
        print(f"\n{rank}. [{similarity:.3f}] {meta['source']}")
        print(f'   "...{snippet}..."')


def main():
    parser = argparse.ArgumentParser(description="Semantic search over local .txt files")
    subparsers = parser.add_subparsers(dest="command", required=True)

    index_parser = subparsers.add_parser("index")
    index_parser.add_argument("folder")

    search_parser = subparsers.add_parser("search")
    search_parser.add_argument("query")

    args = parser.parse_args()

    if args.command == "index":
        cmd_index(args.folder)
    elif args.command == "search":
        cmd_search(args.query)


if __name__ == "__main__":
    main()
```

The `chunk_text()` function and the exact similarity-score conversion in
`cmd_search` are left for you to finish — that's the part of this project
that's genuinely yours to design.

## Stretch goals (optional)

- Support `.md` files in addition to `.txt`, stripping Markdown syntax
  before chunking.
- Add a `--top-k N` flag to `search` instead of hardcoding 5.
- Track and skip re-indexing files that haven't changed since the last run
  (compare file modification time, stored as metadata).

## Exercise

Build the CLI above against a folder of at least 8-10 of your own short
`.txt` notes spanning a few different topics. Run at least 5 different
search queries and, for each, judge by eye whether the top result is
genuinely the most relevant note you have. Write down one query where the
tool surprised you (good or bad) and your best guess at why, based on what
you now know about embeddings and chunking.
