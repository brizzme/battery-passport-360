"""Synthetic pack health summaries and demo triage. Pure functions; no database access."""
from collections import Counter, defaultdict
from datetime import date, datetime, timedelta
from typing import Literal

import numpy as np
from pydantic import BaseModel

DATA_CUTOFF = date(2026, 10, 31)
MILESTONE = date(2027, 2, 18)
GUIDANCE = "Commission guidance v3.2 (non-binding)"
REF_4A = f"Annex XIII 4(a) per {GUIDANCE}"
REF_4C = f"Annex XIII 4(c) per {GUIDANCE}"
REF_4D = f"Annex XIII 4(d) per {GUIDANCE}"
MAPPING = "provisional — rule integration in part 3"
CALIBRATED = ["aalborg-forklift-v2", "hust-lfp-v2"]
ASSUMED = ["generator_assumption"]
NO_HISTORY = "No synthetic history on or before this date"
NO_LEAD_ACID = "No calibration source for lead-acid"


class Indicator(BaseModel):
    key: str
    label: str
    value: float | int | str | None = None
    unit: str | None = None
    status: Literal["value", "unknown", "not_applicable"] = "value"
    reason: str | None = None
    passport_field: bool
    passport_ref: str | None = None
    access_class: Literal["restricted_legitimate_interest", "operational_internal"]
    mapping_status: str | None = None
    calibration_refs: list[str]
    labels: list[str] = []


class HistogramBin(BaseModel):
    bin_lower: float
    bin_upper: float
    hours: float


class PackEvent(BaseModel):
    observed_at: datetime
    kind: str
    detail: str


class HealthSummary(BaseModel):
    battery_id: str
    as_of: date
    data_cutoff: date = DATA_CUTOFF
    source_type: Literal["synthetic"] = "synthetic"
    source_id: str
    generator_version: str
    calibration_version: str
    site_id: str | None
    chemistry: str
    indicators: list[Indicator]
    temperature_histogram: list[HistogramBin]
    soc_histogram: list[HistogramBin]
    events: list[PackEvent]
    not_applicable: list[Indicator]


class ReviewFlag(BaseModel):
    battery_id: str
    rule: str
    reason: str


class FleetHealth(BaseModel):
    as_of: date
    data_cutoff: date = DATA_CUTOFF
    source_type: Literal["synthetic"] = "synthetic"
    triage_version: str = "triage-v1"
    triage_note: str = ("Suggested for specialist review — demo thresholds, not safety, warranty or "
                        "end-of-life limits.")
    packs: int
    capacity_bands: dict[str, int]
    efc_total: float
    events_30d: dict[str, int]
    review: list[ReviewFlag]


def effective_date(as_of: date | None, today: date) -> date:
    return min(as_of or today, DATA_CUTOFF)


def _passport(key, label, ref, unit=None, refs=CALIBRATED, **kw) -> Indicator:
    return Indicator(key=key, label=label, unit=unit, passport_field=True, passport_ref=ref,
                     access_class="restricted_legitimate_interest", mapping_status=MAPPING,
                     calibration_refs=refs, **kw)


def _operational(key, label, unit=None, refs=ASSUMED, **kw) -> Indicator:
    return Indicator(key=key, label=label, unit=unit, passport_field=False,
                     access_class="operational_internal", calibration_refs=refs, **kw)


def _unknown(reason: str) -> dict:
    return {"status": "unknown", "reason": reason, "value": None}


def _regime_labels(rows: list[dict]) -> list[str]:
    counts = Counter(r["temp_regime"] for r in rows)
    total = sum(counts.values())
    return [f"{regime} {round(100 * n / total)}%" for regime, n in sorted(counts.items())
            if n / total >= 0.01]


def _bins(hist: list[dict], kind: str, as_of: date) -> list[HistogramBin]:
    hours = defaultdict(float)
    for h in hist:
        if h["kind"] == kind and h["month"] <= as_of:
            hours[(float(h["bin_lower"]), float(h["bin_upper"]))] += float(h["hours"])
    return [HistogramBin(bin_lower=lo, bin_upper=hi, hours=round(v, 2)) for (lo, hi), v in sorted(hours.items())]


def _rounded(x: float, digits: int = 2) -> float:
    return round(float(x), digits)


