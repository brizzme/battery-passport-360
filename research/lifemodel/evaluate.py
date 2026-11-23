"""Nested grouped evaluation: outer leave-one-batch-out, inner GroupKFold, split-conformal intervals.

Targets are log10(cycle life). Nothing from an outer test batch reaches model fitting, hyper-parameter
selection or interval calibration.
"""
import math
import warnings

import numpy as np
from sklearn.exceptions import ConvergenceWarning
from sklearn.linear_model import ElasticNetCV, LinearRegression
from sklearn.model_selection import GroupKFold, LeaveOneGroupOut
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

L1_RATIOS = [0.1, 0.5, 0.9, 1.0]
ALPHA_GRID = list(np.logspace(-7, 0.5, 60))  # reaches effectively unregularised fits and strong shrinkage
ALPHA = 0.2  # 80 % intervals


class MeanModel:
    def fit(self, x, y, groups=None):
        self.mean_ = float(np.mean(y))
        return self

    def predict(self, x):
        return np.full(len(x), self.mean_)


def _inner_splits(x, groups):
    k = min(5, len(np.unique(groups)))
    return list(GroupKFold(n_splits=k).split(x, groups=groups))


def _fit(kind: str, x, y, groups):
    if kind == "baseline":
        return MeanModel().fit(x, y)
    if kind == "linear":
        return make_pipeline(StandardScaler(), LinearRegression()).fit(x, y)
    if kind == "enet":
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", ConvergenceWarning)
            model = make_pipeline(StandardScaler(), ElasticNetCV(l1_ratio=L1_RATIOS, alphas=ALPHA_GRID,
                                                                 cv=_inner_splits(x, groups), max_iter=50000))
            return model.fit(x, y)
    raise ValueError(kind)


def conformal_quantile(residuals, alpha: float) -> float:
    """k-th smallest absolute residual, k = ceil((n + 1)(1 - alpha)); infinite when k > n."""
    r = np.sort(np.asarray(residuals, dtype=float))
    k = math.ceil((len(r) + 1) * (1 - alpha))
    return float("inf") if k > len(r) else float(r[k - 1])


def _conformal_halfwidth(kind: str, x, y, groups) -> float:
    """CV-residual, conformal-style half-width from inner out-of-fold residuals (training batches only).

    Not split conformal: residuals come from inner refits and exchangeability holds at most at batch level,
    so there is no finite-sample coverage guarantee; empirical coverage is reported instead.
    """
    residuals = np.empty(len(y))
    for tr, te in _inner_splits(x, groups):
        residuals[te] = np.abs(y[te] - _fit(kind, x[tr], y[tr], groups[tr]).predict(x[te]))
    return conformal_quantile(residuals, ALPHA)


def evaluate(x, y_log, groups, kind: str) -> dict:
    x, y_log, groups = np.asarray(x, dtype=float), np.asarray(y_log, dtype=float), np.asarray(groups)
    pred, lo, hi = (np.empty(len(y_log)) for _ in range(3))
    folds = []
    for tr, te in LeaveOneGroupOut().split(x, groups=groups):
        model = _fit(kind, x[tr], y_log[tr], groups[tr])
        p = model.predict(x[te])
        half = _conformal_halfwidth(kind, x[tr], y_log[tr], groups[tr])
        pred[te], lo[te], hi[te] = p, p - half, p + half
        fold = {"train_groups": sorted(int(g) for g in np.unique(groups[tr])),
                "test_groups": sorted(int(g) for g in np.unique(groups[te])), "halfwidth_log": half,
                **metrics(10 ** y_log[te], 10 ** p)}
        enet = getattr(model, "named_steps", {}).get("elasticnetcv")
        if enet is not None:
            fold["alpha"], fold["l1_ratio"] = float(enet.alpha_), float(enet.l1_ratio_)
            fold["nonzero"] = int(np.sum(np.abs(enet.coef_) > 0))
        folds.append(fold)
    return {"pred": pred, "lo": lo, "hi": hi, "folds": folds,
            "coverage": float(np.mean((lo <= y_log) & (y_log <= hi)))}


def metrics(actual, predicted) -> dict:
    a, p = np.asarray(actual, dtype=float), np.asarray(predicted, dtype=float)
    err = p - a
    return {"mae": float(np.mean(np.abs(err))), "rmse": float(np.sqrt(np.mean(err ** 2))),
            "mape": float(100 * np.mean(np.abs(err) / a))}
