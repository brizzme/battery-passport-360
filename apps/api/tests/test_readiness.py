from datetime import date, datetime, timezone

import pytest

from app.readiness import ART8_FROM, GAPS, ROWS, SOURCING_FROM, START, Evidence, Status, assess, coverage

ON = START


def ev(value, unit=None, ref="SHEET-TEST", observed="2026-01-01T00:00:00Z"):
    return Evidence(value_text=value, unit=unit, evidence_ref=ref, source_id="test", source_type="synthetic",
                    observed_at=datetime.fromisoformat(observed.replace("Z", "+00:00")), explanation="fixture")


def status(rule_id, category="industrial", kwh=16, chemistry="LFP", when=ON, fields=None):
    return {r.rule_id: r for r in assess(category, kwh, chemistry, when, fields or {})}[rule_id]


def test_every_catalogue_row_evaluated():
    results = assess("industrial", 16, "LFP", ON, {})
    assert len(results) == len(ROWS) == 72 and all(r.source_type == "derived" for r in results)


def test_mandatory_public_present_missing_invalid():
    assert status("DP-11", fields={"DP-11": ev("320", "Ah")}).status == Status.present
    assert status("DP-11").status == Status.missing_evidence
    assert status("DP-11", fields={"DP-11": ev("unit absent")}).status == Status.invalid
    assert status("DP-11", fields={"DP-11": ev("NaN", "Ah")}).status == Status.invalid
    assert status("DP-11", fields={"DP-11": ev("320", "Ah", ref=None)}).status == Status.missing_evidence


@pytest.mark.parametrize("value,unit,expected", [
    ("320", "Ah", Status.present), ("320000", "mAh", Status.present), ("320", "V", Status.invalid),
    ("320", None, Status.invalid), ("-5", "Ah", Status.invalid)])
def test_number_units_and_si_multiples(value, unit, expected):
    assert status("DP-11", fields={"DP-11": ev(value, unit)}).status == expected


def test_weight_si_multiple_of_kg():
    assert status("DP-10", fields={"DP-10": ev("410000", "g")}).status == Status.present


@pytest.mark.parametrize("value,expected", [("https://example.org/doc.pdf", Status.present),
                                            ("see folder", Status.invalid)])
def test_link_validation(value, expected):
    assert status("DP-43", fields={"DP-43": ev(value)}).status == expected


@pytest.mark.parametrize("value,expected", [("Yes", Status.present), ("maybe", Status.invalid)])
def test_yes_no_validation(value, expected):
    assert status("DP-41", fields={"DP-41": ev(value)}).status == expected


@pytest.mark.parametrize("value,expected", [("2025-06", Status.present), ("June", Status.invalid)])
def test_month_year_validation(value, expected):
    assert status("DP-9", fields={"DP-9": ev(value)}).status == expected


def test_before_start_not_yet_effective():
    r = status("DP-11", when=date(2027, 2, 17), fields={"DP-11": ev("320", "Ah")})
    assert r.status == Status.not_yet_effective and r.effective_from == START


def test_repetition_not_applicable_cites_source_row():
    r = status("DP-25")
    assert r.status == Status.not_applicable and "data point 11" in r.reason


def test_ev_only_and_stationary_only_not_applicable():
    assert status("DP-33").status == Status.not_applicable
    assert status("DP-33", category="ev").status == Status.missing_evidence
    assert status("DP-62").status == Status.not_applicable


def test_optional_not_applicable():
    assert status("DP-40").status == Status.not_applicable


def test_in_use_rows_point_to_health_section():
    for rid in ("DP-52", "DP-56", "DP-67", "DP-68", "DP-71"):
        r = status(rid)
        assert r.status == Status.not_yet_effective and "in use" in r.reason


def test_restricted_mandatory_unknown_not_faked():
    r = status("DP-46")
    assert r.status == Status.unknown and "Restricted-access evidence" in r.reason
    assert status("DP-50").access == "restricted_authorities"


def test_some_industrial_unknown():
    assert status("DP-31").status == Status.unknown
    assert status("DP-31", category="ev").status == Status.missing_evidence


def test_cadmium_lead_symbol_by_chemistry():
    assert status("DP-42", chemistry="lead-acid").status == Status.missing_evidence
    assert status("DP-42", chemistry="LFP").status == Status.not_applicable
    assert status("DP-42", chemistry=None).status == Status.unknown


def test_responsible_sourcing_switches_on_2027_08_18():
    assert status("DP-19", when=SOURCING_FROM.replace(day=17)).status == Status.not_yet_effective
    r = status("DP-19", when=SOURCING_FROM)
    assert r.status == Status.unknown and "not modelled" in r.reason


def test_recycled_content_switches_on_2028_08_18():
    assert status("DP-20", when=date(2028, 8, 17)).status == Status.not_yet_effective
    assert status("DP-20", when=ART8_FROM).status == Status.unknown


def test_carbon_footprint_stays_deferred():
    assert status("DP-17", when=date(2031, 1, 1)).status == Status.not_yet_effective


@pytest.mark.parametrize("kwh,expected", [(2, Status.not_applicable), (2.01, Status.missing_evidence),
                                          (None, Status.unknown), (float("nan"), Status.unknown)])
def test_industrial_capacity_scope(kwh, expected):
    assert status("DP-11", kwh=kwh).status == expected


def test_unknown_category_and_portable():
    assert status("DP-11", category="mystery").status == Status.unknown
    assert status("DP-11", category="portable").status == Status.not_applicable


def test_future_evidence_excluded():
    r = status("DP-11", when=date(2027, 3, 1), fields={"DP-11": ev("320", "Ah", observed="2027-04-01T00:00:00Z")})
    assert r.evidence is None and r.status == Status.missing_evidence


def test_coverage_and_gaps():
    results = assess("industrial", 16, "LFP", ON, {})
    counts = coverage(results)
    assert sum(counts.values()) == 72 and GAPS == {Status.missing_evidence, Status.invalid}
    assert counts[Status.missing_evidence.value] > 0


def test_results_cite_guidance_and_regulation():
    r = status("DP-12")
    assert r.guidance_ref == "Guidance v3.2, data point 12" and r.section == "Annex VI A (7)"
    assert r.source_url.startswith("https://single-market-economy.ec.europa.eu/") and "eur-lex" in r.eurlex_url


def test_complete_seed_evidence_has_no_gaps():
    import sys, pathlib; sys.path.insert(0, str(pathlib.Path(__file__).parent))
    from guidance_fixture import full_evidence
    assert not [r.rule_id for r in assess("industrial", 24, "LFP", ON, full_evidence()) if r.status in GAPS]
    assert not [r.rule_id for r in assess("industrial", 20, "lead-acid", ON, full_evidence("BAT-DEMO-005")) if r.status in GAPS]
