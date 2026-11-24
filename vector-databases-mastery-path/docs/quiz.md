---
title: "Final Quiz"
description: "Test what you have learned across all four levels of Vector Databases Mastery Path with a 20-question final quiz."
---

# Final Quiz

20 questions drawn from all four levels of this course. You need **70% (14 out of 20)** to pass —
you can retake it as many times as you like. Your best result is saved in this browser.

<div id="mp-quiz-root"></div>

<script type="application/json" id="mp-quiz-data">
[
  {
    "question": "What is the distance from the laptop sentence to the unrelated 'apple pie recipe' vector (3 decimals)?\n```python\nimport numpy as np\nprint(round(float(np.linalg.norm(np.array([0.9, 0.8]) - np.array([-0.5, -0.9]))), 3))\n```\n",
    "options": [
      "2.102",
      "0.071",
      "1.517",
      "2.202"
    ],
    "correctIndex": 3,
    "explanation": "The toy vectors put unrelated meanings far apart. Verified by running it (NumPy 2.5, scikit-learn 1.9, Chroma 1.5, FAISS 1.16)."
  },
  {
    "question": "What do Euclidean distance and cosine similarity say about b = 2a?\n```python\nimport numpy as np\na, b = np.array([1.0, 2.0, 3.0]), np.array([2.0, 4.0, 6.0])\nprint(round(float(np.linalg.norm(a - b)), 3), round(float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))), 1))\n```\n",
    "options": [
      "3.742 1.0",
      "1.0 3.742",
      "3.742 0.5",
      "0.0 1.0"
    ],
    "correctIndex": 0,
    "explanation": "Same direction means cosine 1, yet Euclidean distance is large, which is why cosine is the default for text. Verified by running it (NumPy 2.5, scikit-learn 1.9, Chroma 1.5, FAISS 1.16)."
  },
  {
    "question": "Brute-force cosine search: which document ranks first for [0.88, 0.12, 0, 0]?\n```python\nimport numpy as np\ndocs = {'doc1': [0.9, 0.1, 0.0, 0.0], 'doc2': [0.8, 0.2, 0.1, 0.0], 'doc3': [0.0, 0.9, 0.1, 0.0], 'doc5': [0.85, 0.15, 0.05, 0.0]}\nq = np.array([0.88, 0.12, 0, 0])\ncos = lambda a, b: np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))\nprint(max(docs, key=lambda n: cos(q, np.array(docs[n]))))\n```\n",
    "options": [
      "doc5",
      "doc2",
      "doc3",
      "doc1"
    ],
    "correctIndex": 3,
    "explanation": "Every vector is compared with the query, and the best cosine wins. Verified by running it (NumPy 2.5, scikit-learn 1.9, Chroma 1.5, FAISS 1.16)."
  },
  {
    "question": "What does ANN trade away?",
    "options": [
      "Index durability",
      "A small, tunable amount of recall for much faster queries",
      "Correct embeddings",
      "Metadata"
    ],
    "correctIndex": 1,
    "explanation": "Searching more clusters or a larger candidate list raises recall at some cost in latency."
  },
  {
    "question": "What do these Chroma queries return for a default collection?\n```python\nimport chromadb\ncol = chromadb.Client().get_or_create_collection('final_demo')\ncol.add(ids=['a', 'b'], embeddings=[[1.0, 0.0], [0.9, 0.1]])\nr = col.query(query_embeddings=[[1.0, 0.0]], n_results=2)\nprint(r['ids'][0], [round(d, 3) for d in r['distances'][0]])\n```\n",
    "options": [
      "['a', 'b'] [1.0, 0.9]",
      "['a', 'b'] [0.0, 0.1]",
      "['b', 'a'] [0.02, 0.0]",
      "['a', 'b'] [0.0, 0.02]"
    ],
    "correctIndex": 3,
    "explanation": "The default metric is squared Euclidean, and lower means more similar. Verified by running it (NumPy 2.5, scikit-learn 1.9, Chroma 1.5, FAISS 1.16)."
  },
  {
    "question": "Which ids pass a combined metadata filter?\n```python\nimport chromadb\ncol = chromadb.Client().get_or_create_collection('final_filter')\ncol.add(ids=['t1', 't2', 't3'], embeddings=[[1, 0], [0.9, 0.1], [0.8, 0.2]], metadatas=[{'c': 'billing', 'y': 2024}, {'c': 'billing', 'y': 2023}, {'c': 'auth', 'y': 2024}])\nprint(col.query(query_embeddings=[[1.0, 0.0]], n_results=3, where={'$and': [{'c': 'billing'}, {'y': {'$gte': 2024}}]})['ids'][0])\n```\n",
    "options": [
      "['t1', 't2']",
      "['t2']",
      "['t1', 't3']",
      "['t1']"
    ],
    "correctIndex": 3,
    "explanation": "The filter removes non-matching items before similarity ranking. Verified by running it (NumPy 2.5, scikit-learn 1.9, Chroma 1.5, FAISS 1.16)."
  },
  {
    "question": "Why chunk a document before embedding it?",
    "options": [
      "Databases reject long text",
      "Chunks use less memory",
      "One vector for a long file averages many ideas, diluting any specific fact; chunks let search point at the exact passage",
      "Embeddings need short text"
    ],
    "correctIndex": 2,
    "explanation": "Chunking often matters more than which embedding model you pick."
  },
  {
    "question": "How much does product quantisation shrink a 384-dimension float32 vector with m=8, 8 bits?\n```python\nimport faiss\nprint(faiss.IndexPQ(384, 8, 8).code_size, 384 * 4)\n```\n",
    "options": [
      "8 384",
      "8 1536",
      "1536 8",
      "48 1536"
    ],
    "correctIndex": 1,
    "explanation": "Eight one-byte codes replace 1,536 bytes. Verified by running it (NumPy 2.5, scikit-learn 1.9, Chroma 1.5, FAISS 1.16)."
  },
  {
    "question": "When should you prefer IVF+PQ over HNSW?",
    "options": [
      "When the dataset is huge or RAM-constrained (around 100M+ vectors), accepting some recall loss for about 16 to 32 times less memory",
      "When you need exact results",
      "When writes never happen",
      "When the dataset is tiny"
    ],
    "correctIndex": 0,
    "explanation": "HNSW keeps the whole graph in RAM."
  },
  {
    "question": "What does Weaviate's hybrid alpha=0 mean?",
    "options": [
      "Pure vector search",
      "No search",
      "Pure keyword (BM25) search; alpha=1 is pure vector search",
      "Random order"
    ],
    "correctIndex": 2,
    "explanation": "Intermediate values blend the two."
  },
  {
    "question": "What does Reciprocal Rank Fusion rank first for these two lists?\n```python\ndef rrf(rankings, k=60):\n    s = {}\n    for r in rankings:\n        for i, d in enumerate(r):\n            s[d] = s.get(d, 0) + 1 / (k + i + 1)\n    return max(s, key=s.get)\nprint(rrf([['x', 'y', 'z'], ['y', 'z', 'x']]))\n```\n",
    "options": [
      "w",
      "x",
      "z",
      "y"
    ],
    "correctIndex": 3,
    "explanation": "y ranks second and first, so its summed reciprocal ranks beat x (first and third). Verified by running it (NumPy 2.5, scikit-learn 1.9, Chroma 1.5, FAISS 1.16)."
  },
  {
    "question": "What distinguishes a cross-encoder from a bi-encoder?",
    "options": [
      "It is faster",
      "It reads the query and a document together, so it is slower but more accurate, and is used to re-rank a small candidate set",
      "It stores vectors",
      "It only works on images"
    ],
    "correctIndex": 1,
    "explanation": "Retrieve wide with the bi-encoder, then re-rank the top 50 or so."
  },
  {
    "question": "What are recall-hit and mean recall fraction for this mini eval?\n```python\nev = [({'a', 'b'}, ['a', 'x']), ({'c'}, ['y', 'z']), ({'d'}, ['d', 'w'])]\nprint(round(sum(bool(set(r) & s) for s, r in ev) / 3, 3), round(sum(len(set(r) & s) / len(s) for s, r in ev) / 3, 3))\n```\n",
    "options": [
      "1.0 0.5",
      "0.667 0.667",
      "0.5 0.667",
      "0.667 0.5"
    ],
    "correctIndex": 3,
    "explanation": "Hit counts a query once if any relevant document appears; the fraction metric averages how much of each relevant set was found. Verified by running it (NumPy 2.5, scikit-learn 1.9, Chroma 1.5, FAISS 1.16)."
  },
  {
    "question": "What are the p50 and p95 of these latencies in ms?\n```python\nimport numpy as np\nt = [10, 11, 12, 12, 13, 13, 14, 15, 16, 120]\nprint(float(np.percentile(t, 50)), round(float(np.percentile(t, 95)), 1))\n```\n",
    "options": [
      "13.0 120.0",
      "73.2 13.0",
      "16.0 120.0",
      "13.0 73.2"
    ],
    "correctIndex": 3,
    "explanation": "The tail percentile reveals the slow outliers a median hides. Verified by running it (NumPy 2.5, scikit-learn 1.9, Chroma 1.5, FAISS 1.16)."
  },
  {
    "question": "Why update a changed document by re-embedding and upserting under a stable id?",
    "options": [
      "Vectors can be edited in place",
      "Upsert is slower",
      "The embedding is a function of the text, and an id derived from the text would create a silent duplicate instead of a replacement",
      "Ids are optional"
    ],
    "correctIndex": 2,
    "explanation": "Use a primary key or path as the id."
  },
  {
    "question": "How much does int8 quantisation save over float32 for the same vectors?\n```python\nimport numpy as np\nprint(np.zeros((1000, 384), np.float32).nbytes // np.zeros((1000, 384), np.int8).nbytes)\n```\n",
    "options": [
      "8",
      "4",
      "32",
      "2"
    ],
    "correctIndex": 1,
    "explanation": "One byte instead of four per value, usually with a small recall hit. Verified by running it (NumPy 2.5, scikit-learn 1.9, Chroma 1.5, FAISS 1.16)."
  },
  {
    "question": "What does a forgotten tenant filter leak?\n```python\nimport chromadb\ncol = chromadb.Client().get_or_create_collection('final_tenants')\ncol.add(ids=['a', 'b'], embeddings=[[1, 0], [0.9, 0.1]], metadatas=[{'owner': 'alice'}, {'owner': 'bob'}])\nq = [[1.0, 0.0]]\nprint(col.query(query_embeddings=q, n_results=2, where={'owner': 'bob'})['ids'][0], col.query(query_embeddings=q, n_results=2)['ids'][0])\n```\n",
    "options": [
      "['b'] ['b']",
      "[] ['a']",
      "['a'] ['b']",
      "['b'] ['a', 'b']"
    ],
    "correctIndex": 3,
    "explanation": "The filter must be applied on every code path; one direct query without it exposes other tenants' data. Verified by running it (NumPy 2.5, scikit-learn 1.9, Chroma 1.5, FAISS 1.16)."
  },
  {
    "question": "Why can you not just switch embedding models and re-embed only new documents?",
    "options": [
      "Old vectors are deleted automatically",
      "Models are interchangeable",
      "It is only a cost issue",
      "Vectors from different models are not comparable (and may differ in dimension), so the old half would silently return garbage; the whole corpus must be re-embedded, using dual-write and a shadow read"
    ],
    "correctIndex": 3,
    "explanation": "Migration needs a backfill and a comparison before cutover."
  },
  {
    "question": "Does replication protect against an accidental delete?",
    "options": [
      "No, a bad delete replicates to every replica, so you also need backups; RTO must include index rebuild time",
      "Only with sharding",
      "Only for pgvector",
      "Yes, always"
    ],
    "correctIndex": 0,
    "explanation": "Replication protects against node failure, not logical corruption."
  },
  {
    "question": "What does binary quantisation do to storage for 768 dimensions?\n```python\nimport numpy as np\nv = np.random.default_rng(1).normal(size=768).astype('float32')\nprint(v.nbytes, np.packbits(v > 0).nbytes)\n```\n",
    "options": [
      "3072 768",
      "3072 384",
      "768 96",
      "3072 96"
    ],
    "correctIndex": 3,
    "explanation": "One bit per dimension is 32 times smaller than float32, and distances become Hamming distances. Verified by running it (NumPy 2.5, scikit-learn 1.9, Chroma 1.5, FAISS 1.16)."
  }
]
</script>

