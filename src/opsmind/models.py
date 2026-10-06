from datetime import datetime
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class Event(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    tenant_id: str = "demo"
    source: str            # github | deploy | pagerduty | logs | slack | call | jira
    kind: str              # deploy | config_change | commit | alert | log | chat | call_transcript
    service: str
    ts: datetime
    title: str
    body: str = ""
    acl: list[str] = Field(default_factory=lambda: ["public"])


def event_text(service: str, kind: str, title: str, body: str) -> str:
    """The exact text that gets embedded. Used by ingestion AND fine-tuning, keep identical."""
    return f"{service} {kind}: {title}. {body}".strip()
