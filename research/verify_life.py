"""Independently recompute every reported metric from the committed per-cell predictions."""
import json
import math
from pathlib import Path
from statistics import mean

r = json.loads((Path(__file__).resolve().parents[1] / "apps/api/app/artifacts/hust-life-report.json").read_text())
assert r["n_cells"] == len(r["cells"]) == 77
for key, m in r["models"].items():
    err = [c[key]["pred"] - c["life"] for c in r["cells"]]
    assert math.isclose(mean(abs(e) for e in err), m["mae"], abs_tol=0.1), key
    assert math.isclose(math.sqrt(mean(e * e for e in err)), m["rmse"], abs_tol=0.1), key
    assert math.isclose(100 * mean(abs(e) / c["life"] for e, c in zip(err, r["cells"])), m["mape"], abs_tol=0.01), key
    inside = mean(1.0 if c[key]["lo"] - 0.1 <= c["life"] <= c[key]["hi"] + 0.1 else 0.0 for c in r["cells"])
    assert math.isclose(inside, m["interval_coverage"], abs_tol=0.02), key
    for f in m["folds"]:
        assert not set(f["train_groups"]) & set(f["test_groups"]), key
    assert sorted(g for f in m["folds"] for g in f["test_groups"]) == list(range(1, 11)), key
print("Per-cell predictions reproduce MAE, RMSE, MAPE and coverage for", ", ".join(r["models"]), "; folds are batch-disjoint.")
