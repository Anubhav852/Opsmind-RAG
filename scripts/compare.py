import json, statistics, sys

def metrics(rows, mode):
    approved = (lambda r: r.get("approved_baseline", r["status"] == "verified")) if mode == "old" \
        else (lambda r: r["status"] == "verified")
    n, ver = len(rows), [r for r in rows if approved(r)]
    return {
        "n": n,
        "root_event_seen": round(sum(r.get("root_seen", False) for r in rows) / n, 2),
        "root_event_cited": round(sum(r["event_cited"] for r in rows) / n, 2),
        "root_service_accuracy": round(sum(r["service_correct"] for r in rows) / n, 2),
        "approved": len(ver),
        "correct approvals": sum(r["event_cited"] for r in ver),
        "WRONG approvals": sum(not r["event_cited"] for r in ver),
        "correct answers rejected": sum(r["event_cited"] and not approved(r) for r in rows),
        "avg_tokens": round(statistics.mean(r["tokens"] for r in rows)),
        "p50_latency_s": round(statistics.median(r["latency_s"] for r in rows), 1),
    }

cols = []
for tag in sys.argv[1:]:
    rows = json.load(open(f"evals/results/{tag}.json"))["rows"]
    if any("approved_baseline" in r for r in rows):
        cols += [(f"{tag} [old]", metrics(rows, "old")), (f"{tag} [new rule]", metrics(rows, "new"))]
    else:
        cols.append((tag, metrics(rows, "new")))
print(f"{'metric':26}" + "".join(f"{name:>26}" for name, _ in cols))
for k in cols[0][1]:
    print(f"{k:26}" + "".join(f"{d[k]!s:>26}" for _, d in cols))
