import json
from pathlib import Path

import pytest

from generate_fleet import generate, write

ROOT = Path(__file__).resolve().parents[2]
SEED = ROOT / "db/seed/fleet_v2"


@pytest.fixture(scope="module")
def cal():
    return json.loads((ROOT / "apps/api/app/artifacts/fleet-calibration.json").read_text())


@pytest.fixture(scope="module")
def tables(cal):
    return generate(cal)


def test_regeneration_is_byte_identical(tmp_path, cal):
    assert write(generate(cal), tmp_path / "a")["digest"] == write(generate(cal), tmp_path / "b")["digest"]


def test_committed_seed_matches_regeneration(tmp_path, tables):
    assert write(tables, tmp_path)["digest"] == json.loads((SEED / "manifest.json").read_text())["digest"]


def test_chemistry_rule(tables):
    chem = {p["battery_id"]: p["chemistry"] for p in tables["profiles"]}
    assert sum(c == "LFP" for c in chem.values()) == 80
    assert chem["BAT-DEMO-005"] == "lead-acid" and chem["BAT-DEMO-024"] == "LFP"


def test_lead_acid_rows_have_no_capacity(tables):
    lead = [r for r in tables["daily"] if r["battery_id"] in ("BAT-DEMO-005", "BAT-DEMO-010", "BAT-DEMO-100")]
    assert lead and all(r["capacity_pct"] is None and r["resistance_pct"] is None for r in lead)


def test_window_bounds_and_fk(tables):
    ids = {p["battery_id"] for p in tables["profiles"]}
    days = [r["day"] for r in tables["daily"]]
    assert len(ids) == 100 and min(days) >= "2024-11-01" and max(days) == "2026-10-31"
    assert {r["battery_id"] for r in tables["daily"]} == ids
    assert all(e["battery_id"] in ids for e in tables["events"])
    per_pack = {}
    for r in tables["daily"]:
        per_pack[r["battery_id"]] = per_pack.get(r["battery_id"], 0) + 1
    assert max(per_pack.values()) == 730


def test_capacity_monotone_non_increasing_per_pack(tables):
    last = {}
    for r in tables["daily"]:
        if r["capacity_pct"] is None:
            continue
        assert r["capacity_pct"] <= last.get(r["battery_id"], 100.0) + 1e-9
        last[r["battery_id"]] = r["capacity_pct"]


def test_planted_fast_fader_lowest_at_hot_site(tables):
    site = {p["battery_id"]: p["site_id"] for p in tables["profiles"]}
    final = {r["battery_id"]: r["capacity_pct"] for r in tables["daily"]
             if r["day"] == "2026-10-31" and r["capacity_pct"] is not None}
    hot = {b: c for b, c in final.items() if site[b] == "SITE-HOT"}
    assert min(hot, key=hot.get) == "BAT-DEMO-007"


def test_planted_overtemp(tables):
    assert sum(1 for e in tables["events"] if e["battery_id"] == "BAT-DEMO-013" and e["kind"] == "over_temperature"
               and e["observed_at"].startswith("2026-10")) >= 6


def test_planted_idle(tables):
    idle = [r for r in tables["daily"] if r["battery_id"] == "BAT-DEMO-042" and "2026-08-01" <= r["day"] <= "2026-09-30"]
    assert len(idle) == 61 and all(r["efc"] == 0 for r in idle)


def test_regimes_and_histograms(tables):
    assert {r["temp_regime"] for r in tables["daily"]} >= {"calibrated", "extrapolated_below_calibrated_range",
                                                           "clamped_low"}
    kinds = {h["kind"] for h in tables["histograms"]}
    assert kinds == {"temperature", "soc"}
    # every active pack-day contributes 24 h to each histogram kind
    temp_hours = sum(h["hours"] for h in tables["histograms"] if h["kind"] == "temperature")
    assert temp_hours == pytest.approx(24 * len(tables["daily"]), rel=1e-6)
