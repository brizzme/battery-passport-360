"""Life and fade-shape statistics from HUST LFP cells (Ma et al. 2022, CC BY 4.0).

Input is the CSV written by the isolated extractor (research/hust_extract), never the raw pickles.
"""
from pathlib import Path

import numpy as np

KNOTS = 21


def read_cell_csv(path: Path) -> tuple[np.ndarray, np.ndarray]:
    data = np.genfromtxt(path, delimiter=",", names=True, ndmin=1)
    return data["cycle"].astype(int), data["discharge_ah"].astype(float)


def _smoothed(cap: np.ndarray) -> np.ndarray:
    """Centred 5-cycle rolling median (edges use the available window)."""
    n = len(cap)
    return np.array([np.median(cap[max(0, k - 2):min(n, k + 3)]) for k in range(n)])


def _initial(cycles: np.ndarray, cap: np.ndarray) -> float:
    window = cap[(cycles >= 2) & (cycles <= 6)]
    return float(np.median(window if len(window) else cap[:5]))


def life_to_80(cycles: np.ndarray, cap: np.ndarray) -> int | None:
    """First cycle whose smoothed capacity falls below 80 % of initial capacity."""
    below = np.flatnonzero(_smoothed(cap) < 0.8 * _initial(cycles, cap))
    return int(cycles[below[0]]) if len(below) else None


def normalized_curve(cycles: np.ndarray, cap: np.ndarray, life: int, knots: int = KNOTS) -> np.ndarray:
    """Capacity fraction (of initial) at life fractions linspace(0, 1, knots)."""
    frac = _smoothed(cap) / _initial(cycles, cap)
    return np.interp(np.linspace(0, 1, knots) * life, cycles, frac)


def life_distribution(lives: list[int], n_excluded: int = 0) -> dict:
    lives_arr = np.asarray(lives, dtype=float)
    median = float(np.median(lives_arr))
    qs = range(5, 100, 5)
    return {
        "median": median,
        "quantiles": {str(q): float(np.percentile(lives_arr / median, q)) for q in qs},
        "lognormal_sigma": float(np.std(np.log(lives_arr), ddof=1)),
        "n": len(lives),
        "n_excluded": n_excluded,
    }
