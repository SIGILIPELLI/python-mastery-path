---
description: "pgvector's <-> operator does nearest-neighbor ranking inside ordinary SQL, which means vector search can finally JOIN against the rest of your data."
---

# 04 · pgvector: Vectors Inside PostgreSQL

pgvector is a PostgreSQL extension that adds a `vector` column type and distance
operators. Instead of running a separate vector database, you store embeddings
next to the relational data they describe — in the same table, the same
transactions, the same backups.

## Installing the extension

```sql
CREATE EXTENSION IF NOT EXISTS vector;
```

(On managed Postgres like Supabase, Neon, or RDS, this is usually a one-click or
one-command enable; self-hosted Postgres needs the `pgvector` package installed
on the server first.)

## Creating a table with a vector column

```sql
CREATE TABLE articles (
    id SERIAL PRIMARY KEY,
    title TEXT NOT NULL,
    body TEXT NOT NULL,
    embedding VECTOR(384)
);
```

`VECTOR(384)` must match your embedding model's dimension — just like Pinecone's
`dimension` parameter, but enforced at the SQL schema level.

## Inserting embeddings

```python
import psycopg2
from sentence_transformers import SentenceTransformer

model = SentenceTransformer("all-MiniLM-L6-v2")
conn = psycopg2.connect("dbname=mydb")
cur = conn.cursor()

text = "pgvector keeps embeddings next to relational data."
embedding = model.encode(text).tolist()

cur.execute(
    "INSERT INTO articles (title, body, embedding) VALUES (%s, %s, %s)",
    ("pgvector intro", text, embedding),
)
conn.commit()
```

## Nearest-neighbor queries

```sql
SELECT title, body, embedding <-> '[0.01, -0.02, ...]'::vector AS distance
FROM articles
ORDER BY embedding <-> '[0.01, -0.02, ...]'::vector
LIMIT 5;
```

pgvector gives you three distance operators:

- `<->` — Euclidean (L2) distance
- `<#>` — negative inner product (for dot-product similarity)
- `<=>` — cosine distance

From Python with psycopg2, pass the query vector as a parameter instead of
string-formatting it:

```python
query_vector = model.encode("how do distance operators work").tolist()

cur.execute(
    "SELECT title, body FROM articles ORDER BY embedding <=> %s::vector LIMIT 5",
    (query_vector,),
)
for row in cur.fetchall():
    print(row)
```

## Indexing for speed

Without an index, `ORDER BY embedding <-> ...` does a full sequential scan — fine
for thousands of rows, too slow for millions. Add an HNSW index:

```sql
CREATE INDEX ON articles USING hnsw (embedding vector_cosine_ops);
```

Or an IVFFlat index (faster to build, slightly lower recall — covered in depth
next lesson):

```sql
CREATE INDEX ON articles USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);
```

Note `vector_cosine_ops` must match the distance operator you query with
(`vector_l2_ops` for `<->`, `vector_ip_ops` for `<#>`).

## When "just use Postgres" wins

If your data already lives in Postgres and you need semantic search over, say,
10,000-5,000,000 rows with moderate query volume, pgvector lets you avoid standing
up and operating an entirely separate database. You get transactional writes
(insert a row and its embedding atomically with other relational updates), SQL
joins between vector results and relational tables (e.g. filter by a `user_id`
foreign key and rank by embedding distance in one query), and one less system to
back up, monitor, and secure. Dedicated vector databases pull ahead at very large
scale (hundreds of millions+ of vectors) or when you need features pgvector
doesn't offer, like Pinecone/Weaviate-style namespacing or built-in hybrid fusion
scoring.

## Exercise

Set up a local Postgres with pgvector (Docker image `pgvector/pgvector:pg16` is
the fastest path), create the `articles` table above, insert your 10 Level 1
documents with real embeddings, and write one SQL query that both filters by a
`WHERE title ILIKE '%keyword%'` condition and orders by `<=>` cosine distance —
something no pure vector database in this level can do in a single native query
without a client-side join.
