from datetime import date
from pathlib import Path

import pytest

from app.readiness import Evidence, RULES, START, assess, classify

INVALID = Evidence.model_validate_json((Path(__file__).parent / "fixtures/invalid_evidence.json").read_text())
VALID = INVALID.model_copy(update={"value_text": "320"})


@pytest.mark.parametrize("rule,category,kwh,when,evidence,expected", [
    (1, "industrial", 16, START, VALID, "present"),
    (1, "industrial", 16, START, INVALID, "invalid"),
    (1, "industrial", 16, START, None, "missing_evidence"),
    (1, "industrial", 2, START, None, "not_applicable"),
    (1, "industrial", 2.01, START, None, "missing_evidence"),
    (1, "industrial", None, START, VALID, "unknown"),
    (1, "industrial", 16, date(2027,2,17), None, "not_yet_effective"),
    (3, "industrial", 16, START, None, "not_applicable"),
    (3, "ev", 1, START, None, "missing_evidence"),
    (4, "industrial", 16, date(2028,8,17), None, "not_yet_effective"),
    (4, "industrial", 16, date(2028,8,18), None, "unknown"),
])
def test_scope_date_and_evidence(rule, category, kwh, when, evidence, expected):
    assert classify(RULES[rule], category, kwh, when, evidence)[0] == expected


def test_future_evidence_excluded():
    assert assess("industrial", 16, date(2025,12,31), {"rated_ah": VALID})[1].evidence is None
