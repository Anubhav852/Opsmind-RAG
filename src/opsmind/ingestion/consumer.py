import asyncio

from aiokafka import AIOKafkaConsumer

from ..config import settings
from ..models import Event
from .pipeline import ingest


async def run(batch_size: int = 100):
    c = AIOKafkaConsumer(settings.kafka_topic, bootstrap_servers=settings.kafka_bootstrap,
                         group_id="opsmind-ingest", auto_offset_reset="earliest",
                         enable_auto_commit=False)
    await c.start()
    try:
        while True:
            batches = await c.getmany(timeout_ms=2000, max_records=batch_size)
            events = [Event.model_validate_json(m.value) for msgs in batches.values() for m in msgs]
            if events:
                await asyncio.to_thread(ingest, events)   # CPU/DB work off the event loop
                await c.commit()      # commit AFTER success = at-least-once; ON CONFLICT = idempotent
                print(f"ingested {len(events)}")
    finally:
        await c.stop()


if __name__ == "__main__":
    asyncio.run(run())
