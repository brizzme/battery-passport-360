import json
from datetime import date
from pathlib import Path

import numpy as np
import pytest

from fleetgen.model import (GENERATOR_ASSUMPTIONS, SITES, capacity_fraction, daily_effective_efc,
                            life_efc_ref, pack_temperature, resistance_pct)

CAL = Path(__file__).resolve().parents[2] / "apps/api/app/artifacts/fleet-calibration.json"


@pytest.fixture(scope="module")
def cal():
    return json.loads(CAL.read_text())


def test_hotter_day_consumes_more_life(cal):
    assert daily_effective_efc(1, 40, cal)[0] > daily_effective_efc(1, 35, cal)[0]


def test_reference_temperature_is_neutral(cal):
    assert daily_effective_efc(2.0, 35, cal) == (pytest.approx(2.0), "calibrated")


def test_regime_reported(cal):
    assert daily_effective_efc(1, 25, cal)[1] == "extrapolated_below_calibrated_range"


def test_life_ref_positive(cal):
    assert life_efc_ref(cal) > 0


def test_capacity_fraction_monotone_and_extends(cal):
    curve = np.array(cal["hust"]["median_curve"])
    xs = np.linspace(0, 1.3, 60)
    ys = [capacity_fraction(x, curve) for x in xs]
    assert all(a >= b for a, b in zip(ys, ys[1:]))
    assert ys[0] == pytest.approx(1, abs=0.02)
    assert capacity_fraction(1.0, curve) == pytest.approx(curve[-1])
    assert capacity_fraction(1.2, curve) < curve[-1]


def test_resistance_none_without_growth():
    assert resistance_pct(0.9, None) is None


def test_resistance_grows_with_fade():
    assert resistance_pct(0.9, 2.0) == pytest.approx(120.0)


def test_assumptions_exclude_calibrated_quantities():
    assert not any("fade" in k or "life" in k for k in GENERATOR_ASSUMPTIONS)


def test_sites():
    assert [s.site_id for s in SITES] == ["SITE-COLD", "SITE-AMB", "SITE-HOT"]


def test_hot_site_summer_is_hotter_than_cold_site_winter():
    rng = np.random.default_rng(1)
    hot = pack_temperature(SITES[2], date(2026, 7, 20), 3, rng)
    cold = pack_temperature(SITES[0], date(2026, 1, 20), 1, rng)
    assert hot[0] > cold[0] + 20 and hot[1] >= hot[0]


def test_idle_pack_tracks_ambient():
    rng = np.random.default_rng(1)
    mean, _ = pack_temperature(SITES[1], date(2026, 4, 20), 0, rng)
    assert abs(mean - 20) < 8
