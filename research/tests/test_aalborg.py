import math
from pathlib import Path

import numpy as np
import pytest

from fleetcal.aalborg import (duty_profile, efc_per_round, fade_slope_per_efc, fit_arrhenius,
                              pulse_resistance_ohm, rate_at, read_csv_columns, rpt_capacity_ah)

FIX = Path(__file__).parent / "fixtures"


@pytest.fixture(scope="module")
def rpt():
    return read_csv_columns(FIX / "aalborg_rpt_small.csv")


@pytest.fixture(scope="module")
def ageing():
    return read_csv_columns(FIX / "aalborg_ageing_small.csv")


def test_rpt_capacity_integrates_longest_c4_segment(rpt):
    assert rpt_capacity_ah(rpt) == pytest.approx(45.0, rel=1e-3)


def test_pulse_resistance_third_discharge_pulse(rpt):
    assert pulse_resistance_ohm(rpt) == pytest.approx(0.002, rel=1e-3)


def test_pulse_resistance_none_when_pulse_missing(rpt):
    assert pulse_resistance_ohm(rpt, soc_order_index=7) is None


def test_missing_c4_segment_raises():
    flat = {"Time": np.arange(10.0), "Current": np.zeros(10), "Voltage": np.full(10, 3.3)}
    with pytest.raises(ValueError):
        rpt_capacity_ah(flat)


def test_efc_per_round(ageing):
    assert efc_per_round(ageing, nominal_ah=180.0) == pytest.approx(2.0, rel=1e-3)


def test_duty_profile(ageing):
    d = duty_profile(ageing)
    assert d["share_discharge"] == pytest.approx(0.4, abs=1e-3)
    assert d["share_charge"] == pytest.approx(0.4, abs=1e-3)
    assert d["share_rest"] == pytest.approx(0.2, abs=1e-3)
    assert d["efc_per_day"] == pytest.approx(4.8, rel=1e-3)
    assert d["mean_discharge_c_rate"] == pytest.approx(0.5, rel=1e-3)


def test_fade_slope_through_origin():
    efc = np.array([0.0, 100.0, 200.0])
    assert fade_slope_per_efc(efc, 1 - 1e-4 * efc) == pytest.approx(-1e-4)


def test_arrhenius_recovers_known_rates():
    ln_a, e = 5.0, 4000.0
    temps = [35, 40, 45]
    slopes = [math.exp(ln_a - e / (t + 273.15)) for t in temps]
    assert fit_arrhenius(temps, slopes) == pytest.approx((ln_a, e), rel=1e-6)


@pytest.mark.parametrize("t,regime", [(40, "calibrated"), (35, "calibrated"), (45, "calibrated"),
                                      (25, "extrapolated_below_calibrated_range"), (5, "clamped_low"),
                                      (50, "clamped_high")])
def test_regimes(t, regime):
    assert rate_at(t, 5.0, 4000.0)[1] == regime


def test_clamped_low_uses_20c_rate():
    assert rate_at(5, 5.0, 4000.0)[0] == rate_at(20, 5.0, 4000.0)[0]


def test_clamped_high_uses_45c_rate():
    assert rate_at(50, 5.0, 4000.0)[0] == rate_at(45, 5.0, 4000.0)[0]
