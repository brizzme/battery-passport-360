"""Run from any directory with the API project's locked research dependency group."""
import hashlib
import json
import math
import os
import urllib.request
import zipfile
from datetime import datetime, timezone
from io import BytesIO
from itertools import groupby
from pathlib import Path

import numpy as np
from python_calamine import CalamineWorkbook

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "downloads/calce"
OUTPUT = ROOT / "downloads/research"
REPORT = ROOT / "apps/api/app/artifacts/calce-report.json"
TRAIN = ("CS2_35", "CS2_36", "CS2_37")
TEST = "CS2_38"


def observations(archive):
    points = []
    with zipfile.ZipFile(archive) as z:
        for member in sorted(z.namelist()):
            if not member.endswith(".xlsx") or "/~" in member:
                continue
            book = CalamineWorkbook.from_filelike(BytesIO(z.read(member)))
            for sheet in book.sheet_names:
                if not sheet.startswith("Channel"):
                    continue
                rows = iter(book.get_sheet_by_name(sheet).iter_rows())
                header = next(rows)
                cycle, step, cap, voltage, current, timestamp = map(header.index, [
                    "Cycle_Index","Step_Index","Discharge_Capacity(Ah)","Voltage(V)","Current(A)","Date_Time"])
                for index, group in groupby(rows, key=lambda r: r[cycle]):
                    batch = list(group)
                    before = [r for r in batch if r[step] == 6]
                    discharge = [r for r in batch if r[step] == 7]
                    if not before or not discharge or not any(r[step] == 8 for r in batch):
                        continue
                    last = discharge[-1]
                    if not 2.65 <= last[voltage] <= 2.75 or not -1.15 <= last[current] <= -1.05:
                        continue
                    value = last[cap] - before[-1][cap]
                    if not math.isfinite(value) or value <= 0:
                        raise ValueError(f"Unexpected counter change in {member}")
                    points.append(dict(observed_at=last[timestamp].isoformat(), capacity_ah=value,
                                       workbook=member, sheet=sheet, source_cycle=int(index)))
    points.sort(key=lambda p:p["observed_at"])
    unique = {}
    for point in points:
        prior = unique.setdefault(point["observed_at"], point)
        if prior["capacity_ah"] != point["capacity_ah"]:
            raise ValueError("Conflicting observations at one tester timestamp")
    points = list(unique.values())
    if not points:
        raise ValueError("No qualifying discharges")
    return [dict(cycle=i, **p) for i,p in enumerate(points, 1)]


def metrics(y, estimate):
    delta = y - estimate
    return dict(mae_ah=float(np.mean(abs(delta))), rmse_ah=float(np.sqrt(np.mean(delta**2))))


def write(path, obj):
    temp = path.with_suffix(".tmp")
    temp.write_text(json.dumps(obj, indent=2, allow_nan=False) + "\n")
    os.replace(temp, path)


def main():
    RAW.mkdir(parents=True, exist_ok=True)
    OUTPUT.mkdir(parents=True, exist_ok=True)
    manifest = {}
    cells = {}
    for line in (ROOT / "research/calce.sha256").read_text().splitlines():
        expected, name = line.split()
        path = RAW / name
        url = "https://web.calce.umd.edu/batteries/data/" + name
        if not path.exists():
            temp = path.with_suffix(".part")
            urllib.request.urlretrieve(url, temp)
            if hashlib.sha256(temp.read_bytes()).hexdigest() != expected:
                raise ValueError(f"Source checksum changed: {name}")
            temp.replace(path)
        if hashlib.sha256(path.read_bytes()).hexdigest() != expected:
            raise ValueError(f"Checksum mismatch: {name}")
        points = observations(path)
        cells[path.stem] = points
        manifest[path.stem] = dict(url=url, bytes=path.stat().st_size, sha256=expected,
                                   cycles=len(points), first=points[0]["observed_at"], last=points[-1]["observed_at"])
    assert TEST not in TRAIN and set(cells) == set(TRAIN) | {TEST}
    x, y = np.array([(p["cycle"], p["capacity_ah"]) for c in TRAIN for p in cells[c]]).T
    slope, intercept = np.polyfit(x, y, 1)
    xt, yt = np.array([(p["cycle"], p["capacity_ah"]) for p in cells[TEST]]).T
    digest = hashlib.sha256((ROOT / "research/calce.sha256").read_bytes()).hexdigest()
    report = dict(model_run_id="calce-index-ols-v1-"+digest[:12], dataset_digest=digest,
                  source_type="derived", trained_at=datetime.now(timezone.utc).isoformat(),
                  target="Step-7 discharge capacity (Ah)", feature="Ordinal of retained discharge in each cell",
                  train_cells=TRAIN, test_cells=[TEST], train_cycles=len(x), test_cycles=len(xt),
                  intercept_ah=intercept, slope_ah_per_cycle=slope, baseline_mean_ah=float(y.mean()),
                  linear=metrics(yt, slope*xt+intercept), baseline=metrics(yt,y.mean()), sources=manifest)
    for cell, rows in cells.items():
        write(OUTPUT / (cell+".json"), dict(cell_id=cell,source_type="measured_public",
              source_id=cell, dataset_digest=digest, interpretation="Counter difference across a qualifying discharge; cycle is retained observation order.",
              timestamp_basis="Tester clock, timezone unspecified", points=rows))
    write(REPORT,report)
    print(json.dumps(report,indent=2))


if __name__ == "__main__":
    main()
