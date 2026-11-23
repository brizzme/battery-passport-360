"""Passport data readiness from the Commission guidance catalogue (v3.2, non-binding).

Scenario: prospective first EU placement on the assessment date. Every catalogue row is evaluated with a
fixed precedence (design doc, part 3). A gap is missing_evidence or invalid only.
"""
import json
import re
from datetime import date, datetime
from enum import StrEnum
from math import isfinite
from pathlib import Path
from typing import Literal

from pydantic import BaseModel

CATALOGUE = json.loads((Path(__file__).parent / "artifacts/passport-catalogue.json").read_text())
ROWS: list[dict] = CATALOGUE["rows"]
VERSION = CATALOGUE["version"]
GUIDANCE_URL = CATALOGUE["source"]["url"]
OJ = "https://eur-lex.europa.eu/eli/reg/2023/1542/oj/eng"
START = date(2027, 2, 18)          # Article 77(1)
SOURCING_FROM = date(2027, 8, 18)  # responsible sourcing, guidance DP 19 ("required from August 2027")
ART8_FROM = date(2028, 8, 18)      # Article 8(1) earliest application date
IN_USE_REFS = ("Annex XIII 4 (a)", "Annex XIII 4 (c)", "Annex XIII 4 (d)")
CATEGORIES = {"ev", "lmt", "industrial"}
NO_PASSPORT = {"portable", "sli"}
CONTAINS_LEAD_OR_CADMIUM = {"lead-acid", "nicd"}
SI_PREFIX = {"k": 1e3, "M": 1e6, "G": 1e9, "m": 1e-3, "µ": 1e-6}


class Status(StrEnum):
    present = "present"
    missing_evidence = "missing_evidence"
    invalid = "invalid"
    not_applicable = "not_applicable"
    not_yet_effective = "not_yet_effective"
    unknown = "unknown"


GAPS = {Status.missing_evidence, Status.invalid}


class Evidence(BaseModel):
    value_text: str
    unit: str | None = None
    evidence_ref: str | None
    source_id: str
    source_type: Literal["synthetic"]
    observed_at: datetime
    explanation: str


class Result(BaseModel):
    rule_id: str
    dp: int
    field: str
    label: str
    section: str
    guidance_ref: str
    access: str
    effective_from: date | None
    version: str = VERSION
    source_url: str = GUIDANCE_URL
    eurlex_url: str = OJ
    as_of: date
    source_type: Literal["derived"] = "derived"
    status: Status
    reason: str
    evidence: Evidence | None


def _base_unit(unit: str) -> tuple[str, float]:
    u = unit.strip()
    if u == "kg":
        return "g", 1e3
    if len(u) > 1 and u[0] in SI_PREFIX:
        return u[1:], SI_PREFIX[u[0]]
    return u, 1.0


def validate(row: dict, evidence: Evidence) -> tuple[Status, str]:
    text = evidence.value_text.strip()
    kind = row["value_type"]
    if kind == "number":
        try:
            value = float(text)
        except ValueError:
            value = float("nan")
        if not isfinite(value) or value <= 0:
            return Status.invalid, "The entry must be a finite positive number."
        if row["unit"] and row["unit"] not in {"months", "years"}:
            if not evidence.unit:
                return Status.invalid, f"The entry has no unit; the guidance expects {row['unit']} or a multiple."
            if _base_unit(evidence.unit)[0] != _base_unit(row["unit"])[0]:
                return Status.invalid, f"Unit {evidence.unit} does not match {row['unit']} or a multiple of it."
    elif kind == "link":
        if not re.match(r"^https?://[^\s/]+\.[^\s]+", text):
            return Status.invalid, "The entry must be a web link (http or https)."
    elif kind == "yes_no":
        if text.lower() not in {"yes", "no"}:
            return Status.invalid, "The entry must be Yes or No."
    elif kind == "month_year":
        if not re.match(r"^\d{4}-(0[1-9]|1[0-2])$", text):
            return Status.invalid, "The entry must be a month and year (YYYY-MM)."
    elif not text:
        return Status.invalid, "The entry is empty."
    return Status.present, "A synthetic model-sheet entry with a usable value is recorded."


