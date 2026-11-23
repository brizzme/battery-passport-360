import json
from pathlib import Path

import pytest

from guidance.parse import classify, split_cells

ROOT = Path(__file__).resolve().parents[2]
CAT = json.loads((ROOT / "apps/api/app/artifacts/passport-catalogue.json").read_text())
ROWS = {r["id"]: r for r in CAT["rows"]}


@pytest.mark.parametrize("cell,kind", [
    ("Mandatory", "mandatory"),
    ("Not to be filled/displayed - repetition, same data required under data point 11", "not_filled_repetition"),
    ("Same as data point 11 (capacity); only for rechargeable batteries", "not_filled_repetition"),
    ("Not to be filled/displayed as of February 2027 - format still to be specified in the upcoming implementing act", "not_filled_until_act"),
    ("Not to be filled/displayed", "not_filled"),
    ("Only applicable for some industrial batteries", "some_industrial"),
    ("Only for rechargeable batteries", "rechargeable_only"),
    ("If applicable (if commercial warranty envisaged)", "if_applicable"),
    ("Optional, to be filled if such data is available", "optional"),
    ("Applicable as soon as the battery starts to be used", "in_use"),
    ("Cadmium or lead symbol if applicable", "chemistry_conditional"),
    ("Only for stationary battery energy storage systems and if they have a battery management system", "stationary_only"),
])
def test_classify(cell, kind):
    assert classify(cell) == kind


def test_split_cells_three_columns():
    assert split_cells("Mandatory Mandatory Only applicable for some industrial batteries") == [
        "Mandatory", "Mandatory", "Only applicable for some industrial batteries"]


def test_catalogue_source_pinned():
    pins = (ROOT / "research/guidance.sha256").read_text().split()
    assert CAT["source"]["sha256"] == pins[0] and CAT["version"] == "catalogue-v3.2-1"
    assert CAT["source"]["licence"] == "CC BY 4.0"


def test_row_count_and_ids():
    assert len(CAT["rows"]) == 72 and "DP-38a" in ROWS and "DP-38b" in ROWS and "DP-38" not in ROWS
    assert [r["dp"] for r in CAT["rows"]] == sorted(r["dp"] for r in CAT["rows"])


@pytest.mark.parametrize("rid,name,unit,ref,access,kind", [
    ("DP-11", "The capacity", "Ah", "Annex VI A (6)", "public", "mandatory"),
    ("DP-12", "The chemistry", None, "Annex VI A (7)", "public", "mandatory"),
    ("DP-25", "Rated capacity", "Ah", "Annex XIII 1 (g)", "public", "not_filled_repetition"),
    ("DP-33", "Capacity threshold for exhaustion", "%", "Annex XIII 1 (k)", "public", "not_filled"),
    ("DP-34", "Temperature range the battery can withstand when not in use (reference test)", "°C", "Annex XIII 1 (l)", "public", "mandatory"),
    ("DP-38a", "Internal battery cell resistance", "Ω", "Annex XIII 1 (o)", "public", "mandatory"),
    ("DP-38b", "Internal battery pack resistance", "Ω", "Annex XIII 1 (o)", "public", "mandatory"),
    ("DP-42", "The marking requirements laid down in Article 13(5)", None, "Annex XIII 1 (q)", "public", "chemistry_conditional"),
    ("DP-43", "The EU declaration of conformity referred to in Article 18", None, "Annex XIII 1 (r)", "public", "mandatory"),
    ("DP-51", "Rated capacity", "Ah", "Annex XIII 4 (a)", "restricted_legitimate_interest", "not_filled_repetition"),
    ("DP-52", "Capacity fade", "%", "Annex XIII 4 (a)", "restricted_legitimate_interest", "rechargeable_only"),
    ("DP-62", None, "Ah", "Annex XIII 4 (b)", "restricted_legitimate_interest", "stationary_only"),
    ("DP-68", "The number of charging and discharging cycles", None, "Annex XIII 4 (d)", "restricted_legitimate_interest", "in_use"),
])
def test_known_rows(rid, name, unit, ref, access, kind):
    r = ROWS[rid]
    if name:
        assert r["name"] == name
    assert r["unit"] == unit and r["legal_ref"] == ref and r["access"] == access and r["kind"]["industrial"] == kind


def test_value_types():
    assert ROWS["DP-43"]["value_type"] == "link" and ROWS["DP-11"]["value_type"] == "number"
    assert ROWS["DP-12"]["value_type"] == "code_list" and ROWS["DP-41"]["value_type"] == "yes_no"


def test_ev_column_differs_where_expected():
    assert ROWS["DP-33"]["kind"]["ev"] == "mandatory" and ROWS["DP-61"]["kind"]["industrial"] == "not_filled"


def test_every_row_complete():
    for r in CAT["rows"]:
        assert r["name"] and r["legal_ref"] and r["access"] and set(r["kind"]) == {"ev", "lmt", "industrial"}, r["id"]
