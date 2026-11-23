import hashlib
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
CAL = ROOT / "apps/api/app/artifacts/fleet-calibration.json"
PINS = ROOT / "research/calibration.sha256"


@pytest.fixture(scope="module")
def cal():
    return json.loads(CAL.read_text())


def test_top_level_keys(cal):
    assert {"calibration_version", "generated_at", "sources", "aalborg", "hust", "limitations"} <= cal.keys()


def test_version_tracks_pins(cal):
    digest = hashlib.sha256(PINS.read_bytes()).hexdigest()
    assert cal["calibration_version"] == "fleet-calib-v1-" + digest[:12]


def test_sources_reference_pins(cal):
    pins = PINS.read_text()
    by_id = {s["id"]: s for s in cal["sources"]}
    assert {"hust-lfp-v2", "aalborg-forklift-v2"} == set(by_id)
    assert by_id["hust-lfp-v2"]["sha256"] in pins
    assert by_id["aalborg-forklift-v2"]["manifest_sha256"] == hashlib.sha256(PINS.read_bytes()).hexdigest()
    for s in cal["sources"]:
        assert s["licence"] == "CC BY 4.0" and s["attribution"] and s["accessed"] == "2026-11-23"


def test_aalborg_three_temperatures(cal):
    cells = cal["aalborg"]["cells"]
    assert sorted(c["temp_c"] for c in cells) == [35, 40, 45]
    assert all(c["fade_slope_per_efc"] < 0 and c["rounds_used"] >= 10 for c in cells)
    assert cal["aalborg"]["arrhenius"]["calibrated_range_c"] == [35, 45]
    growth = cal["aalborg"]["resistance_growth_per_fade"]
    assert growth is None or growth > 0


def test_hust_curve_and_counts(cal):
    h = cal["hust"]
    assert len(h["median_curve"]) == 21 and h["median_curve"][0] == pytest.approx(1, abs=0.02)
    assert h["n_cells"] + h["n_excluded"] == 77
    assert h["life_distribution"]["quantiles"]["50"] == pytest.approx(1.0)


def test_limitations_listed(cal):
    assert len(cal["limitations"]) >= 4
