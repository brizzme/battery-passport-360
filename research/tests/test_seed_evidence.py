import csv
from pathlib import Path

from guidance.seed_evidence import evidence_rows, passage_rows, targets

ROOT = Path(__file__).resolve().parents[2]


def test_committed_csv_matches_generator():
    rows = list(csv.reader((ROOT / "db/seed/passport_v3/fields.csv").open()))[1:]
    assert rows == [[str(c) for c in r] for r in evidence_rows()]


def test_targets_are_public_placement_fields():
    ids = {r["id"] for r in targets()}
    assert {"DP-11", "DP-12", "DP-27", "DP-43", "DP-42"} <= ids
    assert not ids & {"DP-25", "DP-33", "DP-46", "DP-52", "DP-68", "DP-31"}


def test_planted_gaps_only():
    by = {}
    for b, f, v, u, ref in evidence_rows():
        by.setdefault(b, {})[f] = (v, u, ref)
    assert by["BAT-DEMO-024"]["DP-12"][2] == "" and by["BAT-DEMO-024"]["DP-11"][:2] == ("unit absent", "")
    assert "DP-43" not in by["BAT-DEMO-031"] and "DP-14" not in by["BAT-DEMO-077"]
    assert by["BAT-DEMO-058"]["DP-27"][0] == "fifty"
    full = {f for f in by["BAT-DEMO-002"]}
    assert all(len(by[b]) >= len(full) - 1 for b in by if b not in {"BAT-DEMO-031", "BAT-DEMO-077"})


def test_lead_acid_has_cadmium_lead_symbol_and_lfp_does_not():
    by = {(b, f) for b, f, *_ in evidence_rows()}
    assert ("BAT-DEMO-005", "DP-42") in by and ("BAT-DEMO-002", "DP-42") not in by


def test_one_passage_per_catalogue_row():
    p = passage_rows()
    assert len(p) == 72 and p[10][0] == "GUID-DP-11" and "Annex VI A (6)" in p[10][6]
