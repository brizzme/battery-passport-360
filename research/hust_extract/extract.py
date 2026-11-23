"""Runs ONLY inside the isolated container. Reads /in/our_data.zip, writes /out/<cell>.csv.

Each pickle holds {cell_id: {"data": {cycle: DataFrame[Current (mA), Time (s), Voltage (V)]}}}
(structure per Microsoft BatteryML preprocess_HUST.py). Per cycle, discharge Ah is the integral of
discharge current over time. The sign convention is checked and reported, not assumed.
"""
import json
import pickle
import sys
import zipfile
from pathlib import Path

import numpy as np

OUT = Path("/out")
GRID = [round(2.0 + 0.005 * k, 3) for k in range(281)]  # 2.000 ... 3.400 V
ONE_C_TOL_MA = 110.0  # samples below -110 mA count as discharge


def qv_from_arrays(t, i, v, with_current=False):
    """Capacity remaining to the cut-off along each cycle's final constant-current discharge segment, on GRID.

    The segment is the contiguous run of discharge samples, ending at the last one, whose current stays within
    5 % of the final current. Returns (values on GRID, NaN above the segment's start voltage; start voltage or
    None[; segment current in mA]).
    """
    t, i, v = (np.asarray(a, dtype=float) for a in (t, i, v))
    discharge = np.flatnonzero(i < -ONE_C_TOL_MA)
    if not discharge.size:
        return ([float("nan")] * len(GRID), None, None) if with_current else ([float("nan")] * len(GRID), None)
    end = int(discharge[-1])
    level = i[end]
    same = np.abs(i - level) < 0.05 * abs(level)
    start = end
    while start > 0 and same[start - 1]:
        start -= 1
    if end - start < 10:
        return ([float("nan")] * len(GRID), None, None) if with_current else ([float("nan")] * len(GRID), None)
    ts, cs, vs = t[start:end + 1], -i[start:end + 1], v[start:end + 1]
    dt = np.diff(ts, prepend=ts[0])
    dt[dt < 0] = 0.0
    remaining = (np.sum(cs * dt) - np.cumsum(cs * dt)) / 3.6e6
    v_mono = np.minimum.accumulate(vs)
    x, y = v_mono[::-1], remaining[::-1]
    x, keep = np.unique(x, return_index=True)
    y = y[keep]
    grid = np.asarray(GRID)
    out = np.interp(grid, x, y, left=0.0, right=np.nan)
    out[grid > x[-1]] = np.nan
    values = [float(q) for q in out]
    return (values, float(vs[0]), float(-level)) if with_current else (values, float(vs[0]))


def cycle_ah(frame):
    t = frame["Time (s)"].to_numpy(dtype=float)
    i = frame["Current (mA)"].to_numpy(dtype=float)
    dt = np.diff(t, prepend=t[0])
    dt[dt < 0] = 0.0
    return float(np.sum(np.clip(i, 0, None) * dt) / 3.6e6), float(np.sum(np.clip(-i, 0, None) * dt) / 3.6e6)


def main():
    report = {}
    with zipfile.ZipFile("/in/our_data.zip") as archive:
        members = sorted(m for m in archive.namelist() if m.endswith(".pkl"))
        if not members:
            sys.exit("no .pkl members found")
        for member in members:
            cell = Path(member).stem
            obj = pickle.loads(archive.read(member))
            cycles = obj[cell]["data"]
            rows = []
            pos_total = neg_total = 0.0
            for number in sorted(cycles):
                pos, neg = cycle_ah(cycles[number])
                pos_total += pos
                neg_total += neg
                rows.append((int(number), pos, neg))
            qv = {"grid": GRID}
            for label, number in (("10", 10), ("100", 100)):
                frame = cycles.get(number)
                if frame is None:
                    qv["q" + label], qv["start_v" + label], qv["current_ma" + label] = [None] * len(GRID), None, None
                    continue
                q, start_v, current = qv_from_arrays(frame["Time (s)"].to_numpy(), frame["Current (mA)"].to_numpy(),
                                                     frame["Voltage (V)"].to_numpy(), with_current=True)
                qv["current_ma" + label] = current
                qv["q" + label] = [None if q_ != q_ else round(q_, 6) for q_ in q]
                qv["start_v" + label] = start_v
            (OUT / "qv").mkdir(exist_ok=True)
            (OUT / "qv" / f"{cell}.json").write_text(json.dumps(qv))
            # Discharge is the direction ending each cycle at low voltage; record which sign that is.
            last = cycles[sorted(cycles)[-1]]
            low_v_current = float(last["Current (mA)"].to_numpy()[np.argmin(last["Voltage (V)"].to_numpy())])
            discharge_negative = low_v_current < 0
            with open(OUT / f"{cell}.csv", "w") as f:
                f.write("cycle,discharge_ah\n")
                for number, pos, neg in rows:
                    f.write(f"{number},{(neg if discharge_negative else pos):.6f}\n")
            report[cell] = {"cycles": len(rows), "discharge_negative": discharge_negative,
                            "charge_ah_total": round(pos_total if discharge_negative else neg_total, 3),
                            "discharge_ah_total": round(neg_total if discharge_negative else pos_total, 3)}
    (OUT / "extract_report.json").write_text(json.dumps(report, indent=1))
    print(json.dumps({"cells": len(report)}))


if __name__ == "__main__":
    main()
