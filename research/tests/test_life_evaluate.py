import numpy as np
import pytest

from lifemodel.evaluate import evaluate, metrics


def synthetic(n_groups=6, per=6, noise=0.02, seed=0):
    rng = np.random.default_rng(seed)
    x = rng.normal(size=(n_groups * per, 2))
    y = 3.2 + 0.1 * x[:, 0] + rng.normal(0, noise, n_groups * per)
    groups = np.repeat(np.arange(1, n_groups + 1), per)
    return x, y, groups


def test_metrics_in_cycles():
    m = metrics(np.array([1000.0, 2000.0]), np.array([1100.0, 1800.0]))
    assert m["mae"] == pytest.approx(150.0) and m["rmse"] == pytest.approx(np.sqrt((100**2 + 200**2) / 2))
    assert m["mape"] == pytest.approx(100 * (0.1 + 0.1) / 2)


@pytest.mark.parametrize("kind", ["baseline", "linear", "enet"])
def test_outer_folds_never_share_groups(kind):
    x, y, g = synthetic()
    r = evaluate(x, y, g, kind)
    assert len(r["folds"]) == 6
    for f in r["folds"]:
        assert not set(f["train_groups"]) & set(f["test_groups"]) and len(f["test_groups"]) == 1
    assert np.all(np.isfinite(r["pred"])) and len(r["pred"]) == len(y)


def test_baseline_is_training_mean_per_fold():
    x, y, g = synthetic()
    r = evaluate(x, y, g, "baseline")
    for f in r["folds"]:
        train = ~np.isin(g, f["test_groups"])
        assert np.allclose(r["pred"][np.isin(g, f["test_groups"])], y[train].mean())


def test_informative_feature_beats_baseline():
    x, y, g = synthetic(noise=0.01)
    base = evaluate(x, y, g, "baseline")
    enet = evaluate(x, y, g, "enet")
    assert np.mean(np.abs(enet["pred"] - y)) < np.mean(np.abs(base["pred"] - y))


def test_intervals_contain_predictions_and_report_coverage():
    x, y, g = synthetic()
    r = evaluate(x, y, g, "enet")
    assert np.all(r["lo"] <= r["pred"]) and np.all(r["pred"] <= r["hi"])
    assert r["coverage"] == pytest.approx(np.mean((r["lo"] <= y) & (y <= r["hi"])))


def test_uninformative_features_reduce_to_intercept_without_crashing():
    rng = np.random.default_rng(1)
    x = rng.normal(size=(36, 3))
    y = 3.2 + rng.normal(0, 0.05, 36)
    g = np.repeat(np.arange(1, 7), 6)
    r = evaluate(x, y, g, "enet")
    assert np.all(np.isfinite(r["pred"]))


def test_conformal_quantile_is_kth_order_statistic():
    from lifemodel.evaluate import conformal_quantile
    res = np.arange(1, 70, dtype=float)  # n = 69, k = ceil(70 * 0.8) = 56
    assert conformal_quantile(res, 0.2) == 56.0
    assert conformal_quantile(np.array([1.0, 2.0]), 0.2) == np.inf  # k = 3 > n


def test_alpha_search_reaches_near_zero():
    from lifemodel.evaluate import ALPHA_GRID
    assert min(ALPHA_GRID) <= 1e-6 and max(ALPHA_GRID) >= 1.0