def summarize(profile: dict, daily: list[dict], hist: list[dict], events: list[dict], meta: dict,
              as_of: date) -> HealthSummary:
    rows = sorted((r for r in daily if r["day"] <= as_of), key=lambda r: r["day"])
    past = [PackEvent.model_validate(e) for e in events]
    past = sorted((e for e in past if e.observed_at.date() <= as_of), key=lambda e: e.observed_at)
    lead_acid = profile["chemistry"] == "lead-acid"
    last = rows[-1] if rows else None

    def recent(days):
        return [r for r in rows if r["day"] > as_of - timedelta(days=days)]

    def fade_value(key, transform, missing_reason):
        if not rows:
            return _unknown(NO_HISTORY)
        if lead_acid:
            return _unknown(NO_LEAD_ACID)
        if last[key] is None:
            return _unknown(missing_reason)
        return {"value": _rounded(transform(last[key]))}

    history = {} if rows else _unknown(NO_HISTORY)
    labels = _regime_labels(rows) if rows and not lead_acid else []
    efc_total = float(profile.get("efc_before_window", 0) or 0) + sum(r["efc"] for r in rows)
    r90, r30 = recent(90), recent(30)

    fade_rate = _unknown(NO_HISTORY) if not rows else _unknown(NO_LEAD_ACID) if lead_acid else (
        {"value": _rounded(r90[0]["capacity_pct"] - last["capacity_pct"], 3)} if r90 and r90[0]["capacity_pct"]
        is not None else _unknown("Insufficient recent history"))
    sessions = sum(r["charge_sessions"] for r in r90)

    indicators = [
        _passport("capacity_fade_pct", "Capacity fade", REF_4A, "%", labels=labels,
                  **fade_value("capacity_pct", lambda v: 100 - v, "Capacity not available")),
        _passport("power_fade_pct", "Power fade", REF_4A, "%", refs=["not_modelled"],
                  **_unknown("Power capability is not modelled in this prototype")),
        _passport("resistance_increase_pct", "Internal resistance increase", REF_4A, "%", labels=labels,
                  **fade_value("resistance_pct", lambda v: v - 100,
                               "Resistance growth was not derivable from the calibration data")),
        _passport("expected_lifetime", "Expected lifetime (cycles, years)", REF_4A, refs=["not_modelled"],
                  **_unknown("Not modelled in this prototype")),
        _passport("cycle_count_efc", "Charge-discharge cycles (equivalent full)", REF_4C, "EFC",
                  refs=["aalborg-forklift-v2", "generator_assumption"],
                  **(history or {"value": _rounded(efc_total, 1)})),
        _passport("negative_events", "Negative events recorded", REF_4C, "count", refs=ASSUMED,
                  **(history or {"value": len(past)})),
        _passport("status", "Battery status", REF_4C, refs=ASSUMED, **(history or {"value": "original"})),
        _operational("throughput_kwh_total", "Energy throughput in data window", "kWh",
                     **(history or {"value": _rounded(sum(r["throughput_kwh"] for r in rows), 1)})),
        _operational("efc_30d", "Equivalent full cycles, last 30 days", "EFC",
                     refs=["aalborg-forklift-v2", "generator_assumption"],
                     **(history or {"value": _rounded(sum(r["efc"] for r in r30), 1)})),
        _operational("efc_90d", "Equivalent full cycles, last 90 days", "EFC",
                     refs=["aalborg-forklift-v2", "generator_assumption"],
                     **(history or {"value": _rounded(sum(r["efc"] for r in r90), 1)})),
        _operational("opportunity_charge_share", "Opportunity charges, share of sessions (90 days)", "%",
                     **(history or {"value": _rounded(100 * sum(r["opportunity_charges"] for r in r90) / sessions)
                                    if sessions else 0.0})),
        _operational("temp_mean_30d_c", "Mean pack temperature, last 30 days", "°C",
                     **(history or {"value": _rounded(np.mean([r["temp_mean_c"] for r in r30]), 1)
                                    if r30 else None})),
        _operational("temp_max_30d_c", "Maximum pack temperature, last 30 days", "°C",
                     **(history or {"value": _rounded(max(r["temp_max_c"] for r in r30), 1) if r30 else None})),
        _operational("fade_rate_90d_pct", "Capacity fade, last 90 days", "percentage points",
                     refs=CALIBRATED, labels=labels, **fade_rate),
    ]
    na = [_passport("state_of_health_annex_vii_a", "State of health (Annex VII Part A)",
                    f"Annex XIII 4(b) per {GUIDANCE}", refs=["not_applicable"], status="not_applicable",
                    reason="Annex VII Part A state-of-health applies to stationary BESS only (guidance v3.2)")]
    return HealthSummary(
        battery_id=profile["battery_id"], as_of=as_of, source_id=meta["source_id"],
        generator_version=meta["generator_version"], calibration_version=meta["calibration_version"],
        site_id=profile.get("site_id"), chemistry=profile["chemistry"], indicators=indicators,
        temperature_histogram=_bins(hist, "temperature", as_of), soc_histogram=_bins(hist, "soc", as_of),
        events=past, not_applicable=na)


def _value(summary: HealthSummary, key: str):
    item = next(i for i in summary.indicators if i.key == key)
    return item.value if item.status == "value" else None


def triage(summaries: list[HealthSummary], readiness_gap_ids: set[str], as_of: date) -> list[ReviewFlag]:
    flags = []
    rates = [r for s in summaries if (r := _value(s, "fade_rate_90d_pct")) is not None]
    p90 = float(np.percentile(rates, 90)) if len(rates) >= 10 else None
    window = as_of - timedelta(days=30)
    for s in summaries:
        fade = _value(s, "capacity_fade_pct")
        if fade is not None and fade > 20:
            flags.append(ReviewFlag(battery_id=s.battery_id, rule="capacity_below_80",
                                    reason=f"Synthetic capacity {100 - fade:.1f} % of initial (demo threshold 80 %)"))
        rate = _value(s, "fade_rate_90d_pct")
        if p90 is not None and rate is not None and rate > p90:
            flags.append(ReviewFlag(battery_id=s.battery_id, rule="fade_rate_p90",
                                    reason=f"90-day fade {rate:.2f} pp above fleet 90th percentile {p90:.2f} pp"))
        hot = sum(1 for e in s.events if e.kind == "over_temperature" and e.observed_at.date() > window)
        if hot >= 3:
            flags.append(ReviewFlag(battery_id=s.battery_id, rule="over_temperature_30d",
                                    reason=f"{hot} over-temperature events in the 30 days to {as_of}"))
    for battery_id in sorted(readiness_gap_ids):
        flags.append(ReviewFlag(battery_id=battery_id, rule="passport_gaps_at_milestone",
                                reason=f"Passport evidence gaps when assessed at {MILESTONE} "
                                       "(prospective placement scenario)"))
    return flags