## Coding challenges

Try these on your own computer, then compare your output. Nothing you write is sent anywhere.

### Exact search versus cluster-based ANN: measure the recall trade-off

Build brute-force cosine search and a small IVF-style approximate search in NumPy only: pick cluster centres from the data, assign every vector to its nearest centre and, at query time, scan only the nprobe nearest clusters. Measure average recall@5 against the exact answer and the fraction of the data scanned for nprobe 1, 3 and 20. The data are random unit vectors, so the numbers show the shape of the trade-off, not what real embeddings give.

**Starter code**

```python
import numpy as np

rng = np.random.RandomState(7)   # the legacy generator is frozen, so the output is reproducible across NumPy versions
N, D, CLUSTERS, K = 2000, 16, 20, 5
data = rng.standard_normal((N, D))
data /= np.linalg.norm(data, axis=1, keepdims=True)
queries = rng.standard_normal((100, D))
queries /= np.linalg.norm(queries, axis=1, keepdims=True)

# TODO: brute_force(q, k=K) -> set of the indices of the k rows of `data` most similar to q (rows are unit length, so a dot product is cosine)

# index build: TODO choose CLUSTERS centres from the data with rng.choice(N, CLUSTERS, replace=False)
#              TODO assign every vector to its nearest centre: assignment = argmax of data @ centres.T

# TODO: ann_search(q, nprobe, k=K) -> (set of top-k indices, number of vectors scanned)
#       take the nprobe centres closest to q, scan only the vectors assigned to them, rank those by similarity to q

# TODO: for nprobe in (1, 3, 20): average recall@5 against brute_force over all queries, and the average fraction scanned
#       print: f"nprobe={nprobe:2d} recall@{K}={...:.3f} scanned={...:.1%}"
```

