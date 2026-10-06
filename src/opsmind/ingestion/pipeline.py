from ..db import conn
from ..embeddings import embed
from ..graph.entity_resolution import canonical_service
from ..models import Event, event_text
from ..security.injection import scan
from ..security.redact import redact

INSERT = """INSERT INTO events (id, tenant_id, source, kind, service, ts, title, body, acl, flagged, embedding)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s) ON CONFLICT (id) DO NOTHING"""


def ingest(events: list[Event], batch: int = 64) -> int:
    """Redact -> flag injection -> canonicalize service -> embed -> idempotent insert."""
    done = 0
    for i in range(0, len(events), batch):
        prepared = []
        for e in events[i:i + batch]:
            title, _ = redact(e.title)
            body, _ = redact(e.body)
            svc = canonical_service(e.service)
            prepared.append((e, svc, title, body, bool(scan(f"{title} {body}"))))
        vecs = embed([event_text(svc, e.kind, t, b) for e, svc, t, b, _ in prepared])
        rows = [(e.id, e.tenant_id, e.source, e.kind, svc, e.ts, t, b, e.acl, flagged, vecs[j])
                for j, (e, svc, t, b, flagged) in enumerate(prepared)]
        with conn() as c, c.cursor() as cur:
            cur.executemany(INSERT, rows)
        done += len(rows)
    return done
