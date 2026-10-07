# ADR 0001: Exact vector search, no HNSW index

**Status:** accepted

**Context:** Queries combine vector similarity with selective filters (tenant, ACL, time window, service). Approximate indexes can silently return fewer rows than requested when a selective WHERE clause is applied after the index scan.

**Decision:** Use exact (sequential) cosine search backed by the btree and GIN indexes that narrow candidates first.

**Consequences:** Correct, simple, and fast enough at this scale. At larger scale, add HNSW and verify filtered recall, using pgvector 0.8+ `hnsw.iterative_scan = relaxed_order`.
