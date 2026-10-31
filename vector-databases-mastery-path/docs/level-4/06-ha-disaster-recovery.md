---
description: "Rebuilding an HNSW index for a billion-vector collection from a cold backup can take hours — RTO for a vector DB has to account for index build time, not just data restore time."
---

# 06 · High Availability & Disaster Recovery

A vector database that loses data or goes down has the same consequences as
any other database outage — but vector-specific failure modes (index
corruption, long rebuild times at scale) mean HA/DR planning needs a few
considerations beyond the standard database playbook.

## Replication

Most production vector databases support **replica sets**: multiple copies
of each shard, so a node failure doesn't lose data or availability.

- **Qdrant and Weaviate** support configurable replication factors per
  collection — e.g. `replication_factor: 3` means each shard's data lives
  on three nodes, and queries can be served by any replica.
- **Pinecone** (managed) handles replication transparently as part of the
  service.
- **pgvector** inherits PostgreSQL's replication story — streaming
  replication to standby replicas, with the usual Postgres HA tooling
  (Patroni, etc.) layered on top.

```python
# Qdrant: creating a collection with replication
from qdrant_client import QdrantClient
from qdrant_client.models import VectorParams, Distance

client = QdrantClient(url="http://localhost:6333")
client.create_collection(
    collection_name="docs",
    vectors_config=VectorParams(size=384, distance=Distance.COSINE),
    replication_factor=3,
    shard_number=6,
)
```

Replication protects against a single node failing, but it does **not**
protect against logical corruption or accidental deletion — a bad delete
query replicates to every replica just as reliably as a good one. That's
what backups are for.

## Multi-region deployment

For global, latency-sensitive applications, or for resilience against an
entire region going down, deploy read replicas (or full independent
clusters kept in sync) across regions:

- **Active-passive**: one primary region handles writes, other regions
  serve read-only replicas — simpler, but failover requires promoting a
  replica and redirecting writes.
- **Active-active**: multiple regions accept writes, requiring a
  conflict-resolution strategy (last-write-wins by timestamp, or
  application-level merge logic) — more complex, but no single region is a
  single point of failure for writes.

Most teams start active-passive for vector workloads, since write volume to
a vector DB (document ingestion) is usually much lower and less
latency-sensitive than query volume, and query load is what multi-region
replicas are mainly solving for.

## Backup and restore

Back up both the **raw source data** (the original documents/metadata,
which you can always re-embed from) and the **vector index itself** (so
restore doesn't require re-embedding everything from scratch, which can be
slow and costly for a large corpus):

```python
# Chroma: a persistent client's data directory IS the backup unit
import shutil

def backup_chroma(source_path: str, backup_path: str):
    shutil.copytree(source_path, backup_path, dirs_exist_ok=True)

# Qdrant: use its built-in snapshot API
import requests

def snapshot_qdrant_collection(base_url: str, collection: str):
    resp = requests.post(f"{base_url}/collections/{collection}/snapshots")
    return resp.json()["result"]["name"]
```

Test restores regularly, not just backups — a backup you've never
successfully restored from is a guess, not a safety net.

## RPO and RTO

- **RPO (Recovery Point Objective)**: how much data you can afford to lose,
  measured in time — "RPO of 1 hour" means you back up (or replicate)
  often enough that at most an hour of writes is lost in a disaster.
- **RTO (Recovery Time Objective)**: how long you can afford to be down —
  "RTO of 4 hours" means recovery, start to finish, must complete within 4
  hours.

For vector databases specifically, RTO needs to account for **index
rebuild time**, not just data restore time. Restoring a billion-vector
collection's raw data from a snapshot might take minutes, but if the index
structure itself wasn't included in that snapshot (some restore paths
restore vectors and rebuild the HNSW graph from scratch), rebuilding an
HNSW index at that scale can take hours, because graph construction is not
a simple bulk-copy operation — it involves, for every inserted vector,
finding and linking to its approximate neighbors (Level 2's HNSW lesson
covers why this isn't instant). Always measure actual rebuild time at
representative scale during DR drills, rather than assuming restore time
equals "back online" time.

## Vector-specific failure modes

- **Index corruption**: a partial write, crash mid-rebuild, or disk issue
  can corrupt the HNSW graph structure without corrupting the underlying
  vector data — symptoms are usually degraded recall (queries silently
  return worse results) rather than a hard error, which makes this failure
  mode easy to miss without the retrieval-quality monitoring from Level 3.
- **Rebuild time at scale**: covered above — plan for it explicitly in your
  RTO, don't discover it during a real incident.
- **Shard imbalance after a node failure**: if replication isn't configured
  correctly, losing a node can concentrate query load on the remaining
  replicas disproportionately, causing a cascading slowdown rather than a
  clean failover — verify your replica configuration actually redistributes
  load, don't just assume it from the config file.

## Exercise

Write a short DR runbook (a few paragraphs, not a full document) for your
RAG retrieval service from Level 2: define an RPO and RTO you consider
reasonable for it, list the specific backup mechanism you'd use for your
chosen vector DB backend, and describe the exact steps you'd take to
restore service after losing the primary node, including where index
rebuild time fits into your RTO estimate.
