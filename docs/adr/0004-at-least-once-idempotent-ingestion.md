# ADR 0004: At-least-once delivery with idempotent writes

**Status:** accepted

**Context:** Exactly-once delivery across Kafka and Postgres is complex and unnecessary here.

**Decision:** Commit Kafka offsets after the database write and make writes idempotent with an upsert keyed on event id.

**Consequences:** Crashes cause redelivery but never duplicates or lost events.
