import sys
from datetime import datetime, timedelta, timezone

from faster_whisper import WhisperModel

from opsmind.ingestion.pipeline import ingest
from opsmind.models import Event


def main(path: str, service: str, start_iso: str):
    start = datetime.fromisoformat(start_iso).astimezone(timezone.utc)
    model = WhisperModel("base", device="cpu", compute_type="int8")
    segments, _ = model.transcribe(path)
    events = [Event(source="call", kind="call_transcript", service=service,
                    ts=start + timedelta(seconds=s.start), title=f"Incident call at +{s.start:.0f}s",
                    body=s.text.strip(), acl=["sre"]) for s in segments if s.text.strip()]
    print("ingested", ingest(events), "segments")


if __name__ == "__main__":
    main(*sys.argv[1:4])   # usage: python -m opsmind.ml.transcribe_call call.wav checkout 2025-01-02T10:00:00+00:00
