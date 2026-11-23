"""Run the HUST early-cycle life comparison and write committed artifacts.

Run: (cd apps/api && uv run --locked --group research python ../../research/life_model.py)
Needs downloads/hust_csv (from research/calibrate.py and the isolated extractor). Writes:
  apps/api/app/artifacts/hust-life-report.json, apps/api/app/artifacts/hust-curves.json
"""
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).parent))
from fleetcal.hust import _initial, read_cell_csv  # noqa: E402
from lifemodel.evaluate import _fit, evaluate, metrics  # noqa: E402
from lifemodel.features import FEATURES_CAPACITY, FEATURES_VOLTAGE, HORIZON, feature_table  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "downloads/hust_csv"
ART = ROOT / "apps/api/app/artifacts"
MODELS = {
    "baseline": ("Training mean", "baseline", None),
    "voltage_variance": ("ΔQ(V) variance only", "linear", ["log_var"]),
    "capacity": ("Capacity features", "enet", FEATURES_CAPACITY),
    "full": ("Capacity + ΔQ(V) features", "enet", FEATURES_CAPACITY + FEATURES_VOLTAGE),
}


def digest(paths) -> str:
    h = hashlib.sha256()
    for p in sorted(paths):
        h.update(p.name.encode())
        h.update(p.read_bytes())
    return h.hexdigest()


def main():
    t = feature_table(DATA)
    names = FEATURES_CAPACITY + FEATURES_VOLTAGE
    X = np.hstack([t["X_capacity"], t["X_voltage"]])
    y = np.log10(t["life"])
    groups = np.array(t["batches"])
    data_digest = digest(list(DATA.glob("*.csv")) + list((DATA / "qv").glob("*.json")))
    results, cells = {}, [{"id": i, "batch": b, "life": int(l)} for i, b, l in zip(t["ids"], t["batches"], t["life"])]
    for key, (label, kind, feats) in MODELS.items():
        cols = [names.index(f) for f in (feats or names[:1])]
        r = evaluate(X[:, cols], y, groups, kind)
        pred, lo, hi = 10 ** r["pred"], 10 ** r["lo"], 10 ** r["hi"]
        inside = (lo <= t["life"]) & (t["life"] <= hi)
        per_batch = {int(b): float(np.mean(inside[groups == b])) for b in sorted(set(t["batches"]))}
        fold_mae = [f["mae"] for f in r["folds"]]
        results[key] = {"label": label, "kind": kind, "features": feats or [], **metrics(t["life"], pred),
                        "interval_coverage": r["coverage"], "interval_mean_width": float(np.mean(hi - lo)),
                        "batch_coverage": per_batch, "fold_mae_range": [min(fold_mae), max(fold_mae)],
                        "folds": r["folds"]}
        for c, p, a, b in zip(cells, pred, lo, hi):
            c[key] = {"pred": round(float(p), 1), "lo": round(float(a), 1), "hi": round(float(b), 1)}
    full = _fit("enet", X, y, groups)
    enet = full.named_steps["elasticnetcv"]
    report = {
        "run_id": "hust-life-v1-" + data_digest[:12], "generated_at": datetime.now(timezone.utc).isoformat(),
        "source_type": "derived",
        "target": "log10 of cycle life; life = first cycle whose centred 5-cycle median capacity falls below 80 % of the median of cycles 2–6",
        "horizon_cycles": HORIZON, "n_cells": len(cells), "n_batches": int(len(set(t["batches"]))),
        "split": "outer leave-one-batch-out (cell-id prefix 1–10); inner GroupKFold(5) by batch for elastic-net strength and conformal calibration; every cell has a unique discharge protocol",
        "intervals": "80 % CV-residual, conformal-style intervals: the k-th smallest inner out-of-fold absolute residual (log10 space) around each outer prediction; no finite-sample guarantee under batch shift, empirical coverage reported",
        "voltage_window_v": [float(t["grid"][0]), float(t["grid"][-1])],
        "voltage_window_note": "Fixed from all 77 cells' curve coverage (uses no life labels); the same window serves every fold.",
        "voltage_feature_note": "Adaptation of Severson et al. 2019: ΔQ100−10(V) of capacity remaining to the 2.0 V cut-off along the final constant-current stage (measured 2.2 A for every cell), not their constant 4C discharge.",
        "life_summary": {"min": int(t["life"].min()), "median": float(np.median(t["life"])), "max": int(t["life"].max())},
        "models": results, "cells": cells,
        "interpretation": {"note": "Full model refit on all 77 cells for coefficient reading only; not used for any reported metric.",
                           "standardised_coefficients": dict(zip(names, (round(float(c), 5) for c in enet.coef_))),
                           "alpha": float(enet.alpha_), "l1_ratio": float(enet.l1_ratio_)},
        "data": {"dataset": "HUST LFP (Ma et al. 2022), Mendeley Data 10.17632/nsc7hnsg4s.2, CC BY 4.0",
                 "digest": data_digest, "features": names},
    }
    (ART / "hust-life-report.json").write_text(json.dumps(report, indent=1, allow_nan=False) + "\n")
    curves = {"source_type": "measured_public", "dataset": report["data"]["dataset"],
              "delta_q_grid_v": [round(float(v), 3) for v in t["grid"][::4]], "cells": {}}
    for i, cell in enumerate(t["ids"]):
        cyc, cap = read_cell_csv(DATA / f"{cell}.csv")
        idx = np.unique(np.linspace(0, len(cyc) - 1, 60).round().astype(int))
        curves["cells"][cell] = {"initial_ah": round(_initial(cyc, cap), 5),
                                 "cycles": [int(c) for c in cyc[idx]], "capacity_ah": [round(float(q), 4) for q in cap[idx]],
                                 "delta_q_ah": [round(float(d), 6) for d in t["delta_q"][i][::4]]}
    (ART / "hust-curves.json").write_text(json.dumps(curves, allow_nan=False) + "\n")
    print(json.dumps({k: {m: round(v[m], 1) for m in ("mae", "rmse", "mape")} | {"coverage": round(v["interval_coverage"], 2)}
                      for k, v in results.items()}, indent=1))


if __name__ == "__main__":
    main()