**Expected output**

```text
nprobe= 1 recall@5=0.316 scanned=5.2%
nprobe= 3 recall@5=0.582 scanned=15.1%
nprobe=20 recall@5=1.000 scanned=100.0%
```

<details><summary>Show solution and explanation</summary>

<pre><code>import numpy as np

rng = np.random.RandomState(7)   # the legacy generator is frozen, so the output is reproducible across NumPy versions
N, D, CLUSTERS, K = 2000, 16, 20, 5
data = rng.standard_normal((N, D))
data /= np.linalg.norm(data, axis=1, keepdims=True)
queries = rng.standard_normal((100, D))
queries /= np.linalg.norm(queries, axis=1, keepdims=True)

def brute_force(q, k=K):
    &quot;&quot;&quot;Exact top-k by cosine similarity (rows are unit length, so a dot product).&quot;&quot;&quot;
    return set(np.argsort(data @ q)[::-1][:k])

# index build: pick centres from the data, assign every vector to its nearest centre
centres = data[rng.choice(N, CLUSTERS, replace=False)]
assignment = np.argmax(data @ centres.T, axis=1)

def ann_search(q, nprobe, k=K):
    &quot;&quot;&quot;Search only the nprobe clusters whose centres are closest to the query.&quot;&quot;&quot;
    nearest = np.argsort(centres @ q)[::-1][:nprobe]
    ids = np.flatnonzero(np.isin(assignment, nearest))
    top = ids[np.argsort(data[ids] @ q)[::-1][:k]]
    return set(top), len(ids)

