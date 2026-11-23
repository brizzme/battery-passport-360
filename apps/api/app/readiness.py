"""Illustrative prospective placement on the assessment date; original OJ text."""
from datetime import date, datetime
from enum import StrEnum
from math import isfinite
from typing import Literal

from pydantic import BaseModel

OJ = "https://eur-lex.europa.eu/eli/reg/2023/1542/oj/eng"
START = date(2027, 2, 18)


class Status(StrEnum):
    present = "present"
    missing_evidence = "missing_evidence"
    invalid = "invalid"
    not_applicable = "not_applicable"
    not_yet_effective = "not_yet_effective"
    unknown = "unknown"


class Evidence(BaseModel):
    value_text: str
    evidence_ref: str | None
    source_id: str
    source_type: Literal["synthetic"]
    observed_at: datetime
    explanation: str


class Rule(BaseModel):
    rule_id: str
    field: str
    label: str
    section: str
    effective_from: date = START
    version: str = "1.0"
    source_url: str = OJ
    access_class: str = "public_model"


RULES = (
    Rule(rule_id="BP-01", field="chemistry", label="Chemistry", section="Annex XIII 1(b)"),
    Rule(rule_id="BP-02", field="rated_ah", label="Rated capacity (Ah)", section="Annex XIII 1(g)"),
    Rule(rule_id="BP-03", field="nominal_v", label="Nominal voltage (V)", section="Annex XIII 1(h)"),
    Rule(rule_id="BP-04", field="ev_threshold", label="EV exhaustion threshold", section="Annex XIII 1(k)"),
    Rule(rule_id="BP-05", field="recycled_share", label="Recycled content documentation",
         section="Annex XIII 1(e), Article 8(1)", effective_from=date(2028, 8, 18)),
)


class Result(Rule):
    as_of: date
    source_type: Literal["derived"] = "derived"
    status: Status
    reason: str
    evidence: Evidence | None


def classify(rule: Rule, category: str, kwh: float | None, when: date, evidence: Evidence | None):
    if category not in {"industrial", "ev", "lmt", "portable", "sli"}:
        return Status.unknown, "Battery category is unresolved."
    if category in {"portable", "sli"} or (rule.field == "ev_threshold" and category != "ev"):
        return Status.not_applicable, "Category is outside this passport field’s scope."
    if category == "industrial":
        if kwh is None or not isfinite(kwh) or kwh <= 0:
            return Status.unknown, "Industrial rated energy is unresolved."
        if kwh <= 2:
            return Status.not_applicable, "Industrial rated energy is at or below 2 kWh."
    if rule.field == "recycled_share" and category == "lmt":
        return Status.unknown, "The LMT recycled-content timetable is outside this rule subset."
    if when < rule.effective_from:
        return Status.not_yet_effective, f"The earliest modeled application date is {rule.effective_from}."
    if rule.field == "recycled_share":
        return Status.unknown, "Article 8(1) also depends on a delegated act and battery characteristics. Applicability needs review."
    if not evidence or not evidence.evidence_ref:
        return Status.missing_evidence, "No model-sheet reference supports this field in the demo record."
    if rule.field in {"rated_ah", "nominal_v"}:
        try:
            number = float(evidence.value_text)
        except ValueError:
            number = float("nan")
        if not isfinite(number) or number <= 0:
            return Status.invalid, "The referenced entry requires a finite positive number in the stated unit."
    elif not evidence.value_text.strip():
        return Status.invalid, "The referenced entry is empty."
    return Status.present, "A synthetic model-sheet reference and a usable field value are recorded."


def assess(category: str, kwh: float | None, when: date, fields: dict[str, Evidence]) -> list[Result]:
    results = []
    for rule in RULES:
        evidence = fields.get(rule.field)
        if evidence and evidence.observed_at.date() > when:
            evidence = None
        status, reason = classify(rule, category, kwh, when, evidence)
        results.append(Result(**rule.model_dump(), as_of=when, evidence=evidence, status=status, reason=reason))
    return results
