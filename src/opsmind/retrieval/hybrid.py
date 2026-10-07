import time
from datetime import datetime, timezone
from functools import lru_cache


from ..config import settings
from ..db import conn
from ..embeddings import embed
from ..metrics import RETRIEVE_LAT

_FILTER = """e.tenant_id = %(tenant)s AND e.acl && %(groups)s::text[]
             AND e.ts BETWEEN %(t0)s AND %(t1)s
             AND (%(services)s::text[] IS NULL OR e.service = ANY(%(services)s::text[]))"""

SQL = f"""
WITH sem AS (
  SELECT e.id, ROW_NUMBER() OVER (ORDER BY e.embedding <=> %(qvec)s) AS r
  FROM events e WHERE {_FILTER}
  ORDER BY e.embedding <=> %(qvec)s LIMIT %(cand)s
), kw AS (
  SELECT e.id, ROW_NUMBER() OVER (ORDER BY ts_rank_cd(e.tsv, q.query) DESC) AS r
  FROM events e,
       (SELECT to_tsquery('english', replace(plainto_tsquery('english', %(qtext)s)::text, '&', '|')) AS query) q
  WHERE {_FILTER} AND e.tsv @@ q.query
  ORDER BY ts_rank_cd(e.tsv, q.query) DESC LIMIT %(cand)s
)
SELECT e.id, e.ts, e.service, e.kind, e.source, e.title, e.body, e.flagged,
       COALESCE(1.0/(60+sem.r), 0) + %(kw_w)s * COALESCE(1.0/(60+kw.r), 0) AS score
FROM events e
LEFT JOIN sem ON sem.id = e.id
LEFT JOIN kw  ON kw.id  = e.id
WHERE sem.id IS NOT NULL OR kw.id IS NOT NULL
ORDER BY score DESC
LIMIT %(cand)s
"""   # Reciprocal Rank Fusion: score = sum(1 / (60 + rank_i)) across rankers

_FAR_PAST = datetime(2000, 1, 1, tzinfo=timezone.utc)
_FAR_FUTURE = datetime(2100, 1, 1, tzinfo=timezone.utc)


@lru_cache(maxsize=1)
def _reranker():
    from sentence_transformers import CrossEncoder
    return CrossEncoder(settings.rerank_model)


def retrieve(query: str, *, tenant: str = "demo", groups: list[str], t0: datetime | None = None,
             t1: datetime | None = None, services: list[str] | None = None, mode: str = "hybrid",
             k: int = 10, rerank: bool = False, candidates: int = 40) -> list[dict]:
    start = time.perf_counter()
    params = dict(tenant=tenant, groups=groups, t0=t0 or _FAR_PAST, t1=t1 or _FAR_FUTURE,
                  services=services, qvec=embed([query])[0], qtext=query, cand=candidates,
                  kw_w=0.0 if mode == "vector" else 1.0)
    with conn() as c:
        rows = c.execute(SQL, params).fetchall()
    for r in rows:
        r["id"] = str(r["id"])
    if rerank and rows:
        scores = _reranker().predict([(query, f"{r['title']}. {r['body']}") for r in rows])
        rows = [r for _, r in sorted(zip(scores, rows, strict=True), key=lambda x: -x[0])]
    RETRIEVE_LAT.observe(time.perf_counter() - start)
    return rows[:k]
