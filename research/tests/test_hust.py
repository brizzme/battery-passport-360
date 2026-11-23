import numpy as np
import pytest

from fleetcal.hust import life_distribution, life_to_80, normalized_curve, read_cell_csv


@pytest.fixture
def linear_cell():
    c = np.arange(1, 1001)
    return c, 1.1 * (1 - 0.0003 * c)


def test_life_to_80_detects_crossing(linear_cell):
    c, cap = linear_cell
    # initial = median(cycles 2-6) = cap at cycle 4; crossing where 1-0.0003c < 0.8(1-0.0012)
    assert life_to_80(c, cap) == pytest.approx(670, abs=4)


def test_life_none_when_never_reached():
    assert life_to_80(np.arange(1, 50), np.full(49, 1.1)) is None


def test_life_ignores_single_outlier_dip():
    c = np.arange(1, 301)
    cap = np.full(300, 1.1)
    cap[100] = 0.1
    assert life_to_80(c, cap) is None


def test_curve_endpoints_and_length(linear_cell):
    c, cap = linear_cell
    k = normalized_curve(c, cap, life_to_80(c, cap))
    assert len(k) == 21
    assert k[0] == pytest.approx(1, abs=1e-2)
    assert k[-1] == pytest.approx(0.8, abs=1e-2)


def test_distribution_relative_to_median():
    d = life_distribution([1000, 1500, 2000])
    assert d["median"] == 1500 and d["n"] == 3
    assert d["quantiles"]["50"] == pytest.approx(1.0)
    assert len(d["quantiles"]) == 19
    assert d["lognormal_sigma"] > 0


def test_read_cell_csv(tmp_path):
    p = tmp_path / "1-1.csv"
    p.write_text("cycle,discharge_ah\n1,1.1\n2,1.09\n")
    cycles, cap = read_cell_csv(p)
    assert list(cycles) == [1, 2] and cap[1] == pytest.approx(1.09)
