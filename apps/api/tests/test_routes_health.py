from datetime import date

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient

from app import fleet, fleet_health
from app.health import FleetHealth, ReviewFlag, fleet_summary, summarize
from app.main import app
from tests.test_health_summary import EVENTS, HIST, META, daily, profile

client = TestClient(app)


@pytest.mark.parametrize("query", ["?from=2026-10-10&to=2026-10-01", "?from=2025-01-01&to=2026-10-31"])
def test_history_rejects_bad_ranges(query, monkeypatch):
    monkeypatch.setattr(fleet, "load_history", lambda *a: pytest.fail("loader must not run"))
    assert client.get("/api/batteries/BAT-DEMO-024/history" + query).status_code == 422


def test_history_default_range_ends_at_cutoff(monkeypatch):
    seen = {}

    def fake(battery_id, start, end):
        seen.update(start=start, end=end)
        return {"battery_id": battery_id, "source_type": "synthetic", "data_cutoff": "2026-10-31", "points": []}
    monkeypatch.setattr(fleet, "load_history", fake)
    assert client.get("/api/batteries/BAT-DEMO-024/history").status_code == 200
    assert seen == {"start": date(2025, 11, 1), "end": date(2026, 10, 31)}


def test_health_summary_404_passthrough(monkeypatch):
    def missing(*_):
        raise HTTPException(404, "Synthetic battery not found")
    monkeypatch.setattr(fleet, "load_summary", missing)
    assert client.get("/api/batteries/BAT-DEMO-999/health-summary").status_code == 404


def test_health_summary_caps_as_of(monkeypatch):
    calls = []
    monkeypatch.setattr(fleet, "load_summary", lambda b, d: calls.append(d) or summarize(
        profile(b), daily(b), HIST, EVENTS, META, d))
    body = client.get("/api/batteries/BAT-DEMO-024/health-summary?as_of=2027-02-18").json()
    assert calls == [date(2026, 10, 31)] and body["data_cutoff"] == "2026-10-31"


def test_fleet_summary_lists_milestone_gaps(monkeypatch):
    summaries = [summarize(profile("BAT-DEMO-024"), daily("BAT-DEMO-024"), HIST, EVENTS, META, date(2026, 10, 31))]
    monkeypatch.setattr(fleet_health, "load_fleet", lambda d: (summaries, {"BAT-DEMO-024"}, {}))
    body = client.get("/api/fleet/health-summary").json()
    assert body["packs"] == 1 and body["source_type"] == "synthetic"
    assert {"battery_id": "BAT-DEMO-024", "rule": "passport_gaps_at_milestone"}.items() <= body["review"][0].items()


def test_fleet_summary_bands():
    s = summarize(profile("BAT-DEMO-002"), daily("BAT-DEMO-002"), HIST, EVENTS, META, date(2026, 10, 31))
    lead = summarize(profile("BAT-DEMO-005", "lead-acid"), daily("BAT-DEMO-005", "lead-acid"), HIST, EVENTS, META,
                     date(2026, 10, 31))
    result = fleet_summary([s, lead], [ReviewFlag(battery_id="x", rule="r", reason="y")], date(2026, 10, 31))
    assert isinstance(result, FleetHealth)
    assert result.capacity_bands == {"95-100": 0, "90-95": 1, "80-90": 0, "below 80": 0, "unknown": 1}
    assert result.events_30d == {"deep_discharge": 2, "over_temperature": 2}


def test_history_payload_reports_fixed_cutoff():
    body = fleet_health.history_payload("BAT-DEMO-024", date(2025, 1, 1), date(2025, 2, 1), [], META)
    assert body["data_cutoff"] == date(2026, 10, 31)


def test_fleet_summary_packs_and_regime_share():
    s = summarize(profile("BAT-DEMO-002"), daily("BAT-DEMO-002"), HIST, EVENTS, META, date(2026, 10, 31))
    lead = summarize(profile("BAT-DEMO-005", "lead-acid"), daily("BAT-DEMO-005", "lead-acid"), HIST, EVENTS, META,
                     date(2026, 10, 31))
    flags = [ReviewFlag(battery_id="BAT-DEMO-002", rule="fade_rate_p90", reason="x")]
    result = fleet_summary([s, lead], flags, date(2026, 10, 31), {"calibrated": 1, "clamped_low": 3})
    packs = {p.battery_id: p for p in result.pack_points}
    assert packs["BAT-DEMO-005"].capacity_pct is None and packs["BAT-DEMO-005"].chemistry == "lead-acid"
    assert packs["BAT-DEMO-002"].capacity_pct == pytest.approx(94.1)
    assert packs["BAT-DEMO-002"].review_rules == ["fade_rate_p90"] and packs["BAT-DEMO-002"].site_id == "SITE-AMB"
    assert result.regime_share == {"calibrated": 0.25, "extrapolated_below_calibrated_range": 0.0,
                                   "clamped_low": 0.75, "clamped_high": 0.0}
    assert set(fleet_summary([s], [], date(2026, 10, 31)).regime_share.values()) == {0.0}


def test_fleet_route_carries_versions(monkeypatch):
    summaries = [summarize(profile("BAT-DEMO-002"), daily("BAT-DEMO-002"), HIST, EVENTS, META, date(2026, 10, 31))]
    monkeypatch.setattr(fleet_health, "load_fleet", lambda d: (summaries, set(), {}))
    body = client.get("/api/fleet/health-summary").json()
    assert body["calibration_version"] == "fleet-calib-v1-test" and body["generator_version"] == "fleet-gen-v1"
