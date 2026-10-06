import mlflow
import numpy as np
import torch
import torch.nn as nn
from sklearn.metrics import precision_recall_fscore_support

rng = np.random.default_rng(0)
torch.manual_seed(0)
W = 48


def make_series(n=20000, anomalies=0):
    t = np.arange(n)
    x = 100 + 20 * np.sin(2 * np.pi * t / 288) + rng.normal(0, 3, n)       # daily seasonality + noise
    y = np.zeros(n, dtype=int)
    for _ in range(anomalies):
        s, length = rng.integers(500, n - 100), rng.integers(5, 30)
        x[s:s + length] += rng.choice([-1, 1]) * rng.uniform(40, 80)
        y[s:s + length] = 1
    return x, y


def windows(x, y, stride=8):
    xs = np.stack([x[i:i + W] for i in range(0, len(x) - W, stride)])
    ys = np.array([y[i:i + W].max() for i in range(0, len(x) - W, stride)])
    return xs, ys


class LSTMAE(nn.Module):
    def __init__(self, hidden=32):
        super().__init__()
        self.enc = nn.LSTM(1, hidden, batch_first=True)
        self.dec = nn.LSTM(hidden, hidden, batch_first=True)
        self.out = nn.Linear(hidden, 1)

    def forward(self, x):                         # x: (B, W, 1)
        _, (h, _) = self.enc(x)
        z = h[-1].unsqueeze(1).repeat(1, x.size(1), 1)
        d, _ = self.dec(z)
        return self.out(d)


def errors(model, xs):
    model.eval()
    with torch.no_grad():
        t = torch.tensor(xs, dtype=torch.float32).unsqueeze(-1)
        return ((model(t) - t) ** 2).mean(dim=(1, 2)).numpy()


def main(epochs=15):
    mlflow.set_experiment("opsmind-anomaly")
    xtr, _ = make_series(anomalies=0)
    mu, sd = xtr.mean(), xtr.std()
    xtr = (xtr - mu) / sd
    xtr_w, _ = windows(xtr, np.zeros(len(xtr), dtype=int))
    xte, yte = make_series(anomalies=40)
    xte_w, yte_w = windows((xte - mu) / sd, yte)
    with mlflow.start_run():
        mlflow.log_params({"window": W, "hidden": 32, "epochs": epochs, "lr": 1e-3})
        model, opt, lossf = LSTMAE(), None, nn.MSELoss()
        opt = torch.optim.Adam(model.parameters(), lr=1e-3)
        data = torch.tensor(xtr_w, dtype=torch.float32).unsqueeze(-1)
        for ep in range(epochs):
            model.train()
            perm = torch.randperm(len(data))
            total = 0.0
            for i in range(0, len(data), 128):
                b = data[perm[i:i + 128]]
                opt.zero_grad()
                loss = lossf(model(b), b)
                loss.backward()
                opt.step()
                total += loss.item() * len(b)
            mlflow.log_metric("train_loss", total / len(data), step=ep)
        thr = float(np.percentile(errors(model, xtr_w), 99))       # threshold from NORMAL data only
        pred = (errors(model, xte_w) > thr).astype(int)
        p, r, f1, _ = precision_recall_fscore_support(yte_w, pred, average="binary", zero_division=0)
        mlflow.log_metrics({"threshold": thr, "precision": p, "recall": r, "f1": f1})
        mlflow.pytorch.log_model(model, "model")
        print(f"threshold={thr:.4f} precision={p:.2f} recall={r:.2f} f1={f1:.2f}")


if __name__ == "__main__":
    main()
