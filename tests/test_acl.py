from datetime import datetime, timedelta, timezone

import pytest

from opsmind.db import conn
from opsmind.ingestion.pipeline import ingest
from opsmind.models import Event
from opsmind.retrieval.hybrid import retrieve

pytestmark = pytest.mark.integration

T = datetime(2030, 1, 1, tzinfo=timezone.utc)


@pytest.fixture(autouse=True)
def clean_acl_test_data():
    with conn() as c:
        c.execute("DELETE FROM events WHERE tenant_id = 't-acl'")
    yield
    with conn() as c:
        c.execute("DELETE FROM events WHERE tenant_id = 't-acl'")


def test_private_events_hidden_without_group():
    ingest([
        Event(
            tenant_id="t-acl",
            source="slack",
            kind="chat",
            service="payments",
            ts=T,
            title="secret pentest finding",
            body="restricted note",
            acl=["security"],
        )
    ])

    kw = dict(
        tenant="t-acl",
        t0=T - timedelta(hours=1),
        t1=T + timedelta(hours=1),
        services=["payments"],
    )

    assert retrieve("pentest finding", groups=["public"], **kw) == []
    assert len(retrieve("pentest finding", groups=["public", "security"], **kw)) == 1
