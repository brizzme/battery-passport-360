"""Generate the deterministic synthetic fleet seed from committed calibration. No downloads needed.

Run: (cd apps/api && uv run --locked --group research python ../../research/generate_fleet.py)
"""
import csv
import gzip
import hashlib
import io
import json
import sys
from datetime import date, timedelta
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).parent))
from fleetgen.model import (GENERATOR_ASSUMPTIONS, SITES, capacity_fraction, daily_effective_efc,  # noqa: E402
                            life_efc_ref, pack_temperature, resistance_pct)

ROOT = Path(__file__).resolve().parents[1]
CAL = ROOT / "apps/api/app/artifacts/fleet-calibration.json"
OUT = ROOT / "db/seed/fleet_v2"
GENERATOR_VERSION = "fleet-gen-v1"
SEED = 20261123
START, END = date(2024, 11, 1), date(2026, 10, 31)
SITE_WEIGHTS = (0.2, 0.5, 0.3)
SHIFT_CHOICES, SHIFT_WEIGHTS = (1, 2, 3), (0.3, 0.45, 0.25)
TEMP_BINS = np.arange(-10, 65, 5)
SOC_BINS = np.arange(0, 101, 20)
PLANTED = {
    "BAT-DEMO-007": {"site_id": "SITE-HOT", "shifts": 3, "life_quantile": "5", "commissioned": "2023-01-15",
                     "note": "Fast fader: hot site, 3 shifts, HUST 5th-percentile life multiplier"},
    "BAT-DEMO-013": {"site_id": "SITE-HOT", "shifts": 3, "life_quantile": "50",
                     "cooling_fault": ("2026-10-01", "2026-10-31"),
                     "note": "Fictional cooling fault in October 2026: repeated over-temperature events"},
    "BAT-DEMO-042": {"idle": ("2026-08-01", "2026-09-30"), "note": "Idle (parked) August-September 2026"},
    "BAT-DEMO-024": {"site_id": "SITE-AMB", "shifts": 2, "life_quantile": "50",
                     "note": "Ordinary health; passport evidence gaps unchanged"},
}
COLUMNS = {
    "sites": ["site_id", "name", "ambient_mean_c", "seasonal_amp_c"],
    "profiles": ["battery_id", "chemistry", "rated_kwh", "site_id", "commissioned_on", "shifts", "life_multiplier",
                 "opportunity_propensity", "efc_before_window"],
    "daily": ["battery_id", "day", "efc", "throughput_kwh", "soc_min_pct", "soc_max_pct", "temp_mean_c",
              "temp_max_c", "charge_sessions", "opportunity_charges", "capacity_pct", "resistance_pct", "temp_regime"],
    "histograms": ["battery_id", "month", "kind", "bin_lower", "bin_upper", "hours"],
    "events": ["battery_id", "observed_at", "kind", "detail"],
}
FILES = {"sites": "sites.csv", "profiles": "profiles.csv", "daily": "daily.csv.gz",
         "histograms": "histograms.csv.gz", "events": "events.csv.gz"}


def _days(start: date, end: date):
    for k in range((end - start).days + 1):
        yield start + timedelta(days=k)


def _spread(hist: dict, key: tuple, lo: float, hi: float, hours: float, edges: np.ndarray) -> None:
    """Add `hours` spread uniformly over [lo, hi] into histogram bins (point mass if lo == hi)."""
    if hours <= 0:
        return
    lo, hi = float(np.clip(lo, edges[0], edges[-1] - 1e-6)), float(np.clip(hi, edges[0], edges[-1] - 1e-6))
    for a, b in zip(edges[:-1], edges[1:]):
        share = (1.0 if a <= lo < b else 0.0) if hi <= lo else max(0.0, min(b, hi) - max(a, lo)) / (hi - lo)
        if share > 0:
            hist[key + (float(a), float(b))] = hist.get(key + (float(a), float(b)), 0.0) + hours * share