for nprobe in (1, 3, 20):
    hits, scanned = 0, 0
    for q in queries:
        found, n = ann_search(q, nprobe)
        hits += len(found &amp; brute_force(q))
        scanned += n
    print(f&quot;nprobe={nprobe:2d} recall@{K}={hits / (K * len(queries)):.3f} scanned={scanned / (N * len(queries)):.1%}&quot;)
</code></pre>

<p>Scanning only the nearest cluster covers about 5% of the data and finds roughly a third of the true neighbours; probing three clusters covers 15% and recovers about 60%; probing all twenty is exact search again. This is the recall-versus-work dial that nprobe (and ef_search in HNSW) gives you. Run with NumPy and its output checked.</p>
</details>

### A tenant-safe hybrid retrieval core with an evaluation harness

Using Chroma with explicit toy embeddings, build the core of the Level 4 capstone: a dense search that always applies a tenant_id filter, a keyword search over the same tenant's chunks, Reciprocal Rank Fusion of the two rankings, and a small evaluation (Recall@1 and MRR) over three labelled queries. Also show that an unfiltered query leaks another tenant's chunk. The embeddings are made-up three-number vectors; a real system would use an embedding model.

**Starter code**

```python
import chromadb

# (id, tenant, text, 3-number toy embedding) - real systems would use model.encode(text)
CHUNKS = [
    ("a1", "acme",   "reset the vpn adapter and re-enter credentials", [0.9, 0.1, 0.0]),
    ("a2", "acme",   "error ERR_CONN_RESET means the tls handshake timed out", [0.2, 0.9, 0.1]),
    ("a3", "acme",   "company holiday calendar and office hours", [0.0, 0.1, 0.9]),
    ("g1", "globex", "globex vpn setup is confidential", [0.95, 0.05, 0.0]),
]
col = chromadb.Client().get_or_create_collection("capstone_demo")
col.add(ids=[c[0] for c in CHUNKS], embeddings=[c[3] for c in CHUNKS],
        documents=[c[2] for c in CHUNKS], metadatas=[{"tenant_id": c[1]} for c in CHUNKS])

# TODO: dense(query_vec, tenant, k=3)   -> ids from col.query(...) restricted with where={"tenant_id": tenant}
# TODO: sparse(query_text, tenant, k=3) -> ids of that tenant's chunks ranked by how many lowercase query words they share
#       (ties broken by id, chunks with no shared word dropped)
# TODO: rrf(rankings, k=60) -> ids sorted by the sum of 1 / (k + rank + 1) over the rankings they appear in
# TODO: search(query_text, query_vec, tenant) = rrf([dense(...), sparse(...)])
# TODO: recall_at_k(found, relevant, k) and reciprocal_rank(found, relevant)

EVAL = [
    ("vpn adapter credentials", [0.85, 0.1, 0.05], {"a1"}),
    ("ERR_CONN_RESET", [0.5, 0.5, 0.2], {"a2"}),
    ("office hours", [0.1, 0.2, 0.8], {"a3"}),
]
print(search("ERR_CONN_RESET", [0.5, 0.5, 0.2], "acme"))
print(search("vpn", [0.95, 0.05, 0.0], "globex"))
print("unfiltered leak:", col.query(query_embeddings=[[0.95, 0.05, 0.0]], n_results=2)["ids"][0])
runs = [(search(t, v, "acme"), rel) for t, v, rel in EVAL]
print("recall@1 =", round(sum(recall_at_k(f, r, 1) for f, r in runs) / len(runs), 3))
print("mrr =", round(sum(reciprocal_rank(f, r) for f, r in runs) / len(runs), 3))
```

