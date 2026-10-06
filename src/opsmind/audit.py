from psycopg.types.json import Jsonb

from .db import conn


def audit(actor: str, action: str, payload: dict) -> None:
    with conn() as c:
        c.execute("INSERT INTO audit_log (actor, action, payload) VALUES (%s,%s,%s)", (actor, action, Jsonb(payload)))
