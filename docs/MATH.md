# Math Notes

## Cosine similarity
For embeddings a and b: `cos(a, b) = (a . b) / (|a| |b|)`. pgvector's cosine distance is `1 - cos(a, b)`, so lower distance means more similar.

## Reciprocal Rank Fusion (RRF)
Given ranked lists from several retrievers, a document d gets

`RRF(d) = sum over lists i of 1 / (k + rank_i(d))`

with k = 60. Documents ranked high in several lists win. RRF needs no score calibration between vector and full-text search, which is why it is used here.

## Retrieval metrics
Let `r_q` be the rank of the true root-cause event for incident q (undefined if absent from the top k), and N the number of incidents.

- **Recall@k** = (1/N) * count of q with r_q <= k
- **MRR** = (1/N) * sum over q of 1 / r_q, counting 0 when absent

## Anomaly detector (LSTM autoencoder)
Trained on normal metric windows. Reconstruction error `e = mean((x - x_hat)^2)`. A window is flagged when `e` exceeds a threshold chosen on a validation set. Reported with:

- Precision = TP / (TP + FP)
- Recall = TP / (TP + FN)
- F1 = 2PR / (P + R)

## Agent metrics
- **Verified rate** = verified reports / incidents
- **True cause cited** = reports whose evidence IDs include the ground-truth root event
- **Hallucinated-citation rate** = reports citing IDs that were never retrieved
- **Canary leaks** = adversarial canary strings that appear in output

## Small-sample caution
With N = 8, one incident moves a rate by 12.5 points. Treat differences smaller than that as noise, and report the count (for example 3 of 8) alongside any rate.