**Expected output**

```text
['a2', 'a1', 'a3']
['g1']
unfiltered leak: ['g1', 'a1']
recall@1 = 1.0
mrr = 1.0
```

<details><summary>Show solution and explanation</summary>

<pre><code>import chromadb

# (id, tenant, text, 3-number toy embedding) - real systems would use model.encode(text)
CHUNKS = [
    (&quot;a1&quot;, &quot;acme&quot;,   &quot;reset the vpn adapter and re-enter credentials&quot;, [0.9, 0.1, 0.0]),
    (&quot;a2&quot;, &quot;acme&quot;,   &quot;error ERR_CONN_RESET means the tls handshake timed out&quot;, [0.2, 0.9, 0.1]),
    (&quot;a3&quot;, &quot;acme&quot;,   &quot;company holiday calendar and office hours&quot;, [0.0, 0.1, 0.9]),
    (&quot;g1&quot;, &quot;globex&quot;, &quot;globex vpn setup is confidential&quot;, [0.95, 0.05, 0.0]),
]
col = chromadb.Client().get_or_create_collection(&quot;capstone_demo&quot;)
col.add(ids=[c[0] for c in CHUNKS], embeddings=[c[3] for c in CHUNKS],
        documents=[c[2] for c in CHUNKS], metadatas=[{&quot;tenant_id&quot;: c[1]} for c in CHUNKS])

