from dataclasses import dataclass
from pathlib import Path
import datetime as dt
from sklearn.metrics import f1_score

import numpy as np    

@dataclass
class MetricsReport:
    name: str
    mae: np.ndarray
    ccc: np.ndarray
    pearson: np.ndarray
    std_ratio: np.ndarray
    quadrant_f1: float

    def as_dict(self):
        d = {"name": self.name}
        for i, l in enumerate("VAD"):
            d[f"mae_{l}"] = round(float(self.mae[i]), 4)
        for i, l in enumerate("VAD"):
            d[f"ccc_{l}"] = round(float(self.ccc[i]), 4)
        for i, l in enumerate("VAD"):
            d[f"pearson_{l}"] = round(float(self.pearson[i]), 4)
        for i, l in enumerate("VAD"):
            d[f"std_ratio_{l}"] = round(float(self.std_ratio[i]), 4)
        d["quadrant_f1"] = round(float(self.quadrant_f1), 4)
        return d

class Metrics:
    def __init__(self):
        self.metric_reports: list[MetricsReport] = []
        self.labels = ("V", "A", "D")

    def mae(self, y_true, y_pred):
        """
        Compute the Mean Absolute Error (MAE) per dimension.

        Args:
            y_true: Ground truth target values of shape (n_samples, n_targets).
            y_pred: Predicted values of shape (n_samples, n_targets).

        Returns:
            np.ndarray: MAE value for each target dimension of shape (n_targets,).
        """
        return np.abs(y_true - y_pred).mean(axis=0)


    def ccc(self, y_true, y_pred):
        """
        Compute Lin's Concordance Correlation Coefficient (CCC) for each dimension.

        CCC evaluates agreement between ground truth and predicted continuous values,
        penalizing both deviations from linear correlation and shifts in scale:
        CCC = (2 * cov(t, p)) / (var(t) + var(p) + (mean(t) - mean(p))^2)

        Args:
            y_true: Ground truth target values of shape (n_samples, n_targets).
            y_pred: Predicted values of shape (n_samples, n_targets).

        Returns:
            np.ndarray: CCC score per dimension of shape (n_targets,). Returns 0.0
            for dimensions where the denominator is zero.
        """
        out = []
        for i in range(y_true.shape[1]):
            t, p = y_true[:, i], y_pred[:, i]
            cov = ((t - t.mean()) * (p - p.mean())).mean()
            denom = t.var() + p.var() + ((t.mean() - p.mean())) ** 2
            out.append(0.0 if denom == 0 else 2 * cov / denom)
        return np.array(out)

    def pearson(self, y_true, y_pred):
        out = []
        for i in range(y_true.shape[1]):
            t, p = y_true[:, i], y_pred[:, i]
            # stała predykcja (np. mean_baseline) -> korelacja nieokreślona
            out.append(0.0 if t.std() == 0 or p.std() == 0 else np.corrcoef(t, p)[0, 1])
        return np.array(out)

    def std_ratio(self, y_true, y_pred):
        return y_pred.std(axis=0) / y_true.std(axis=0)

    def _quadrant(self, y, threshold):
        # 0: V-A-, 1: V-A+, 2: V+A-, 3: V+A+
        return (y[:, 0] > threshold).astype(int) * 2 + (y[:, 1] > threshold).astype(int)

    def quadrant_f1(self, y_true, y_pred, threshold=0.0):
        return f1_score(
            self._quadrant(y_true, threshold),
            self._quadrant(y_pred, threshold),
            average="macro",
            zero_division=0,
        )

    def compute_metrics(self, name, y_true, y_pred):
        self.metric_reports.append(
            MetricsReport(
                name=name,
                mae=self.mae(y_true, y_pred),
                ccc=self.ccc(y_true, y_pred),
                pearson=self.pearson(y_true, y_pred),
                std_ratio=self.std_ratio(y_true, y_pred),
                quadrant_f1=self.quadrant_f1(y_true, y_pred),
            )
        )

    def compute_metrics(self, name, y_true, y_pred):
        self.metric_reports.append(
            MetricsReport(
                name=name,
                mae=self.mae(y_true, y_pred),
                ccc=self.ccc(y_true, y_pred),
                pearson=self.pearson(y_true, y_pred),
                std_ratio=self.std_ratio(y_true, y_pred),
                quadrant_f1=self.quadrant_f1(y_true, y_pred),
            )
        )

    def report(self):
        rows = [r.as_dict() for r in self.metric_reports]
        keys = list(rows[0].keys())[1:]
        print(f"{'name':<20}" + "".join(f"{k:>13}" for k in keys))
        for row in rows:
            print(f"{row['name']:<20}" + "".join(f"{row[k]:>13.4f}" for k in keys))
        return rows