def generate(cal: dict, seed: int = SEED) -> dict[str, list[dict]]:
    a = GENERATOR_ASSUMPTIONS
    rng = np.random.default_rng(seed)
    quantiles = cal["hust"]["life_distribution"]["quantiles"]
    sigma = cal["hust"]["life_distribution"]["lognormal_sigma"]
    curve = np.array(cal["hust"]["median_curve"])
    growth = cal["aalborg"]["resistance_growth_per_fade"]
    life_ref = life_efc_ref(cal)
    efc_per_shift = cal["aalborg"]["duty_profile"]["efc_per_day"] / a["reference_shifts_for_aalborg_profile"]
    sites = {s.site_id: s for s in SITES}
    tables = {k: [] for k in COLUMNS}
    tables["sites"] = [{"site_id": s.site_id, "name": s.name, "ambient_mean_c": s.ambient_mean_c,
                        "seasonal_amp_c": s.seasonal_amp_c} for s in SITES]
    hist: dict = {}
    span = (date(2025, 6, 30) - date(2023, 1, 1)).days
    for index in range(1, 101):
        battery_id = f"BAT-DEMO-{index:03d}"
        plant = PLANTED.get(battery_id, {})
        chemistry = "lead-acid" if index % 5 == 0 else "LFP"
        rated_kwh = 16 + 4 * (index % 8)
        site = sites[plant.get("site_id") or SITES[rng.choice(3, p=SITE_WEIGHTS)].site_id]
        commissioned = date(2023, 1, 1) + timedelta(days=int(rng.integers(0, span + 1)))
        if "commissioned" in plant:
            commissioned = date.fromisoformat(plant["commissioned"])
        shifts = int(plant.get("shifts") or rng.choice(SHIFT_CHOICES, p=SHIFT_WEIGHTS))
        drawn = float(np.exp(rng.normal(0, sigma)))
        multiplier = float(quantiles[plant["life_quantile"]]) if "life_quantile" in plant else drawn
        propensity = float(rng.uniform(a["opportunity_propensity_min"], a["opportunity_propensity_max"]))
        idle = tuple(date.fromisoformat(d) for d in plant["idle"]) if "idle" in plant else None
        fault = tuple(date.fromisoformat(d) for d in plant["cooling_fault"]) if "cooling_fault" in plant else None

        series = []
        for day in _days(max(START, commissioned), END):
            weekend = day.weekday() >= 5
            active = shifts if not weekend or rng.random() < a["weekend_activity_share"] else 0
            if idle and idle[0] <= day <= idle[1]:
                active = 0
            efc = max(0.0, active * efc_per_shift * (1 + rng.normal(0, a["efc_noise_rel"]))) if active else 0.0
            temp_mean, temp_max = pack_temperature(site, day, active, rng)
            if fault and fault[0] <= day <= fault[1] and active:
                temp_mean += a["planted_cooling_fault_offset_c"]
                temp_max += a["planted_cooling_fault_offset_c"]
            eff, regime = daily_effective_efc(efc, temp_mean, cal)
            if active:
                soc_min = float(np.clip(rng.normal(a["soc_min_mean_pct"] + a["soc_min_opportunity_lift_pct"]
                                                   * propensity, a["soc_min_sd_pct"]), 2, 95))
                opportunity = int(rng.binomial(2 * active, propensity))
                sessions = active + opportunity
            else:
                soc_min, opportunity, sessions = float(a["soc_max_pct"]) - float(rng.uniform(0, 5)), 0, 0
            series.append(dict(day=day, active=active, efc=efc, eff=eff, regime=regime, temp_mean=temp_mean,
                               temp_max=temp_max, soc_min=soc_min, sessions=sessions, opportunity=opportunity,
                               event_hour=int(rng.integers(6, 22)), comm_loss=rng.random() < a["bms_comm_loss_daily_rate"]))

        pre_days = max(0, (START - commissioned).days)
        first_year = series[:365]
        used = pre_days * float(np.mean([s["eff"] for s in first_year])) / (life_ref * multiplier)
        efc_before = pre_days * float(np.mean([s["efc"] for s in first_year]))
        tables["profiles"].append({"battery_id": battery_id, "chemistry": chemistry, "rated_kwh": rated_kwh,
                                   "site_id": site.site_id, "commissioned_on": commissioned.isoformat(),
                                   "shifts": shifts, "life_multiplier": multiplier,
                                   "opportunity_propensity": propensity, "efc_before_window": efc_before})
        for s in series:
            used += s["eff"] / (life_ref * multiplier)
            cap = res = None
            if chemistry == "LFP":
                frac = capacity_fraction(used, curve)
                cap, res = 100 * frac, resistance_pct(frac, growth)
            day_iso = s["day"].isoformat()
            tables["daily"].append({
                "battery_id": battery_id, "day": day_iso, "efc": s["efc"], "throughput_kwh": s["efc"] * 2 * rated_kwh,
                "soc_min_pct": s["soc_min"], "soc_max_pct": float(a["soc_max_pct"]), "temp_mean_c": s["temp_mean"],
                "temp_max_c": s["temp_max"], "charge_sessions": s["sessions"], "opportunity_charges": s["opportunity"],
                "capacity_pct": cap, "resistance_pct": res, "temp_regime": s["regime"]})
            stamp = f"{day_iso}T{s['event_hour']:02d}:00:00+00:00"
            if s["temp_max"] > a["over_temperature_threshold_c"]:
                tables["events"].append({"battery_id": battery_id, "observed_at": stamp, "kind": "over_temperature",
                                         "detail": f"Peak pack temperature {s['temp_max']:.1f} °C"})
            if s["active"] and s["soc_min"] < a["deep_discharge_threshold_pct"]:
                tables["events"].append({"battery_id": battery_id, "observed_at": stamp, "kind": "deep_discharge",
                                         "detail": f"Minimum state of charge {s['soc_min']:.0f} %"})
            if s["comm_loss"]:
                tables["events"].append({"battery_id": battery_id, "observed_at": stamp, "kind": "bms_comm_loss",
                                         "detail": "No BMS data received for part of the day"})
            month = (battery_id, s["day"].replace(day=1).isoformat())
            op_hours = 8.0 * s["active"]
            ambient = s["temp_mean"] - a["temp_rise_per_shift_c"] * s["active"]
            _spread(hist, month + ("temperature",), s["temp_mean"], s["temp_mean"], op_hours, TEMP_BINS)
            _spread(hist, month + ("temperature",), ambient, ambient, 24 - op_hours, TEMP_BINS)
            _spread(hist, month + ("soc",), s["soc_min"], a["soc_max_pct"], op_hours, SOC_BINS)
            _spread(hist, month + ("soc",), a["soc_max_pct"], a["soc_max_pct"], 24 - op_hours, SOC_BINS)
    tables["histograms"] = [{"battery_id": b, "month": m, "kind": k, "bin_lower": lo, "bin_upper": hi, "hours": h}
                            for (b, m, k, lo, hi), h in sorted(hist.items())]
    return tables