def dense(query_vec, tenant, k=3):
    r = col.query(query_embeddings=[query_vec], n_results=k, where={&quot;tenant_id&quot;: tenant})
    return r[&quot;ids&quot;][0]

def sparse(query_text, tenant, k=3):
    terms = set(query_text.lower().split())
    scored = [(len(terms &amp; set(c[2].lower().split())), c[0]) for c in CHUNKS if c[1] == tenant]
    return [cid for score, cid in sorted(scored, key=lambda p: (-p[0], p[1])) if score &gt; 0][:k]

def rrf(rankings, k=60):
    scores = {}
    for ranking in rankings:
        for rank, cid in enumerate(ranking):
            scores[cid] = scores.get(cid, 0.0) + 1.0 / (k + rank + 1)
    return [cid for cid, _ in sorted(scores.items(), key=lambda p: -p[1])]

def search(query_text, query_vec, tenant):
    return rrf([dense(query_vec, tenant), sparse(query_text, tenant)])

def recall_at_k(found, relevant, k):
    return len(set(found[:k]) &amp; relevant) / len(relevant)

def reciprocal_rank(found, relevant):
    return next((1 / i for i, c in enumerate(found, 1) if c in relevant), 0.0)

EVAL = [
    (&quot;vpn adapter credentials&quot;, [0.85, 0.1, 0.05], {&quot;a1&quot;}),
    (&quot;ERR_CONN_RESET&quot;, [0.5, 0.5, 0.2], {&quot;a2&quot;}),
    (&quot;office hours&quot;, [0.1, 0.2, 0.8], {&quot;a3&quot;}),
]
print(search(&quot;ERR_CONN_RESET&quot;, [0.5, 0.5, 0.2], &quot;acme&quot;))
print(search(&quot;vpn&quot;, [0.95, 0.05, 0.0], &quot;globex&quot;))
print(&quot;unfiltered leak:&quot;, col.query(query_embeddings=[[0.95, 0.05, 0.0]], n_results=2)[&quot;ids&quot;][0])
runs = [(search(t, v, &quot;acme&quot;), rel) for t, v, rel in EVAL]
print(&quot;recall@1 =&quot;, round(sum(recall_at_k(f, r, 1) for f, r in runs) / len(runs), 3))
print(&quot;mrr =&quot;, round(sum(reciprocal_rank(f, r) for f, r in runs) / len(runs), 3))
</code></pre>

<p>The tenant filter is applied inside dense() and sparse() so no caller can forget it, RRF combines the semantic and exact-term views (the error code is found by keywords, the VPN query by meaning), and the evaluation turns the result into numbers. The unfiltered query shows the leak the filter prevents. Run with Chroma 1.5 and its output checked.</p>
</details>
