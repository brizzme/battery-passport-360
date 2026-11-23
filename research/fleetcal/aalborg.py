"""Parse Aalborg forklift-profile LFP files (Vilsen & Stroe, Data in Brief 2024, CC BY 4.0).

Columns as published: Cell, Round, [Part,] Time (s), Current (A, charge positive), Voltage (V),
Energy (Wh), Temperature (degC).
"""
from pathlib import Path

import numpy as np

C4_A = 45.0
REST_A = 0.5
CAL_LOW, CAL_HIGH, EXTRAP_LOW = 35.0, 45.0, 20.0


def read_csv_columns(path: Path) -> dict[str, np.ndarray]:
    data = np.genfromtxt(path, delimiter=",", names=True)
    return {name: np.asarray(data[name], dtype=float) for name in data.dtype.names}


def _segments(mask: np.ndarray) -> list[tuple[int, int]]:
    """Half-open index ranges [s, e) where mask is True."""
    edges = np.diff(np.r_[0, mask.astype(int), 0])
    return list(zip(np.flatnonzero(edges == 1), np.flatnonzero(edges == -1)))


def _step_dt(t: np.ndarray) -> np.ndarray:
    dt = np.diff(t, prepend=t[0])
    dt[dt < 0] = 0.0  # time restarts between ageing parts
    return dt


def rpt_capacity_ah(df: dict[str, np.ndarray]) -> float:
    """Ah delivered in the longest contiguous C/4 (-45 A) discharge of a reference test."""
    t, i = df["Time"], df["Current"]
    dt = _step_dt(t)
    segs = [(s, e) for s, e in _segments(np.abs(i + C4_A) < 2.0) if s > 0]
    if not segs:
        raise ValueError("No C/4 discharge segment in reference test")
    s, e = max(segs, key=lambda se: t[se[1] - 1] - t[se[0] - 1])
    if t[e - 1] - t[s - 1] < 1800:
        raise ValueError("C/4 discharge segment too short for a capacity test")
    return float(np.sum(np.abs(i[s:e]) * dt[s:e]) / 3600)


def pulse_resistance_ohm(df: dict[str, np.ndarray], soc_order_index: int = 2) -> float | None:
    """(V before - V at end) / 45 A for the n-th 20 s C/4 discharge pulse (order 90/70/50/30 % SOC)."""
    t, i, v = df["Time"], df["Current"], df["Voltage"]
    pulses = [(s, e) for s, e in _segments(np.abs(i + C4_A) < 2.0)
              if s > 0 and 15 <= t[e - 1] - t[s - 1] <= 25]
    if soc_order_index >= len(pulses):
        return None
    s, e = pulses[soc_order_index]
    return float((v[s - 1] - v[e - 1]) / C4_A)


def efc_per_round(ageing: dict[str, np.ndarray], nominal_ah: float = 180.0) -> float:
    dt = _step_dt(ageing["Time"])
    return float(np.sum(np.abs(ageing["Current"]) * dt) / 3600 / (2 * nominal_ah))


def duty_profile(ageing: dict[str, np.ndarray], nominal_ah: float = 180.0) -> dict:
    i = ageing["Current"]
    dt = _step_dt(ageing["Time"])
    total = float(np.sum(dt))
    dis, chg = i < -REST_A, i > REST_A
    return {
        "share_discharge": float(np.sum(dt[dis]) / total),
        "share_charge": float(np.sum(dt[chg]) / total),
        "share_rest": float(np.sum(dt[~dis & ~chg]) / total),
        "efc_per_day": efc_per_round(ageing, nominal_ah) / (total / 86400),
        "mean_discharge_c_rate": float(np.sum(-i[dis] * dt[dis]) / np.sum(dt[dis]) / nominal_ah),
        "hours": total / 3600,
    }


def fade_slope_per_efc(efc: np.ndarray, capacity_frac: np.ndarray) -> float:
    """Least-squares slope of (capacity_frac - 1) vs EFC, constrained through (0, 1)."""
    efc = np.asarray(efc, dtype=float)
    return float(np.sum(efc * (np.asarray(capacity_frac) - 1)) / np.sum(efc * efc))


def fit_arrhenius(temps_c: list[float], slopes: list[float]) -> tuple[float, float]:
    """Fit ln|slope| = ln_a - ea_over_r / T[K]; returns (ln_a, ea_over_r)."""
    inv_t = 1 / (np.asarray(temps_c, dtype=float) + 273.15)
    gradient, intercept = np.polyfit(inv_t, np.log(np.abs(slopes)), 1)
    return float(intercept), float(-gradient)


def rate_at(temp_c: float, ln_a: float, ea_over_r: float) -> tuple[float, str]:
    """Fade rate magnitude per EFC and the temperature regime label."""
    if temp_c > CAL_HIGH:
        regime, used = "clamped_high", CAL_HIGH
    elif temp_c >= CAL_LOW:
        regime, used = "calibrated", temp_c
    elif temp_c >= EXTRAP_LOW:
        regime, used = "extrapolated_below_calibrated_range", temp_c
    else:
        regime, used = "clamped_low", EXTRAP_LOW
    return float(np.exp(ln_a - ea_over_r / (used + 273.15))), regime
