"""Derive synthetic-fleet calibration parameters from pinned public LFP measurements.

Run: (cd apps/api && uv run --locked --group research python ../../research/calibrate.py)
Requires Docker for the isolated HUST pickle extraction. Never writes partial or default values.
"""
import hashlib
import json
import os
import re
import subprocess
import sys
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).parent))
from fleetcal.aalborg import (duty_profile, efc_per_round, fade_slope_per_efc, fit_arrhenius,  # noqa: E402
                              pulse_resistance_ohm, read_csv_columns, rpt_capacity_ah)
from fleetcal.hust import life_distribution, life_to_80, normalized_curve, read_cell_csv  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
DOWNLOADS = ROOT / "downloads"
PINS = ROOT / "research/calibration.sha256"
OUT = ROOT / "apps/api/app/artifacts/fleet-calibration.json"
UA = {"User-Agent": "Mozilla/5.0 (research-client)"}
CHAMBER_C = {"Cell1": 45, "Cell2": 40, "Cell3": 35}  # Vilsen & Stroe 2024, ageing temperatures
NOMINAL_AH = 180.0
ACCESSED = "2026-11-23"
LIMITATIONS = [
    "Aalborg: three prismatic LFP cells, one per temperature (35/40/45 degC); fade rates are single-cell estimates.",
    "Aalborg: equivalent full cycles per round measured on one ageing round per cell (Round10) and assumed constant; "
    "missing ageing parts would make cumulative EFC an overestimate.",
    "Aalborg reference tests were performed at 25 degC; capacity is the C/4 discharge.",
    "HUST: 77 cylindrical 1.1 Ah LFP cells at 30 degC under 5C fast charging; only relative life spread and curve shape are used.",
    "Cell-level measurements are applied to fictional packs without a validated cell-to-pack model.",
    "Below 35 degC the temperature model is an extrapolation; below 20 degC the 20 degC rate is used.",
]


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def fetch(expected: str, size: int, rel: str, url: str) -> Path:
    path = DOWNLOADS / rel
    if not path.exists():
        path.parent.mkdir(parents=True, exist_ok=True)
        part = path.with_suffix(path.suffix + ".part")
        with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=120) as r, open(part, "wb") as f:
            while block := r.read(1 << 20):
                f.write(block)
        if sha256(part) != expected or part.stat().st_size != size:
            part.unlink()
            raise ValueError(f"Source checksum or size changed: {rel}")
        part.replace(path)
    elif sha256(path) != expected:
        raise ValueError(f"Checksum mismatch: {rel}")
    return path


def extract_hust(archive: Path) -> Path:
    out = DOWNLOADS / "hust_csv"
    report = out / "extract_report.json"
    if not report.exists() or len(json.loads(report.read_text())) != 77:
        out.mkdir(exist_ok=True)
        os.chmod(out, 0o777)
        subprocess.run(["docker", "build", "-q", "-t", "hust-extract", str(ROOT / "research/hust_extract")], check=True)
        subprocess.run(["docker", "run", "--rm", "--network", "none", "--read-only", "--tmpfs", "/tmp",
                        "-v", f"{archive}:/in/our_data.zip:ro", "-v", f"{out}:/out", "hust-extract"], check=True)
    return out


def aalborg(files: dict[str, Path]) -> dict:
    cells, slopes, temps, growth_x, growth_y, duties = [], [], [], [], [], []
    for cell, temp in CHAMBER_C.items():
        ageing = read_csv_columns(files[f"aalborg/{cell}/Round10/Ageing.csv"])
        per_round = efc_per_round(ageing, NOMINAL_AH)
        duty = duty_profile(ageing, NOMINAL_AH)
        duty["measured_mean_temp_c"] = float(np.mean(ageing["Temperature"]))
        duties.append(duty)
        rounds = sorted((int(re.search(r"Round(\d+)", rel).group(1)), path)
                        for rel, path in files.items() if rel.startswith(f"aalborg/{cell}/") and rel.endswith("RPT.csv"))
        if not rounds or rounds[0][0] != 0:
            raise ValueError(f"{cell}: initial reference test (Round00) missing")
        caps, res = [], []
        for number, path in rounds:
            rpt = read_csv_columns(path)
            caps.append((number, rpt_capacity_ah(rpt)))
            res.append(pulse_resistance_ohm(rpt))
        numbers = np.array([n for n, _ in caps], dtype=float)
        frac = np.array([c for _, c in caps]) / caps[0][1]
        efc = numbers * per_round
        slope = fade_slope_per_efc(efc, frac)
        residual = float(np.sqrt(np.mean((frac - (1 + slope * efc)) ** 2)))
        if res[0]:
            for f, r in zip(frac[1:], res[1:]):
                if r:
                    growth_x.append(1 - f)
                    growth_y.append(r / res[0] - 1)
        cells.append({"cell": cell, "temp_c": temp, "measured_mean_temp_c": duty["measured_mean_temp_c"],
                      "rounds_used": len(caps), "efc_per_round": per_round, "initial_capacity_ah": caps[0][1],
                      "final_capacity_frac": float(frac[-1]), "final_efc": float(efc[-1]),
                      "fade_slope_per_efc": slope, "residual_rmse": residual})
        slopes.append(slope)
        temps.append(temp)
    ln_a, ea = fit_arrhenius(temps, slopes)
    gx, gy = np.array(growth_x), np.array(growth_y)
    growth = float(np.sum(gx * gy) / np.sum(gx * gx)) if len(gx) >= 10 else None
    if growth is not None and growth <= 0:
        growth = None
    keys = ["share_discharge", "share_charge", "share_rest", "efc_per_day", "mean_discharge_c_rate", "hours"]
    return {"cells": cells,
            "arrhenius": {"ln_a": ln_a, "ea_over_r": ea, "calibrated_range_c": [35, 45],
                          "form": "|fade per EFC| = exp(ln_a - ea_over_r / (T_degC + 273.15))"},
            "resistance_growth_per_fade": growth, "resistance_points": len(gx),
            "resistance_definition": "20 s 45 A discharge pulse at 50 % SOC, relative to Round00",
            "duty_profile": {k: float(np.mean([d[k] for d in duties])) for k in keys}}


