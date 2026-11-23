"""Complete, valid synthetic evidence for every public industrial-mandatory placement data point (test helper)."""
import csv
from datetime import datetime, timezone
from pathlib import Path

from app.readiness import Evidence

SEED = Path(__file__).resolve().parents[3] / "db/seed/passport_v3/fields.csv"


def full_evidence(battery_id: str = "BAT-DEMO-002") -> dict[str, Evidence]:
    out = {}
    for row in csv.DictReader(SEED.open()):
        if row["battery_id"] == battery_id:
            out[row["field_code"]] = Evidence(value_text=row["value_text"], unit=row["unit"] or None,
                evidence_ref=row["evidence_ref"] or None, source_id="test", source_type="synthetic",
                observed_at=datetime(2026, 1, 1, tzinfo=timezone.utc), explanation="fixture")
    return out
