import json
from datetime import datetime
from opsmind.agents.investigator import investigate

gts = [g for g in map(json.loads, open("data/ground_truth.jsonl")) if g["split"] == "test"]
for tries, gt in enumerate(gts[:15], 1):
    out = investigate(groups=["public", "sre"], alert_service=gt["alert_service"],
                      alert_ts=datetime.fromisoformat(gt["alert_ts"]))
    hit = gt["root_event_id"] in out["report"]["evidence_ids"]
    print(f"try {tries}: incident {gt['incident_id']} status={out['status']} true_cause_cited={hit}")
    if out["status"] == "verified" and hit:
        out["id"] = "recorded-demo"
        out["recorded"] = {"incident": gt["incident_id"], "alert_service": gt["alert_service"],
                           "alert_ts": gt["alert_ts"], "tries_to_find_it": tries}
        json.dump(out, open("web/public/sample-investigation.json", "w"), indent=2, default=str)
        print("saved web/public/sample-investigation.json")
        break
else:
    print("no verified+correct example in 15 tries; paste this output")
