# ADR 0002: Hybrid retrieval merged with RRF

**Status:** accepted

**Context:** Incident text mixes exact tokens (service names, version numbers, error strings) that full-text search handles well with paraphrases that embeddings handle well.

**Decision:** Run both searches and merge ranks with Reciprocal Rank Fusion, then optionally rerank with a cross-encoder.

**Consequences:** No score normalization needed. Each added stage (window, graph filter, rerank) is measured separately in the ablation eval, so its value is visible rather than assumed.
