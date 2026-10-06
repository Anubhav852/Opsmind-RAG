import argparse
import asyncio
from collections.abc import Iterator
from datetime import datetime, timezone

from aiokafka import AIOKafkaProducer

from ..config import settings
from ..db import conn
from ..models import Event
from ..topology import EDGES
from .pipeline import ingest


def iter_jsonl(path: str) -> Iterator[Event]:       # generator: constant memory
    with open(path) as f:
        for line in f:
            yield Event.model_validate_json(line)


def seed_topology() -> None:
    with conn() as c, c.cursor() as cur:
        cur.executemany(
            "INSERT INTO edges (src, dst, valid_from) VALUES (%s,%s,%s) ON CONFLICT DO NOTHING",
            [(s, d, datetime(2024, 1, 1, tzinfo=timezone.utc)) for s, d in EDGES])


async def publish(events: list[Event]) -> None:
    p = AIOKafkaProducer(bootstrap_servers=settings.kafka_bootstrap)
    await p.start()
    try:
        for e in events:   # key = service -> same service lands in same partition (ordering)
            await p.send_and_wait(settings.kafka_topic, e.model_dump_json().encode(), key=e.service.encode())
    finally:
        await p.stop()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("path")
    ap.add_argument("--reset", action="store_true")
    ap.add_argument("--kafka", action="store_true", help="publish to Kafka instead of direct insert")
    a = ap.parse_args()
    if a.reset:
        with conn() as c:
            c.execute("TRUNCATE events, edges RESTART IDENTITY")
    seed_topology()
    events = list(iter_jsonl(a.path))
    if a.kafka:
        asyncio.run(publish(events))
        print(f"published {len(events)} events; run: python -m opsmind.ingestion.consumer")
    else:
        print(f"ingested {ingest(events)} events")


if __name__ == "__main__":
    main()
