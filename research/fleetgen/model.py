"""Daily model for fictional forklift packs.

Calibrated quantities (fade per EFC vs temperature, curve shape, life spread, resistance growth) come
from fleet-calibration.json. Everything in GENERATOR_ASSUMPTIONS is a hand-set, labelled assumption.
"""
import math
import sys
from dataclasses import dataclass
from datetime import date
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from fleetcal.aalborg import rate_at  # noqa: E402

REFERENCE_C = 35.0


@dataclass(frozen=True)
class Site:
    site_id: str
    name: str
    ambient_mean_c: float
    seasonal_amp_c: float


SITES = (
    Site("SITE-COLD", "Cold store", 5, 2),
    Site("SITE-AMB", "Ambient warehouse", 20, 5),
    Site("SITE-HOT", "Hot dock", 30, 6),
)

GENERATOR_ASSUMPTIONS: dict[str, float] = {
    "reference_shifts_for_aalborg_profile": 3,   # Aalborg profile treated as continuous 3-shift duty
    "temp_rise_per_shift_c": 3.0,
    "pack_temp_noise_c": 1.5,
    "max_over_mean_per_shift_c": 2.5,
    "seasonal_peak_day_of_year": 201,
    "efc_noise_rel": 0.15,
    "weekend_activity_share": 0.3,
    "opportunity_propensity_min": 0.1,
    "opportunity_propensity_max": 0.8,
    "soc_max_pct": 100,
    "soc_min_mean_pct": 30,
    "soc_min_sd_pct": 10,
    "soc_min_opportunity_lift_pct": 25,
    "over_temperature_threshold_c": 45,
    "deep_discharge_threshold_pct": 10,
    "bms_comm_loss_daily_rate": 0.004,
}


def pack_temperature(site: Site, day: date, shifts: int, rng: np.random.Generator) -> tuple[float, float]:
    a = GENERATOR_ASSUMPTIONS
    phase = 2 * math.pi * (day.timetuple().tm_yday - a["seasonal_peak_day_of_year"]) / 365.25
    ambient = site.ambient_mean_c + site.seasonal_amp_c * math.cos(phase)
    mean = ambient + a["temp_rise_per_shift_c"] * shifts + rng.normal(0, a["pack_temp_noise_c"])
    peak = mean + a["max_over_mean_per_shift_c"] * shifts + abs(rng.normal(0, a["pack_temp_noise_c"]))
    return float(mean), float(peak)


def _arrhenius(cal: dict) -> tuple[float, float]:
    arr = cal["aalborg"]["arrhenius"]
    return arr["ln_a"], arr["ea_over_r"]


def daily_effective_efc(efc: float, temp_c: float, cal: dict) -> tuple[float, str]:
    """EFC expressed at the 35 degC reference rate, plus the temperature regime used."""
    rate, regime = rate_at(temp_c, *_arrhenius(cal))
    return efc * rate / rate_at(REFERENCE_C, *_arrhenius(cal))[0], regime


def life_efc_ref(cal: dict) -> float:
    """EFC to 80 % capacity at 35 degC under the forklift profile (linear Aalborg fit)."""
    return 0.2 / rate_at(REFERENCE_C, *_arrhenius(cal))[0]


def capacity_fraction(effective_life_used: float, median_curve: np.ndarray) -> float:
    curve = np.asarray(median_curve, dtype=float)
    xs = np.linspace(0, 1, len(curve))
    if effective_life_used <= 1:
        return float(np.interp(effective_life_used, xs, curve))
    slope = (curve[-1] - curve[-2]) / (xs[-1] - xs[-2])
    return float(curve[-1] + slope * (effective_life_used - 1))


def resistance_pct(cap_frac: float, growth: float | None) -> float | None:
    return None if growth is None else 100 * (1 + growth * (1 - cap_frac))
