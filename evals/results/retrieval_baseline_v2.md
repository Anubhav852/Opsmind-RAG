| variant | R@1 | R@3 | R@5 | R@10 | MRR | p50 ms |
|---|---|---|---|---|---|---|
| A vector only, no window | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 275 |
| B hybrid, no window | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 133 |
| C + time window | 0.00 | 0.00 | 0.00 | 0.03 | 0.00 | 31 |
| D + graph filter | 0.00 | 0.00 | 0.00 | 0.19 | 0.02 | 31 |
| E + cross-encoder rerank | 0.00 | 0.00 | 0.01 | 0.16 | 0.02 | 50 |
| F two-hop (error logs, then cause) | 0.00 | 0.00 | 1.00 | 1.00 | 0.25 | 65 |