import numpy as np
import pytest

from lifemodel.features import FEATURES_CAPACITY, FEATURES_VOLTAGE, capacity_features, common_grid, delta_q, voltage_features


def test_capacity_features_linear_fixture():
    c = np.arange(1, 501)
    cap = 1.2 - 0.0001 * c
    f = capacity_features(c, cap)
    assert f["q2"] == pytest.approx(1.2 - 0.0002)
    assert f["slope_91_100"] == pytest.approx(-0.0001)
    assert f["intercept_91_100"] == pytest.approx(1.2)
    assert f["max_minus_q2"] == pytest.approx(0.0)
    assert list(f) == FEATURES_CAPACITY


def test_capacity_features_ignore_cycles_after_100():
    c = np.arange(1, 501)
    cap = 1.2 - 0.0001 * c
    altered = cap.copy()
    altered[100:] = 0.1
    assert capacity_features(c, cap) == capacity_features(c, altered)


def test_capacity_features_require_100_cycles():
    with pytest.raises(ValueError):
        capacity_features(np.arange(1, 50), np.full(49, 1.1))


def test_common_grid_trims_to_shared_coverage():
    g = np.array([2.0, 2.5, 3.0, 3.1])
    a = {"grid": g, "q10": np.array([0, 1, 2, np.nan]), "q100": np.array([0, 1, 2, 3])}
    b = {"grid": g, "q10": np.array([0, 1, 2, 3]), "q100": np.array([0, 1, 2, 3])}
    assert list(common_grid([a, b])) == [True, True, True, False]


def test_delta_q_and_voltage_features():
    qv = {"grid": np.array([2.0, 2.5, 3.0]), "q10": np.array([0.0, 0.10, 0.20]), "q100": np.array([0.0, 0.08, 0.17])}
    mask = np.array([True, True, True])
    dq = delta_q(qv, mask)
    assert list(np.round(dq, 6)) == [0.0, -0.02, -0.03]
    f = voltage_features(dq)
    assert f["log_var"] == pytest.approx(np.log10(np.var(dq)))
    assert f["log_abs_min"] == pytest.approx(np.log10(0.03))
    assert list(f) == FEATURES_VOLTAGE


def test_identical_curves_floor_instead_of_minus_infinity():
    f = voltage_features(np.zeros(5))
    assert np.isfinite(f["log_var"]) and np.isfinite(f["log_abs_min"])
