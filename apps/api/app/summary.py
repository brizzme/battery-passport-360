from datetime import date, datetime, timezone

from fastapi import APIRouter
from fastapi.responses import PlainTextResponse
from pydantic import BaseModel, Field

from .fleet import inspect

router = APIRouter(prefix="/api", tags=["Draft investigation"])


class SummaryRequest(BaseModel):
    battery_id: str = Field(pattern=r"^BAT-DEMO-\d{3}$")
    as_of: date | None = None


@router.post("/inspection-summaries", response_class=PlainTextResponse)
def draft_inspection_summary(request: SummaryRequest) -> PlainTextResponse:
    data = inspect(request.battery_id, request.as_of)
    b = data.battery
    lines = [
        f"# Draft investigation — {b.battery_id}", "",
        f"Synthetic industrial fleet · assessment {data.as_of} · generated {datetime.now(timezone.utc).isoformat()}",
        data.scenario, "",
        f"Identity: {b.chemistry}, {b.rated_kwh} kWh. Source: {b.source_id}, {b.observed_at.isoformat()}. {b.explanation}",
        "", "## Derived passport checks", "",
    ]
    for r in data.results:
        lines.extend([f"### {r.label} — {r.status.value}", r.reason,
                      f"Derived: {r.rule_id} v{r.version}, assessed {r.as_of}, earliest date {r.effective_from}.",
                      f"Reference: Regulation (EU) 2023/1542, {r.section}, {r.source_url}"])
        if r.evidence:
            e = r.evidence
            lines.append(f"Synthetic entry: {e.value_text}. Evidence: {e.evidence_ref or 'unlinked'}. "
                         f"Source: {e.source_id}, {e.observed_at.isoformat()}. {e.explanation}")
        else:
            lines.append("Evidence: no recorded field entry for this date.")
        lines.append("")
    if data.bench:
        bench = data.bench
        lines.extend(["## Simulated bench history", "",
                      f"{bench.vehicle_id}, assigned {bench.assigned_on}.",
                      f"Charge {bench.started_at} to {bench.ended_at}: {bench.energy_kwh} kWh.",
                      f"BMS at {bench.sampled_at}: {bench.soc_pct}% charge, {bench.temperature_c} °C.",
                      f"Service at {bench.serviced_at}: {bench.note}.",
                      f"Synthetic source: {bench.source_id}, {bench.observed_at}. {bench.explanation}", ""])
    lines.extend(["## Expert review", "",
                  "Verify unresolved fields against the original model sheet and confirm the applicable legal dates. "
                  "This draft covers selected evidence checks. A qualified specialist decides any operational or lifecycle action.", ""])
    filename = f"{b.battery_id}-{data.as_of}-draft.md"
    return PlainTextResponse("\n".join(lines), media_type="text/markdown",
                             headers={"Content-Disposition": f'attachment; filename="{filename}"'})
