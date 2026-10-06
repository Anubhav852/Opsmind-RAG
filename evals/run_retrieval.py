import argparse
from collections import Counter
import json
import statistics
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path

from opsmind.graph.temporal_graph import load_graph, upstream
from opsmind.retrieval.hybrid import retrieve

VARIANTS = {
    "A vector only, no window": dict(mode="vector", window=False, graph=False, rerank=False),
    "B hybrid, no window":      dict(mode="hybrid", window=False, graph=False, rerank=False),
    "C + time window":          dict(mode="hybrid", window=True,  graph=False, rerank=False),
    "D + graph filter":         dict(mode="hybrid", window=True,  graph=True,  rerank=False),
    "E + cross-encoder rerank": dict(mode="hybrid", window=True,  graph=True,  rerank=True),
    "F two-hop (error logs, then cause)": dict(mode="hybrid", window=True, graph=True, rerank=True, hop2=True),
}


def evaluate(split: str, limit: int | None):
    gts = [json.loads(line) for line in open("data/ground_truth.jsonl")]
    gts = [g for g in gts if g["split"] == split][:limit]
    results = {}
    for name, v in VARIANTS.items():
        ranks, lat = [], []
        for gt in gts:
            t1 = datetime.fromisoformat(gt["alert_ts"])
            services = None
            if v["graph"]:
                services = [gt["alert_service"], *upstream(load_graph(t1), gt["alert_service"])]
            t = time.perf_counter()
            query = gt["alert_text"]
            if v.get("hop2"):
                hop1 = retrieve("ERROR WARN failed timeout exception", groups=["public"], mode="hybrid",
                                t0=t1 - timedelta(hours=3), t1=t1, services=services, k=20, candidates=60)
                errs = [r for r in hop1 if r["kind"] == "log" and r["title"].startswith(("ERROR", "WARN"))]
                if errs:
                    query = Counter(r["title"] for r in errs).most_common(1)[0][0]
            rows = retrieve(query, groups=["public"], mode=v["mode"],
                            t0=t1 - timedelta(hours=3) if v["window"] else None,
                            t1=t1 if v["window"] else None, services=services, k=10,
                            rerank=v["rerank"], candidates=40)
            lat.append(time.perf_counter() - t)
            if v.get("hop2"):
                rows = [r for r in rows if r["kind"] in ("deploy", "config_change")]
            ids = [r["id"] for r in rows]
            ranks.append(ids.index(gt["root_event_id"]) + 1 if gt["root_event_id"] in ids else None)
        n = len(ranks)
        rec = lambda k: sum(1 for r in ranks if r and r <= k) / n   # noqa: E731
        results[name] = {"recall@1": rec(1), "recall@3": rec(3), "recall@5": rec(5), "recall@10": rec(10),
                         "mrr": sum(1 / r for r in ranks if r) / n,
                         "p50_ms": statistics.median(lat) * 1000, "n": n}
    return results


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--split", default="test")
    ap.add_argument("--limit", type=int)
    ap.add_argument("--tag", default="baseline")
    ap.add_argument("--gate-recall5", type=float, default=0.0, help="fail if best variant recall@5 is below")
    a = ap.parse_args()
    res = evaluate(a.split, a.limit)
    Path("evals/results").mkdir(parents=True, exist_ok=True)
    Path(f"evals/results/retrieval_{a.tag}.json").write_text(json.dumps(res, indent=2))
    lines = ["| variant | R@1 | R@3 | R@5 | R@10 | MRR | p50 ms |", "|---|---|---|---|---|---|---|"]
    for k, m in res.items():
        lines.append(f"| {k} | {m['recall@1']:.2f} | {m['recall@3']:.2f} | {m['recall@5']:.2f} | "
                     f"{m['recall@10']:.2f} | {m['mrr']:.2f} | {m['p50_ms']:.0f} |")
    table = "\n".join(lines)
    Path(f"evals/results/retrieval_{a.tag}.md").write_text(table)
    print(f"split={a.split} n={list(res.values())[0]['n']} tag={a.tag}\n{table}")
    if list(res.values())[-1]["recall@5"] < a.gate_recall5:
        sys.exit(f"FAIL: recall@5 below gate {a.gate_recall5}")


if __name__ == "__main__":
    main()
