# System Design

## Goal
Given an alert (service + timestamp), find the change most likely to have caused it, cite the evidence, and propose a fix. A human approves. Every claim must be checkable against stored events.

## Components

| Component | Role |
|---|---|
| Simulator / connectors / Whisper | Produce events: deploys, commits, config changes, alerts, logs, chat, call transcripts |
| Redpanda (Kafka API) | Durable event stream between producers and the consumer |
| Async consumer | Reads events, runs the ingestion pipeline, writes idempotently |
| Ingestion pipeline | redact secrets/PII, flag prompt injection, canonicalize service names (Union-Find), embed |
| Postgres 16 + pgvector | Single store for events, vectors, full-text (tsvector), graph edges, audit log |
| Hybrid retrieval | vector + full-text, merged with Reciprocal Rank Fusion, optional time window, graph filter and cross-encoder rerank |
| Investigator agent | Tool-calling loop over retrieval and graph tools; read-only |
| Verifier | Structural checks (citations exist, no hallucinated IDs) plus an LLM judge |
| FastAPI | JWT auth, RBAC, rate limiting, audit, /status health |
| Redis | Sliding-window rate limiter |
| React UI | Investigation view, timeline, agent trace, evidence, approval |
| Prometheus, Grafana, Jaeger, MLflow | Metrics, dashboards, traces, experiment tracking |

## Data model
- **events**: id (UUID), tenant, source, kind, service, ts, title, body, acl (text[]), flagged, embedding (vector 384), tsv (generated tsvector). Indexed on (tenant, ts), (service, ts) and GIN on tsv.
- **edges**: temporal service-dependency edges (src DEPENDS_ON dst, valid-from/valid-to) used for upstream lookups and blast radius.
- **audit_log**: append-only; a database trigger rejects UPDATE and DELETE.
- Investigation records are stored so approvals can be tied to a specific report.

## Delivery guarantees
- Kafka consumer is **at-least-once**: offsets are committed after the database write.
- Writes are **idempotent** (upsert by event id), so redelivery cannot create duplicates.
- Partition key is the service, which keeps per-service ordering.

## Retrieval design
1. Hybrid search: vector similarity and BM25-style full-text ranking run separately, then merge with RRF: `score(d) = sum 1 / (k + rank_i(d))`, k = 60.
2. Time window: only events in the N hours before the alert.
3. Graph filter: restrict to the alerting service plus its upstream dependencies at alert time.
4. Cross-encoder rerank of the top candidates.
5. ACL filter is applied in SQL, before ranking, so unauthorized events never reach the agent.

## Agent and verification flow
1. The agent receives the alert and the caller's ACL groups.
2. It calls tools (search, error-log lookup, change lookup, graph walk) for a bounded number of steps.
3. It emits a report: root cause, service, evidence IDs, confidence, suggested fix.
4. The verifier checks that every evidence ID exists and was retrieved, then asks a judge model whether the cited evidence supports the claim.
5. Result is `verified` or `insufficient_evidence`. Only verified reports can be approved.

## Scaling notes
- Exact vector search is used on purpose at this scale (see ADR 0001). Beyond roughly 1M events, add HNSW and test filtered recall.
- Ingestion scales by adding consumers in the same group (up to the partition count).
- The API is stateless; run replicas behind a load balancer (Kubernetes Deployment + HPA is provided).
- LLM calls dominate latency. Cache by (alert, window) and route cheap checks to a smaller model.

## Trade-offs
- One database for everything keeps operations simple and makes ACL filtering atomic with retrieval, at the cost of a ceiling on vector scale.
- A small local model keeps the project free and self-hostable, but is weaker at tool calling (see README results).
- Human approval is required because the system proposes fixes but never executes them.
