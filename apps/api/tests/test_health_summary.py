import json
from datetime import date, timedelta

import pytest

from app.health import DATA_CUTOFF, effective_date, summarize, triage

META = {"source_id": "demo-fleet-v2", "generator_version": "fleet-gen-v1",
        "calibration_version": "fleet-calib-v1-test", "seed_digest": "abc"}
START = date(2026, 10, 22)


def daily(battery_id, chemistry="LFP", days=10, temp=30.0):
    rows = []
    for k in range(days):
        rows.append({"battery_id": battery_id, "day": START + timedelta(days=k), "efc": 1.0, "throughput_kwh": 30.0,
                     "soc_min_pct": 30.0, "soc_max_pct": 100.0, "temp_mean_c": temp, "temp_max_c": temp + 5,
                     "charge_sessions": 2, "opportunity_charges": 1,
                     "capacity_pct": None if chemistry == "lead-acid" else 95.0 - 0.1 * k,
                     "resistance_pct": None if chemistry == "lead-acid" else 101.0 + 0.1 * k,
                     "temp_regime": "extrapolated_below_calibrated_range" if temp < 35 else "calibrated"})
    return rows


def profile(battery_id, chemistry="LFP"):
    return {"battery_id": battery_id, "chemistry": chemistry, "site_id": "SITE-AMB", "commissioned_on": date(2024, 1, 1)}


HIST = [{"month": date(2026, 10, 1), "kind": "temperature", "bin_lower": 20, "bin_upper": 25, "hours": 100.0},
        {"month": date(2026, 10, 1), "kind": "soc", "bin_lower": 20, "bin_upper": 40, "hours": 50.0},
        {"month": date(2026, 11, 1), "kind": "soc", "bin_lower": 20, "bin_upper": 40, "hours": 999.0}]
EVENTS = [{"observed_at": "2026-10-25T10:00:00+00:00", "kind": "over_temperature", "detail": "46.1 degC"},
          {"observed_at": "2026-10-30T10:00:00+00:00", "kind": "deep_discharge", "detail": "8 %"}]


def ind(summary, key):
    return next(i for i in summary.indicators if i.key == key)


def lfp(as_of=date(2026, 10, 31)):
    return summarize(profile("BAT-DEMO-002"), daily("BAT-DEMO-002"), HIST, EVENTS, META, as_of)


def test_capacity_fade_uses_last_row_on_or_before_as_of():
    assert ind(lfp(date(2026, 10, 26)), "capacity_fade_pct").value == pytest.approx(5.4)


def test_no_future_rows_or_events():
    s = lfp(date(2026, 10, 26))
    assert ind(s, "cycle_count_efc").value == pytest.approx(5.0)
    assert [e.kind for e in s.events] == ["over_temperature"]


def test_histograms_only_months_up_to_as_of():
    assert sum(b.hours for b in lfp().soc_histogram) == pytest.approx(50.0)


def test_before_history_is_unknown():
    s = lfp(date(2024, 6, 1))
    for key in ("capacity_fade_pct", "cycle_count_efc", "negative_events"):
        assert ind(s, key).status == "unknown"
        assert ind(s, key).reason == "No synthetic history on or before this date"


def test_effective_date_caps_at_cutoff():
    assert effective_date(date(2027, 2, 18), date(2026, 11, 23)) == DATA_CUTOFF
    assert effective_date(None, date(2026, 11, 23)) == DATA_CUTOFF
    assert effective_date(date(2026, 5, 1), date(2026, 11, 23)) == date(2026, 5, 1)


def test_lead_acid_fade_unknown_never_zero():
    s = summarize(profile("BAT-DEMO-005", "lead-acid"), daily("BAT-DEMO-005", "lead-acid"), HIST, EVENTS, META,
                  date(2026, 10, 31))
    for key in ("capacity_fade_pct", "resistance_increase_pct"):
        assert ind(s, key).status == "unknown" and ind(s, key).value is None
        assert ind(s, key).reason == "No calibration source for lead-acid"


