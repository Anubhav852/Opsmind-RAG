# Threat Model

## Assets
- Operational data (logs, chat, call transcripts) that may contain secrets or PII
- Per-group access boundaries (ACLs)
- Integrity of the audit log
- Trustworthiness of reports shown to on-call engineers

## Trust boundaries
- Event content is **untrusted**: anyone who can write a log line or chat message can try to influence the agent.
- The LLM is **untrusted for authorization**: it never decides who can see what.
- The API caller is authenticated (JWT) and authorized (RBAC + ACL groups).

## Threats and mitigations

| # | Threat | Mitigation | Residual risk |
|---|---|---|---|
| 1 | Prompt injection in event text ("ignore previous instructions...") | Regex scan at ingest sets `flagged`; retrieved text is framed as untrusted data; agent tools are read-only; verifier checks claims against evidence; human approval | Regex is a first layer only. Novel phrasing can pass. Canary tests measure leakage |
| 2 | Secrets or PII in events | Redaction at ingest, before storage and embedding | Pattern-based; unknown secret formats can slip through |
| 3 | Cross-tenant or cross-group data leak | ACL filter in SQL before ranking; tenant column; integration tests for ACL | Misconfigured groups at ingest |
| 4 | Hallucinated evidence | Structural verifier rejects IDs that were not retrieved | Judge can still accept a plausible but wrong cited event |
| 5 | Agent takes harmful action | No write-capable tools; fixes are suggestions; approval is human | None by design, until write tools exist |
| 6 | Audit tampering | Append-only table with trigger blocking UPDATE and DELETE | A database superuser can drop the trigger |
| 7 | Brute force and abuse | Redis sliding-window rate limit per user | Distributed attackers |
| 8 | Token theft | Short-lived JWT, secret from environment, HTTPS in deployment | Compromised client |
| 9 | Denial of service via expensive investigations | Rate limit, bounded agent steps, request timeouts | Shared LLM capacity |

## Testing
- `tests/test_security.py`: redaction and injection scanning
- `tests/test_acl.py`: integration test that restricted events never reach a lower-privilege caller
- Adversarial eval: events carrying a canary string are planted, and the eval asserts the canary never appears in agent output (`canary_leaks`)

## Not covered
- Real-world adversaries adapting to the regex rules
- Supply-chain risks in model weights and dependencies
- Multi-region or key-rotation concerns
