from datetime import date, datetime, timezone

from fastapi import APIRouter
from fastapi.responses import PlainTextResponse
from pydantic import BaseModel, Field

from .fleet import inspect
from .readiness import GAPS

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
        "", "## Passport data points (Commission guidance v3.2, non-binding)", "",
        "Counts: " + ", ".join(f"{k.replace('_', ' ')} {v}" for k, v in data.coverage.items()) + ".", "",
    ]
    gaps = [r for r in data.results if r.status in GAPS]
    lines.append("### Gaps (missing or invalid evidence)" if gaps else "### No missing or invalid evidence on this date")
    for r in gaps:
        lines.extend(["", f"**{r.rule_id} {r.label}** — {r.status.value}", r.reason,
                      f"Reference: {r.guidance_ref} ({r.source_url}); Regulation (EU) 2023/1542, {r.section} ({r.eurlex_url})."])
        if r.evidence:
            e = r.evidence
            lines.append(f"Synthetic entry: {e.value_text}{' ' + e.unit if e.unit else ''}. Evidence: {e.evidence_ref or 'unlinked'}. "
                         f"Source: {e.source_id}, {e.observed_at.isoformat()}.")
    unresolved = [r.rule_id for r in data.results if r.status.value == "unknown"]
    lines.extend(["", f"Unresolved, not gaps ({len(unresolved)}): {', '.join(unresolved) or 'none'}. "
                  "Reasons vary per row (restricted access, design-dependent applicability, deferred acts); see the pack page.", ""])
    if data.health:
        h = data.health
        lines.extend(["## Synthetic pack health (simulated, calibrated)", "",
                      f"Data cut-off {h.data_cutoff}; values as of {h.as_of}. Source {h.source_id}, generator "
                      f"{h.generator_version}, calibration {h.calibration_version}.", ""])
        for i in h.indicators:
            shown = f"{i.value} {i.unit or ''}".strip() if i.status == "value" else f"{i.status}: {i.reason}"
            ref = f" ({i.passport_ref}, {i.access_class}, {i.mapping_status})" if i.passport_field else " (operational, not a passport field)"
            extra = f" Temperature regimes: {', '.join(i.labels)}." if i.labels else ""
            lines.append(f"- {i.label}: {shown}{ref}. Basis: {', '.join(i.calibration_refs)}.{extra}")
        for i in h.not_applicable:
            lines.append(f"- {i.label}: not applicable. {i.reason}")
        lines.extend(["", "Calibration data: HUST LFP cells (Ma et al. 2022, Mendeley Data 10.17632/nsc7hnsg4s.2, "
                      "CC BY 4.0) and the Aalborg forklift-profile LFP dataset (Vilsen & Stroe 2024, Mendeley Data "
                      "yz4pttm73n v2, CC BY 4.0). Cell measurements are applied to fictional packs; see "
                      "docs/LIMITATIONS.md.", ""])
    lines.extend(["## Expert review", "",
                  "Verify unresolved fields against the original model sheet and confirm the applicable legal dates. "
                  "This draft covers selected evidence checks. A qualified specialist decides any operational or lifecycle action.", ""])
    filename = f"{b.battery_id}-{data.as_of}-draft.md"
    return PlainTextResponse("\n".join(lines), media_type="text/markdown",
                             headers={"Content-Disposition": f'attachment; filename="{filename}"'})
