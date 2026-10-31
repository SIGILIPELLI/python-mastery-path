---
description: "This is the project that proves it — not a tutorial, a spec: build a production-shaped RAG platform using every technique from all four levels of this course."
---

# 10 · Capstone Project — Production-Grade RAG Platform

This is the final project of the Vector Databases Mastery Path. Unlike the
project lessons in earlier levels, this one has no guided code to copy —
it's a spec, a checklist, and enough structural guidance to build the thing
over several days. You should be pulling techniques from all four levels:
embeddings and vector search fundamentals (Level 1), a real production
vector database with proper indexing (Level 2), hybrid search and
retrieval-quality engineering (Level 3), and the architecture, evaluation,
security, and portability concerns from this level.

## What you're building

A **RAG platform** — not a single script, a small system with multiple
components — that lets a user ingest a set of documents and ask natural-
language questions over them, with:

- Real, production-shaped retrieval (not brute-force linear scan)
- Measured, not assumed, retrieval quality
- Multi-tenant data isolation
- A backend that isn't hard-wired to one vendor

## Required components

Build all of these. The spec below gives you the shape of each; filling in
the implementation is the project.

### 1. Ingestion pipeline

Takes a folder of documents (plain text or markdown is fine — don't spend
your time on PDF parsing unless you want to), chunks them using a
deliberately chosen strategy (Level 3, lesson 3 — state which strategy you
picked and why), embeds each chunk with a real embedding model (Level 1),
and writes them into your vector store with `tenant_id` metadata attached
to every chunk (Level 4, lesson 3).

### 2. Storage layer, via your abstraction

Use the `VectorStore` interface from lesson 7 — implement at least one real
adapter (Chroma, Qdrant, or pgvector; whichever you have the easiest local
setup for) rather than talking to a vendor SDK directly from application
code. This is a requirement, not a nice-to-have: the whole point of the
capstone is to combine techniques, and the abstraction layer is what makes
the rest of this project (especially tenant isolation and testability)
clean to implement.

### 3. Retrieval pipeline

Implement **hybrid search** (Level 3, lesson 1 — dense vector search + BM25
sparse search, combined) and **re-ranking** (Level 3, lesson 2 — a
cross-encoder re-rank pass over the hybrid candidates before returning
final results). Every retrieval call must take a `tenant_id` and enforce it
as a metadata filter — no code path that queries the vector store should be
able to skip this.

### 4. Generation

Wire the re-ranked, filtered chunks into a prompt and call an LLM to
generate the final answer. This part can be thin — the project is about
retrieval, not prompt engineering — but it needs to exist end to end so you
can evaluate real answers, not just retrieved chunks.

### 5. Evaluation harness

Build a labeled eval set of at least 20 questions against your own test
corpus (Level 4, lesson 2), and a script that runs Recall@K, MRR, and NDCG
for your retrieval pipeline against it. This is what turns "I built a RAG
system" into "I built a RAG system and can prove how good it is."

### 6. Basic security

Multi-tenant isolation via metadata filtering (already required in
component 3) plus a minimal audit log (Level 4, lesson 3) recording every
query: tenant id, timestamp, result count.

## Suggested milestones

Work through these roughly in order — each one should be independently
runnable and testable before you move to the next, rather than building
everything at once and debugging it all together at the end.

1. **Day 1 — Ingestion + storage.** Get documents chunked, embedded, and
   stored via your `VectorStore` abstraction with tenant metadata attached.
   Verify with a trivial unfiltered query that data landed correctly.
2. **Day 2 — Retrieval.** Add hybrid search and re-ranking. Verify
   tenant filtering actually isolates data by inserting documents under two
   different `tenant_id`s and confirming cross-tenant queries return
   nothing.
3. **Day 3 — Generation + end-to-end.** Wire retrieval into an LLM call and
   get a full question-in, answer-out path working.
4. **Day 4 — Evaluation.** Build the labeled eval set and metrics harness.
   Run it against your pipeline and record baseline numbers.
5. **Day 5 — Iterate with evidence.** Make one deliberate change (chunk
   size, re-ranker on/off, hybrid weight between dense and sparse) and
   re-run the eval. Confirm the change actually helped or hurt, using the
   metrics rather than impression.

## Deliverable checklist

- [ ] Ingestion pipeline chunks and embeds documents with a stated,
      deliberate chunking strategy
- [ ] Vector storage goes through a `VectorStore` abstraction, not a direct
      vendor SDK call from application code
- [ ] Every chunk is tagged with `tenant_id` at insert time
- [ ] Retrieval combines dense + sparse (hybrid) search
- [ ] Retrieval includes a cross-encoder re-ranking pass
- [ ] Every retrieval call enforces a tenant filter — verified by a test
      that confirms cross-tenant isolation, not just assumed
- [ ] A minimal audit log records tenant id, timestamp, and result count
      per query
- [ ] An LLM generation step produces a final answer from retrieved context
- [ ] A labeled eval set of 20+ questions exists against your test corpus
- [ ] Recall@K, MRR, and NDCG are computed and reported for your pipeline
- [ ] You made at least one deliberate pipeline change and measured its
      effect with the eval harness, rather than assuming the effect

## What "done" looks like

You should be able to point someone at your project and have them run: an
ingestion command against a folder of documents, a query command that
returns a grounded, retrieved-context answer, and an eval command that
prints Recall@K/MRR/NDCG numbers for your current pipeline configuration.
If a reviewer changes the `tenant_id` on a query and gets another tenant's
data back, or if you can't say what your actual retrieval quality is
because you never measured it, the project isn't done yet — those are
exactly the failure modes this entire level exists to prevent.

This capstone is intentionally open-ended beyond the required components
above. Where this course's earlier lessons gave you a specific library and
a specific worked example, here you're choosing: which chunking strategy,
which backend, which embedding model, which re-ranker, how to weigh hybrid
search — and you now have the evaluation tools from this level to justify
those choices with numbers instead of guesses. That's the actual skill this
40-lesson course has been building toward.
