import json, re, sys
from datetime import datetime
from opsmind.agents.investigator import investigate

MAX = int(sys.argv[1]) if len(sys.argv) > 1 else 30
QUERYISH = re.compile(r"\b(service|level|kind):\S+|\bAND\b|\bOR\b")

def good(out, gt):
    r = out["report"]
    rc = (r.get("root_cause") or "").strip()
    return (out["status"] == "verified"
            and gt["root_event_id"] in r.get("evidence_ids", [])
            and len(rc.split()) >= 5 and not QUERYISH.search(rc)
            and (r.get("remediation") or "").strip()
            and (r.get("confidence") or 0) > 0)

gts = [json.loads(l) for l in open("data/ground_truth.jsonl")]
gts.sort(key=lambda g: g["split"] != "test")          # test incidents first
for tries, gt in enumerate(gts[:MAX], 1):
    out = investigate(groups=["public", "sre"], alert_service=gt["alert_service"],
                      alert_ts=datetime.fromisoformat(gt["alert_ts"]))
    r = out["report"]
    print(f"try {tries}: incident {gt['incident_id']} status={out['status']} "
          f"cited={gt['root_event_id'] in r.get('evidence_ids', [])} conf={r.get('confidence')} "
          f"rc={(r.get('root_cause') or '')[:60]!r}", flush=True)
    if good(out, gt):
        out["id"] = "recorded-demo"
        out["recorded"] = {"incident": gt["incident_id"], "alert_service": gt["alert_service"],
                           "alert_ts": gt["alert_ts"], "tries_to_find_it": tries}
        json.dump(out, open("web/public/sample-investigation.json", "w"), indent=2, default=str)
        print("saved web/public/sample-investigation.json")
        break
else:
    print(f"no good example in {MAX} tries; paste this output")
