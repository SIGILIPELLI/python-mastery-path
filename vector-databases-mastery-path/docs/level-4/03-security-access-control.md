---
description: "An embedding isn't anonymous — with enough queries against a known model, the original text can be approximately reconstructed from the vector alone."
---

# 03 · Security & Access Control for Vector Data

A vector database holding customer support tickets, internal documents, or
medical notes is holding sensitive data, even though it looks like harmless
arrays of floats. This lesson covers the access-control and data-protection
concerns specific to vector databases — distinct from, but overlapping
with, ordinary database security.

## Metadata-based row-level access control

Nearly every production vector DB (Pinecone, Qdrant, Weaviate) supports
filtering query results by metadata. The most common multi-tenant pattern
is to tag every vector with a `tenant_id` or `owner_id` at insert time, and
*require* that filter on every query — never trust the caller to remember
to add it.

```python
def search_as_user(collection, query_embedding, user_id: str, top_k: int = 5):
    # The tenant filter is baked into the query function itself, not left
    # to whichever caller happens to remember it.
    return collection.query(
        query_embeddings=[query_embedding],
        n_results=top_k,
        where={"owner_id": user_id},
    )
```

This is **row-level security** implemented at the application layer: the
vector DB doesn't inherently know about your tenants, so the guarantee only
holds if every code path that queries the collection goes through a
function like this one. A direct `collection.query()` call anywhere else in
the codebase that forgets the `where` clause is a data leak waiting to
happen — this is the single most common vector DB security bug in practice,
and it's worth a lint rule or code-review checklist item, not just
discipline.

For stronger isolation, some teams go further and give each tenant a
separate collection or namespace (see Level 2's lesson on namespaces and
multi-tenancy) rather than relying purely on a metadata filter — trading
operational overhead for a guarantee that doesn't depend on every query
remembering a `where` clause.

## Encryption at rest and in transit

Vectors and their metadata should be encrypted at rest, same as any other
sensitive data store. Managed services (Pinecone, Weaviate Cloud, Qdrant
Cloud) typically encrypt storage volumes by default — verify this in your
vendor's docs rather than assuming it. Self-hosted deployments (Qdrant,
Chroma, pgvector) need this configured explicitly: encrypted EBS/disk
volumes, TLS for client connections, and — for the most sensitive
deployments — encrypting the metadata payload itself (the original text
snippet is often stored alongside the vector for retrieval, and that text
is usually the most sensitive part).

```python
# pgvector example: application-layer encryption of the metadata payload
# before it ever reaches the database, using a library like `cryptography`
from cryptography.fernet import Fernet

fernet = Fernet(encryption_key)

def insert_encrypted(cursor, embedding, plaintext_chunk: str, owner_id: str):
    encrypted_chunk = fernet.encrypt(plaintext_chunk.encode())
    cursor.execute(
        "INSERT INTO documents (embedding, chunk_encrypted, owner_id) VALUES (%s, %s, %s)",
        (embedding, encrypted_chunk, owner_id),
    )
```

The embedding vector itself is harder to encrypt usefully — most vector DBs
need the raw float values to compute distances, so encrypting the vector
breaks search. This is exactly why embedding inversion risk (next section)
matters: the vector is effectively unencrypted data even when everything
around it is locked down.

## Embedding inversion risk

A reasonable assumption is that an embedding — a list of 384 or 1536 floats
— is a safe, anonymized representation of text: you can't read the original
sentence off the numbers. This assumption is **wrong**. Research on
embedding inversion attacks (e.g. "Text Embeddings Reveal (Almost) As Much
As Text") has shown that if an attacker knows (or can guess) the embedding
model, they can train an inversion model that maps embeddings back to
plausible — often near-exact — reconstructions of the original text,
especially for short texts like names, addresses, or single sentences.

The practical implication: **treat embedding vectors with the same
sensitivity as the text they were computed from.** Don't assume that
exporting "just the embeddings" for analytics, sharing them with a
third-party vendor, or logging them is safe just because they're not
human-readable. If the underlying text is sensitive (PII, medical notes,
legal documents), the embeddings are sensitive too, and should be covered
by the same access controls, retention policies, and data-sharing
agreements.

## API key scoping

Managed vector DB providers issue API keys — scope them the same way you
would any other credential:

- **Read-only keys** for services that only need to query (e.g. a search
  frontend) — never give query-time services write access they don't need.
- **Per-namespace or per-index keys** where the provider supports it, so a
  compromised key for one application can't read or write another
  application's data.
- **Short-lived keys** issued per-request from a backend that holds the
  long-lived credential, rather than embedding a long-lived key in a
  client-side application — the same pattern you'd use for any other cloud
  credential.

## Audit logging

Log every query (the query text or embedding, the `where` filter applied,
the user/service identity, and the result count) to a separate audit store.
This serves two purposes: detecting access-control bugs (a user whose
queries are returning results outside their `owner_id` filter is a bug you
want to catch quickly, not discover in an incident review), and satisfying
compliance requirements that require proof of who accessed what sensitive
data and when.

```python
def search_with_audit(collection, query_embedding, user_id, top_k=5):
    results = search_as_user(collection, query_embedding, user_id, top_k)
    audit_log.write({
        "user_id": user_id,
        "timestamp": datetime.utcnow().isoformat(),
        "result_count": len(results["ids"][0]),
        "result_ids": results["ids"][0],
    })
    return results
```

## Exercise

Audit a retrieval codebase you've built in an earlier lesson (the semantic
search CLI, or the RAG retrieval service) for every place that calls
`collection.query()` or equivalent. For each one, confirm there's a tenant
or owner filter applied, and if there isn't, add one. Then add a minimal
audit log line that records the query identity and result count for every
search call.
