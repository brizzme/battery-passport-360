from datetime import date, datetime, timedelta, timezone
from contextlib import contextmanager
from typing import Literal

import psycopg
from fastapi import APIRouter, HTTPException, Query
from psycopg.rows import dict_row
from pydantic import BaseModel

from .db import connect
from .health import DATA_CUTOFF, HealthSummary, effective_date
from .readiness import Evidence, Result, Status, assess

router = APIRouter(prefix="/api/batteries", tags=["Synthetic fleet"])


class DemoBattery(BaseModel):
    battery_id: str
    category: str
    chemistry: str
    rated_kwh: int
    source_type: Literal["synthetic"]
    source_id: str
    observed_at: datetime
    explanation: str


IDENTITIES = """
SELECT b.battery_id, b.category, b.chemistry, b.rated_kwh,
       s.source_type, s.source_id, s.observed_at, s.explanation
FROM batteries b JOIN source_records s USING (source_id)
WHERE s.source_type = 'synthetic'
"""
FIELDS = """
SELECT f.battery_id, f.field_code, f.value_text, f.evidence_ref, s.*
FROM passport_fields f JOIN source_records s USING(source_id)
WHERE s.source_type = 'synthetic' AND f.battery_id = ANY(%s)
"""


@contextmanager
def fleet_cursor():
    try:
        with connect() as conn, conn.cursor(row_factory=dict_row) as cursor:
            yield cursor
    except psycopg.Error as exc:
        raise HTTPException(503, "Fleet database unavailable") from exc


def identity(cursor, battery_id):
    cursor.execute(IDENTITIES + " AND b.battery_id = %s", (battery_id,))
    row = cursor.fetchone()
    if row is None:
        raise HTTPException(404, "Synthetic battery not found")
    return DemoBattery.model_validate(row)


def fields_for(cursor, ids):
    cursor.execute(FIELDS, (ids,))
    grouped = {}
    for row in cursor:
        grouped.setdefault(row["battery_id"], {})[row["field_code"]] = Evidence.model_validate(row)
    return grouped


class FleetPage(BaseModel):
    items: list[DemoBattery]
    total: int
    page: int
    page_size: int = 12
    as_of: date


@router.get("")
def search(query: str = Query("", max_length=100), status: Status | None = None,
           page: int = Query(1, ge=1), as_of: date | None = None) -> FleetPage:
    when = as_of or datetime.now(timezone.utc).date()
    with fleet_cursor() as cursor:
        cursor.execute(IDENTITIES + """ AND strpos(lower(b.battery_id || ' ' || b.chemistry), lower(%s)) > 0
                                      ORDER BY b.battery_id""", (query.strip(),))
        rows = [DemoBattery.model_validate(row) for row in cursor]
        if status:
            fields = fields_for(cursor, [row.battery_id for row in rows])
            rows = [row for row in rows if any(result.status == status for result in
                    assess(row.category, row.rated_kwh, when, fields.get(row.battery_id, {})))]
    offset = (page - 1) * 12
    return FleetPage(items=rows[offset:offset + 12], total=len(rows), page=page, as_of=when)


@router.get("/{battery_id}")
def battery_detail(battery_id: str) -> DemoBattery:
    with fleet_cursor() as cursor:
        return identity(cursor, battery_id)


class Inspection(BaseModel):
    battery: DemoBattery
    as_of: date
    scenario: str = "Prospective first EU market placement on the assessment date."
    results: list[Result]
    health: HealthSummary | None


@router.get("/{battery_id}/passport-readiness")
def inspect(battery_id: str, as_of: date | None = None) -> Inspection:
    when = as_of or datetime.now(timezone.utc).date()
    with fleet_cursor() as cursor:
        battery = identity(cursor, battery_id)
        fields = fields_for(cursor, [battery_id]).get(battery_id, {})
    return Inspection(battery=battery, as_of=when, health=load_summary(battery_id, effective_date(when, when)),
                      results=assess(battery.category, battery.rated_kwh, when, fields))


def load_summary(battery_id: str, as_of: date) -> HealthSummary:
    from .fleet_health import summary_for
    return summary_for(battery_id, as_of)


def load_history(battery_id: str, start: date, end: date) -> dict:
    from .fleet_health import history_for
    return history_for(battery_id, start, end)


@router.get("/{battery_id}/health-summary")
def get_health_summary(battery_id: str, as_of: date | None = None) -> HealthSummary:
    """Synthetic, calibration-labelled pack health indicators for a qualified reviewer."""
    return load_summary(battery_id, effective_date(as_of, datetime.now(timezone.utc).date()))


@router.get("/{battery_id}/history")
def history(battery_id: str, start: date | None = Query(None, alias="from"),
            end: date | None = Query(None, alias="to")) -> dict:
    end = min(end or DATA_CUTOFF, DATA_CUTOFF)
    start = start or end - timedelta(days=364)
    if start > end or (end - start).days > 365:
        raise HTTPException(422, "Range must run forwards and span at most 366 days")
    return load_history(battery_id, start, end)