def test_power_and_lifetime_not_modelled():
    s = lfp()
    assert ind(s, "power_fade_pct").status == "unknown"
    assert ind(s, "expected_lifetime").status == "unknown"


def test_passport_mapping_and_labels():
    s = lfp()
    fade = ind(s, "capacity_fade_pct")
    assert fade.passport_field and fade.access_class == "restricted_legitimate_interest"
    assert fade.passport_ref == "Annex XIII 4(a) per Commission guidance v3.2 (non-binding)"
    assert fade.mapping_status.startswith("catalogue-v3.2-1, DP-52")
    assert fade.calibration_refs == ["aalborg-forklift-v2", "hust-lfp-v2"]
    assert fade.labels == ["extrapolated_below_calibrated_range 100%"]
    ops = ind(s, "efc_30d")
    assert not ops.passport_field and ops.access_class == "operational_internal"
    assert all(i.calibration_refs for i in s.indicators)
    assert s.source_type == "synthetic" and s.data_cutoff == DATA_CUTOFF


def test_state_of_health_not_applicable():
    na = lfp().not_applicable
    assert na[0].passport_ref.startswith("Annex XIII 4(b)")
    assert "stationary BESS only" in na[0].reason


def test_triage_flags_with_reasons():
    healthy = lfp()
    worn = summarize(profile("BAT-DEMO-007"), [dict(r, capacity_pct=78.0) for r in daily("BAT-DEMO-007")],
                     HIST, EVENTS * 3, META, date(2026, 10, 31))
    flags = triage([healthy, worn], {"BAT-DEMO-024"}, date(2026, 10, 31))
    rules = {(f.battery_id, f.rule) for f in flags}
    assert ("BAT-DEMO-007", "capacity_below_80") in rules
    assert ("BAT-DEMO-007", "over_temperature_30d") in rules
    assert ("BAT-DEMO-024", "passport_gaps_at_milestone") in rules
    assert ("BAT-DEMO-002", "capacity_below_80") not in rules
    gap = next(f for f in flags if f.rule == "passport_gaps_at_milestone")
    assert gap.reason == "Passport evidence gaps when assessed at 2027-02-18 (prospective placement scenario)"


def test_no_certifying_language():
    text = json.dumps([lfp().model_dump(mode="json")]).lower()
    for word in ("compliant", "certified", "safe to operate", "replace"):
        assert word not in text


def test_capacity_below_measured_curve_is_labelled_extrapolated():
    worn = summarize(profile("BAT-DEMO-007"), [dict(r, capacity_pct=75.0) for r in daily("BAT-DEMO-007")],
                     HIST, [], META, date(2026, 10, 31))
    assert "extrapolated_beyond_measured_curve" in ind(worn, "capacity_fade_pct").labels
    assert "extrapolated_beyond_measured_curve" not in ind(lfp(), "capacity_fade_pct").labels
    flag = next(f for f in triage([worn], set(), date(2026, 10, 31)) if f.rule == "capacity_below_80")
    assert "extrapolated" in flag.reason


def test_lead_acid_cites_no_lfp_calibration():
    s = summarize(profile("BAT-DEMO-005", "lead-acid"), daily("BAT-DEMO-005", "lead-acid"), HIST, EVENTS, META,
                  date(2026, 10, 31))
    for i in s.indicators:
        assert not {"aalborg-forklift-v2", "hust-lfp-v2"} & set(i.calibration_refs), i.key


def test_battery_status_not_asserted():
    status = ind(lfp(), "status")
    assert status.status == "unknown" and status.value is None
    assert status.reason == "Status changes (repurposed, re-used, remanufactured, waste) are not modelled"


def test_in_use_fields_cite_catalogue_rows():
    s = lfp()
    assert "4(d)" in ind(s, "cycle_count_efc").passport_ref and "DP-68" in ind(s, "cycle_count_efc").mapping_status
    assert "4(d)" in ind(s, "negative_events").passport_ref and "DP-69" in ind(s, "negative_events").mapping_status
    assert "part 3" not in json.dumps(s.model_dump(mode="json"))
