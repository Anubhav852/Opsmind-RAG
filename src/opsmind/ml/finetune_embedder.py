import json
from pathlib import Path

from sentence_transformers import InputExample, SentenceTransformer, losses
from torch.utils.data import DataLoader

from opsmind.config import settings
from opsmind.graph.entity_resolution import canonical_service
from opsmind.models import Event, event_text


def text_of(e: Event) -> str:
    return event_text(canonical_service(e.service), e.kind, e.title, e.body)


def main(out="models/opsmind-embed-ft", epochs=3):
    events = {str(e.id): e for e in (Event.model_validate_json(line) for line in open("data/events.jsonl"))}
    gts = [json.loads(line) for line in open("data/ground_truth.jsonl")]
    pairs = []
    for gt in gts:
        if gt["split"] != "train":        # NEVER train on test cause types
            continue
        pos = text_of(events[gt["root_event_id"]])
        pairs.append(InputExample(texts=[gt["alert_text"], pos]))                       # alert -> root cause
        for sid in gt["symptom_event_ids"][:1]:
            pairs.append(InputExample(texts=[text_of(events[sid]), pos]))               # symptom -> root cause
    print(f"{len(pairs)} training pairs")
    model = SentenceTransformer(settings.embed_model)
    loader = DataLoader(pairs, shuffle=True, batch_size=16)
    loss = losses.MultipleNegativesRankingLoss(model)       # in-batch negatives
    model.fit(train_objectives=[(loader, loss)], epochs=epochs, warmup_steps=int(0.1 * len(loader) * epochs),
              output_path=out, show_progress_bar=True)
    Path(out).mkdir(parents=True, exist_ok=True)
    print("saved", out)


if __name__ == "__main__":
    main()
