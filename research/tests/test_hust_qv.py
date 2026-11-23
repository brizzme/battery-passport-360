import json

import numpy as np
import pytest

from fleetcal.hust import read_qv
from hust_extract.extract import GRID, qv_from_arrays


def synthetic_cycle():
    """5C stage, then a final 1C segment from 3.2 V down to 2.0 V over 720 s (0.22 Ah)."""
    t1 = np.arange(0, 100, 1.0)
    i1 = np.full_like(t1, -5500.0)
    v1 = np.linspace(3.3, 3.25, t1.size)
    t2 = np.arange(100, 821, 1.0)
    i2 = np.full_like(t2, -1100.0)
    v2 = np.linspace(3.2, 2.0, t2.size)
    return np.r_[t1, t2], np.r_[i1, i2], np.r_[v1, v2]


def test_remaining_capacity_on_final_1c_segment():
    q, start_v = qv_from_arrays(*synthetic_cycle())
    assert start_v == pytest.approx(3.2)
    g = np.asarray(GRID)
    assert q[np.searchsorted(g, 2.0)] == pytest.approx(0.0, abs=1e-3)
    assert q[np.searchsorted(g, 3.195)] == pytest.approx(0.22, rel=0.02)   # nearly the whole segment remains
    assert np.isnan(q[np.searchsorted(g, 3.3)])                              # above segment start: undefined


def test_remaining_capacity_monotone_in_voltage():
    q, _ = qv_from_arrays(*synthetic_cycle())
    finite = np.asarray(q)[np.isfinite(q)]
    assert np.all(np.diff(finite) >= -1e-12)


def test_no_discharge_returns_all_nan():
    t = np.arange(0, 10, 1.0)
    q, start_v = qv_from_arrays(t, np.full_like(t, 500.0), np.linspace(3.3, 3.4, t.size))
    assert start_v is None and all(np.isnan(q))


def test_read_qv(tmp_path):
    p = tmp_path / "1-1.json"
    p.write_text(json.dumps({"grid": [2.0, 2.005], "q10": [0.0, 0.001], "q100": [0.0, None], "start_v10": 3.2, "start_v100": 3.19}))
    d = read_qv(p)
    assert np.isnan(d["q100"][1]) and d["start_v10"] == 3.2


def test_final_segment_at_any_constant_current():
    t = np.arange(0, 400, 1.0)
    i = np.r_[np.full(100, -5500.0), np.full(300, -2200.0)]
    v = np.r_[np.linspace(3.3, 3.22, 100), np.linspace(3.18, 2.0, 300)]
    q, start_v, current = qv_from_arrays(t, i, v, with_current=True)
    assert start_v == pytest.approx(3.18) and current == pytest.approx(2200.0)
    assert q[np.searchsorted(np.asarray(GRID), 3.175)] == pytest.approx(2200 * 299 / 3.6e6, rel=0.03)