def classify(row: dict, category: str, kwh: float | None, chemistry: str | None, when: date,
             evidence: Evidence | None) -> tuple[Status, str, date | None]:
    if category in NO_PASSPORT:
        return Status.not_applicable, "Article 77 requires a passport for LMT, EV and industrial batteries above 2 kWh only.", None
    if category not in CATEGORIES:
        return Status.unknown, "Battery category is unresolved.", None
    if category == "industrial":
        if kwh is None or not isfinite(kwh) or kwh <= 0:
            return Status.unknown, "Industrial rated energy is unresolved.", None
        if kwh <= 2:
            return Status.not_applicable, "Industrial rated energy is at or below 2 kWh.", None
    kind, text = row["kind"][category], row["guidance"][category]
    if kind == "not_filled_repetition":
        source = re.search(r"data point (\d+)", text)
        return Status.not_applicable, f"Not to be filled: repeats data point {source.group(1) if source else '?'} (guidance).", None
    if kind == "not_filled":
        return Status.not_applicable, "Not to be filled for this battery category (guidance).", None
    if kind == "stationary_only":
        return Status.not_applicable, "Applies only to stationary battery energy storage systems with a BMS.", None
    if kind == "optional":
        return Status.not_applicable, "Optional data point.", None
    if kind == "not_filled_until_act":
        if row["dp"] == 19:
            if when < SOURCING_FROM:
                return Status.not_yet_effective, "Responsible sourcing is required from 18 August 2027 (guidance).", SOURCING_FROM
            return Status.unknown, "Required from 18 August 2027 per guidance; sourcing evidence is not modelled in this prototype.", SOURCING_FROM
        if row["legal_ref"] == "Annex XIII 1 (e)":
            if when < ART8_FROM:
                return Status.not_yet_effective, "Recycled content applies as envisaged by Article 8; earliest 18 August 2028.", ART8_FROM
            return Status.unknown, "Article 8(1) also depends on a delegated act. Applicability needs review.", ART8_FROM
        return Status.not_yet_effective, "Not to be filled as of February 2027; awaits an implementing act or pending amendment (guidance).", None
    if when < START:
        return Status.not_yet_effective, f"The battery passport applies from {START} (Article 77).", START
    if row["legal_ref"] in IN_USE_REFS:
        return (Status.not_yet_effective, "Applies once the battery is in use; first-placement scenario. Synthetic in-use "
                "values are shown in the pack health section (restricted access).", START)
    if kind == "chemistry_conditional":
        if not chemistry:
            return Status.unknown, "Chemistry is unresolved, so the cadmium or lead symbol requirement cannot be decided.", START
        if chemistry.lower() not in CONTAINS_LEAD_OR_CADMIUM:
            return Status.not_applicable, f"Cadmium or lead symbol applies to batteries containing them; chemistry {chemistry}.", START
    if kind in {"some_industrial", "if_applicable"}:
        return Status.unknown, "Applicability depends on battery design; not resolved for these packs.", START
    if row["access"] != "public":
        return Status.unknown, "Restricted-access evidence is not modelled in this prototype.", START
    if not evidence or not evidence.evidence_ref:
        return Status.missing_evidence, "No model-sheet reference supports this data point in the demo record.", START
    status, reason = validate(row, evidence)
    return status, reason, START


def assess(category: str, kwh: float | None, chemistry: str | None, when: date,
           fields: dict[str, Evidence]) -> list[Result]:
    results = []
    for row in ROWS:
        evidence = fields.get(row["id"])
        if evidence and evidence.observed_at.date() > when:
            evidence = None
        status, reason, effective = classify(row, category, kwh, chemistry, when, evidence)
        results.append(Result(rule_id=row["id"], dp=row["dp"], field=row["id"], label=row["name"],
                              section=row["legal_ref"], guidance_ref=f"Guidance v3.2, data point {row['dp']}{row['sub'] or ''}",
                              access=row["access"], effective_from=effective, as_of=when, status=status,
                              reason=reason, evidence=evidence))
    return results


def coverage(results: list[Result]) -> dict[str, int]:
    counts = {s.value: 0 for s in Status}
    for r in results:
        counts[r.status.value] += 1
    return counts
