"""Early-cycle features for HUST cells. Every feature reads cycles <= 100 only.

Voltage features adapt Severson et al. (2019): Delta Q_100-10(V) of the capacity remaining to the cut-off along
each cell's final constant-current discharge stage (measured 2.2 A for every HUST cell).
"""
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from fleetcal.hust import life_to_80, read_cell_csv, read_qv  # noqa: E402

HORIZON = 100
FLOOR = 1e-12
FEATURES_CAPACITY = ["q2", "max_minus_q2", "slope_91_100", "intercept_91_100"]
FEATURES_VOLTAGE = ["log_var", "log_abs_min", "mean"]


def capacity_features(cycles: np.ndarray, cap: np.ndarray) -> dict[str, float]:
    keep = np.asarray(cycles) <= HORIZON
    c, q = np.asarray(cycles)[keep], np.asarray(cap, dtype=float)[keep]
    if c.size < HORIZON or c.max() < HORIZON:
        raise ValueError("At least 100 cycles are required")
    q2 = float(q[c == 2][0])
    window = (c >= 91) & (c <= 100)
    slope, intercept = np.polyfit(c[window], q[window], 1)
    return {"q2": q2, "max_minus_q2": float(q[c >= 2].max() - q2),
            "slope_91_100": float(slope), "intercept_91_100": float(intercept)}


def common_grid(qvs: list[dict]) -> np.ndarray:
    """Boolean mask of grid points where every cell has both cycle-10 and cycle-100 values."""
    mask = np.ones_like(qvs[0]["grid"], dtype=bool)
    for qv in qvs:
        mask &= np.isfinite(qv["q10"]) & np.isfinite(qv["q100"])
    return mask


def delta_q(qv: dict, mask: np.ndarray) -> np.ndarray:
    return np.asarray(qv["q100"])[mask] - np.asarray(qv["q10"])[mask]


def voltage_features(dq: np.ndarray) -> dict[str, float]:
    return {"log_var": float(np.log10(max(np.var(dq), FLOOR))),
            "log_abs_min": float(np.log10(max(abs(np.min(dq)), FLOOR))),
            "mean": float(np.mean(dq))}


def feature_table(csv_dir: Path) -> dict:
    """Load every cell; returns ids, batches, voltage/capacity matrices, life (cycles) and the shared grid."""
    ids = sorted((p.stem for p in csv_dir.glob("*.csv")), key=lambda s: tuple(int(x) for x in s.split("-")))
    qvs = [read_qv(csv_dir / "qv" / f"{i}.json") for i in ids]
    mask = common_grid(qvs)
    if mask.sum() < 50:
        raise ValueError("Shared voltage window too small")
    xv, xc, life, dqs = [], [], [], []
    for cell, qv in zip(ids, qvs):
        cycles, cap = read_cell_csv(csv_dir / f"{cell}.csv")
        lf = life_to_80(cycles, cap)
        if lf is None or lf <= HORIZON:
            raise ValueError(f"{cell}: life must exceed the 100-cycle horizon")
        dq = delta_q(qv, mask)
        dqs.append(dq)
        xv.append(list(voltage_features(dq).values()))
        xc.append(list(capacity_features(cycles, cap).values()))
        life.append(lf)
    return {"ids": ids, "batches": [int(i.split("-")[0]) for i in ids], "X_voltage": np.array(xv),
            "X_capacity": np.array(xc), "life": np.array(life, dtype=float), "grid": qvs[0]["grid"][mask],
            "delta_q": np.array(dqs)}
