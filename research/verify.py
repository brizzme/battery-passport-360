"""Independently recompute the reported scores from the held-out local observations."""
import json
import math
from pathlib import Path
from statistics import mean

root = Path(__file__).resolve().parents[1]
r = json.loads((root/"apps/api/app/artifacts/calce-report.json").read_text())
assert set(r["train_cells"]).isdisjoint(r["test_cells"])
for split in ("train", "test"):
    records = []
    for cell in r[split+"_cells"]:
        series = json.loads((root/"downloads/research"/(cell+".json")).read_text())
        assert series["dataset_digest"] == r["dataset_digest"]
        records.extend(series["points"])
    assert len(records) == r[split+"_cycles"]
    if split == "train":
        assert math.isclose(mean(p["capacity_ah"] for p in records),r["baseline_mean_ah"])
    else:
        for name in ("linear", "baseline"):
            errors = [p["capacity_ah"] - (r["intercept_ah"]+r["slope_ah_per_cycle"]*p["cycle"]
                      if name=="linear" else r["baseline_mean_ah"]) for p in records]
            assert math.isclose(mean(map(abs, errors)), r[name]["mae_ah"])
            assert math.isclose(math.sqrt(mean(e*e for e in errors)), r[name]["rmse_ah"])
print("Whole-cell split, counts, baseline and held-out metrics verified.")