def hust(csv_dir: Path) -> dict:
    lives, curves, excluded = [], [], 0
    for path in sorted(csv_dir.glob("*.csv")):
        cycles, cap = read_cell_csv(path)
        life = life_to_80(cycles, cap)
        if life is None:
            excluded += 1
            continue
        lives.append(life)
        curves.append(normalized_curve(cycles, cap, life))
    if len(lives) + excluded != 77:
        raise ValueError("Expected 77 HUST cells")
    return {"n_cells": len(lives), "n_excluded": excluded, "life_distribution": life_distribution(lives, excluded),
            "median_curve": [float(x) for x in np.median(np.array(curves), axis=0)],
            "curve_definition": "capacity fraction of initial at life fractions linspace(0, 1, 21); life = cycles to 80 %"}


def main():
    pins = [line.split() for line in PINS.read_text().splitlines() if line.strip()]
    files = {rel: fetch(h, int(size), rel, url) for h, size, rel, url in pins}
    manifest_digest = hashlib.sha256(PINS.read_bytes()).hexdigest()
    hust_pin = next(p for p in pins if p[2] == "hust/our_data.zip")
    result = {
        "calibration_version": "fleet-calib-v1-" + manifest_digest[:12],
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "sources": [
            {"id": "hust-lfp-v2", "url": "https://data.mendeley.com/datasets/nsc7hnsg4s/2", "doi": "10.17632/nsc7hnsg4s.2",
             "sha256": hust_pin[0], "bytes": int(hust_pin[1]), "licence": "CC BY 4.0", "accessed": ACCESSED,
             "attribution": "Ma, G. et al. (2022) Real-time personalized health status prediction of lithium-ion "
                            "batteries using deep transfer learning. Energy Environ. Sci. Data: HUST, Mendeley Data."},
            {"id": "aalborg-forklift-v2", "url": "https://data.mendeley.com/datasets/yz4pttm73n/2",
             "files": len(pins) - 1, "bytes": sum(int(p[1]) for p in pins if p[2].startswith("aalborg/")),
             "manifest": "research/calibration.sha256", "manifest_sha256": manifest_digest,
             "licence": "CC BY 4.0", "accessed": ACCESSED,
             "attribution": "Vilsen, S. B. & Stroe, D.-I. (2024) Lithium-ion battery degradation dataset based on a "
                            "realistic forklift operation profile. Data in Brief. Aalborg University, Mendeley Data."},
        ],
        "aalborg": aalborg(files),
        "hust": hust(extract_hust(files["hust/our_data.zip"])),
        "limitations": LIMITATIONS,
    }
    tmp = OUT.with_suffix(".tmp")
    tmp.write_text(json.dumps(result, indent=2, allow_nan=False) + "\n")
    os.replace(tmp, OUT)
    print(json.dumps({k: result[k] for k in ("calibration_version",)} | {
        "aalborg_cells": [(c["cell"], c["temp_c"], round(c["fade_slope_per_efc"], 7), c["rounds_used"],
                           round(c["final_capacity_frac"], 3)) for c in result["aalborg"]["cells"]],
        "arrhenius": result["aalborg"]["arrhenius"], "growth": result["aalborg"]["resistance_growth_per_fade"],
        "hust_median_life": result["hust"]["life_distribution"]["median"]}, indent=1))


if __name__ == "__main__":
    main()
