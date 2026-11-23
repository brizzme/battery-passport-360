"""Database loaders for synthetic pack health and the fleet-level summary route."""
from collections import defaultdict
from datetime import date, datetime, timezone

from fastapi import APIRouter

from .fleet import fields_for, fleet_cursor, identity
from .health import MILESTONE, FleetHealth, HealthSummary, effective_date, fleet_summary, summarize, triage
from .readiness import Status, assess

router = APIRouter(prefix="/api/fleet", tags=["Synthetic fleet health"])

PROFILE = """SELECT p.*, b.chemistry, b.rated_kwh, b.category FROM pack_profiles p JOIN batteries b USING (battery_id)"""
DAILY = """SELECT battery_id, day, efc, throughput_kwh, soc_min_pct, soc_max_pct, temp_mean_c, temp_max_c,
                  charge_sessions, opportunity_charges, capacity_pct, resistance_pct, temp_regime
           FROM pack_daily WHERE day <= %s"""
GAPS = {Status.missing_evidence, Status.invalid}


def _meta(cursor) -> dict:
    cursor.execute("SELECT source_id, generator_version, calibration_version, digest AS seed_digest "
                   "FROM fleet_seed_manifest")
    return cursor.fetchone()


def summary_for(battery_id: str, as_of: date) -> HealthSummary:
    with fleet_cursor() as cursor:
        identity(cursor, battery_id)
        meta = _meta(cursor)
        cursor.execute(PROFILE + " WHERE battery_id = %s", (battery_id,))
        profile = cursor.fetchone()
        cursor.execute(DAILY + " AND battery_id = %s ORDER BY day", (as_of, battery_id))
        daily = cursor.fetchall()
        cursor.execute("SELECT month, kind, bin_lower, bin_upper, hours FROM pack_monthly_histograms "
                       "WHERE battery_id = %s AND month <= %s", (battery_id, as_of))
        hist = cursor.fetchall()
        cursor.execute("SELECT observed_at, kind, detail FROM pack_events WHERE battery_id = %s "
                       "AND observed_at < (%s::date + 1)::timestamp AT TIME ZONE 'UTC' ORDER BY observed_at",
                       (battery_id, as_of))
        events = cursor.fetchall()
    return summarize(profile, daily, hist, events, meta, as_of)


def history_for(battery_id: str, start: date, end: date) -> dict:
    with fleet_cursor() as cursor:
        identity(cursor, battery_id)
        cursor.execute("""SELECT day, capacity_pct, resistance_pct, efc, temp_mean_c, temp_max_c, soc_min_pct, soc_max_pct,
                                 temp_regime FROM pack_daily WHERE battery_id = %s AND day BETWEEN %s AND %s ORDER BY day""",
                       (battery_id, start, end))
        points = cursor.fetchall()
        meta = _meta(cursor)
    return {"battery_id": battery_id, "source_type": "synthetic", "source_id": meta["source_id"],
            "generator_version": meta["generator_version"], "calibration_version": meta["calibration_version"],
            "data_cutoff": effective_date(None, end), "from": start, "to": end, "points": points}


def load_fleet(as_of: date) -> tuple[list[HealthSummary], set[str]]:
    with fleet_cursor() as cursor:
        meta = _meta(cursor)
        cursor.execute(PROFILE + " ORDER BY battery_id")
        profiles = cursor.fetchall()
        cursor.execute(DAILY + " ORDER BY battery_id, day", (as_of,))
        daily = defaultdict(list)
        for row in cursor:
            daily[row["battery_id"]].append(row)
        cursor.execute("SELECT battery_id, observed_at, kind, detail FROM pack_events "
                       "WHERE observed_at < (%s::date + 1)::timestamp AT TIME ZONE 'UTC'", (as_of,))
        events = defaultdict(list)
        for row in cursor:
            events[row.pop("battery_id")].append(row)
        fields = fields_for(cursor, [p["battery_id"] for p in profiles])
    summaries = [summarize(p, daily[p["battery_id"]], [], events[p["battery_id"]], meta, as_of) for p in profiles]
    gaps = {p["battery_id"] for p in profiles
            if any(r.status in GAPS for r in assess(p["category"], p["rated_kwh"], MILESTONE,
                                                    fields.get(p["battery_id"], {})))}
    return summaries, gaps


@router.get("/health-summary")
def fleet_health(as_of: date | None = None) -> FleetHealth:
    when = effective_date(as_of, datetime.now(timezone.utc).date())
    summaries, gaps = load_fleet(when)
    return fleet_summary(summaries, triage(summaries, gaps, when), when)
