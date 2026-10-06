| variant | R@1 | R@3 | R@5 | R@10 | MRR | p50 ms |
|---|---|---|---|---|---|---|
| A vector only, no window | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 301 |
| B hybrid, no window | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 161 |
| C + time window | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 22 |
| D + graph filter | 0.00 | 0.00 | 0.00 | 0.16 | 0.02 | 20 |
| E + cross-encoder rerank | 0.00 | 0.00 | 0.00 | 0.19 | 0.02 | 49 |
| F two-hop (error logs, then cause) | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 69 |