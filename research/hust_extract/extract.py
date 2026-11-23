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
