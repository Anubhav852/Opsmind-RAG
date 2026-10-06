from datetime import datetime, timedelta, timezone
from uuid import UUID

import jwt
from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from psycopg.types.json import Jsonb
from pydantic import BaseModel

from ..agents.investigator import investigate
from ..audit import audit
from ..config import settings
from ..db import conn
from ..observability import setup_observability
from ..retrieval.hybrid import retrieve
from ..security.ratelimit import allow

app = FastAPI(title="OpsMind")
import os

CORS_ORIGINS = [
    origin.strip()
    for origin in os.getenv(
        "CORS_ORIGINS",
        "http://localhost:5173"
    ).split(",")
    if origin.strip()
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_methods=["*"],
    allow_headers=["*"],
    allow_credentials=True,
)
setup_observability(app)
bearer = HTTPBearer()


class User(BaseModel):
    sub: str
    groups: list[str]


class TokenReq(BaseModel):
    user: str
    groups: list[str] = ["public"]


class SearchReq(BaseModel):
    query: str
    at: datetime
    minutes: int = 180
    services: list[str] | None = None


class InvestigateReq(BaseModel):
    alert_service: str
    alert_ts: datetime


def current_user(creds: HTTPAuthorizationCredentials = Depends(bearer)) -> User:
    try:
        p = jwt.decode(creds.credentials, settings.jwt_secret, algorithms=["HS256"])
    except jwt.PyJWTError:
        raise HTTPException(401, "invalid token") from None
    return User(sub=p["sub"], groups=sorted(set(p.get("groups", [])) | {"public"}))


def limited(user: User = Depends(current_user)) -> User:
    if not allow(f"rl:{user.sub}", settings.rate_limit_per_min, 60):
        raise HTTPException(429, "rate limit exceeded")
    return user


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/auth/token")
def token(req: TokenReq):
    """DEMO ONLY. In production replace with OIDC (Auth0/Keycloak/Cognito)."""
    if not settings.demo_mode:
        raise HTTPException(404)
    exp = datetime.now(timezone.utc) + timedelta(hours=8)
    return {"token": jwt.encode({"sub": req.user, "groups": req.groups, "exp": exp},
                                settings.jwt_secret, algorithm="HS256")}


@app.post("/search")
def search(req: SearchReq, user: User = Depends(limited)):
    rows = retrieve(req.query, groups=user.groups, t0=req.at - timedelta(minutes=req.minutes), t1=req.at,
                    services=req.services, k=10, rerank=True)
    audit(user.sub, "search", {"query": req.query, "returned": [r["id"] for r in rows]})
    return [{"id": r["id"], "ts": r["ts"], "service": r["service"], "kind": r["kind"], "title": r["title"]}
            for r in rows]


@app.post("/investigate")
def run_investigation(req: InvestigateReq, user: User = Depends(limited)):
    result = investigate(groups=user.groups, alert_service=req.alert_service, alert_ts=req.alert_ts)
    alert = {"service": req.alert_service, "ts": req.alert_ts.isoformat()}
    with conn() as c:
        row = c.execute("INSERT INTO investigations (created_by, alert, result) VALUES (%s,%s,%s) RETURNING id",
                        (user.sub, Jsonb(alert), Jsonb(result))).fetchone()
    audit(user.sub, "investigate", {"investigation": str(row["id"]), "status": result["status"],
                                    "tokens": result["tokens"]})
    return {"id": str(row["id"]), **result}


@app.post("/investigations/{inv_id}/approve")
def approve(inv_id: UUID, user: User = Depends(limited)):
    if "sre" not in user.groups:
        raise HTTPException(403, "sre group required")
    with conn() as c:
        row = c.execute("UPDATE investigations SET status='approved', approved_by=%s "
                        "WHERE id=%s AND status='proposed' RETURNING id", (user.sub, inv_id)).fetchone()
    if not row:
        raise HTTPException(404, "not found or already decided")
    audit(user.sub, "approve", {"investigation": str(inv_id)})
    return {"status": "approved", "note": "Approval recorded. No production action is executed automatically."}