def _format(value) -> str:
    if value is None:
        return ""
    if isinstance(value, float):
        return f"{value:.4f}"
    return str(value)


def write(tables: dict[str, list[dict]], out_dir: Path, cal_version: str = "") -> dict:
    out_dir.mkdir(parents=True, exist_ok=True)
    hashes, rows = {}, {}
    for key, name in FILES.items():
        buf = io.StringIO()
        writer = csv.writer(buf, lineterminator="\n")
        writer.writerow(COLUMNS[key])
        for row in tables[key]:
            writer.writerow([_format(row[c]) for c in COLUMNS[key]])
        data = buf.getvalue().encode()
        if name.endswith(".gz"):
            packed = io.BytesIO()
            with gzip.GzipFile(fileobj=packed, mode="wb", mtime=0, filename="") as gz:
                gz.write(data)
            data = packed.getvalue()
        (out_dir / name).write_bytes(data)
        hashes[name] = hashlib.sha256(data).hexdigest()
        rows[name] = len(tables[key])
    manifest = {
        "generator_version": GENERATOR_VERSION, "calibration_version": cal_version, "seed": SEED,
        "window": [START.isoformat(), END.isoformat()], "assumptions": GENERATOR_ASSUMPTIONS,
        "planted": {k: v["note"] for k, v in PLANTED.items()}, "rows": rows, "sha256": hashes,
        "digest": hashlib.sha256("".join(hashes[n] for n in sorted(hashes)).encode()).hexdigest(),
    }
    (out_dir / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    return manifest


def main():
    cal = json.loads(CAL.read_text())
    manifest = write(generate(cal), OUT, cal["calibration_version"])
    print(json.dumps({k: manifest[k] for k in ("rows", "digest")}, indent=1))


if __name__ == "__main__":
    main()
