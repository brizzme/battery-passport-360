"""Isolated public-cell research; pack IDs are never accepted here."""
import json
import os
from pathlib import Path

from fastapi import APIRouter, HTTPException

router = APIRouter(prefix="/api/research", tags=["CALCE research cells"])
DATA = Path(os.getenv("RESEARCH_DIR", "/research"))
REPORT = Path(__file__).parent / "artifacts/calce-report.json"


@router.get("/model-report")
def report():
    if not REPORT.is_file():
        return {"status": "model_not_trained"}
    return {"status": "trained", **json.loads(REPORT.read_text())}


@router.get("/cells")
def cells():
    return [{"cell_id": cell, "source_type": "measured_public", "cycles_available": (DATA / (cell+".json")).is_file()}
            for cell in report().get("sources", {})]


@router.get("/cells/{cell_id}/cycles")
def cycles(cell_id: str):
    model = report()
    if cell_id not in model.get("sources", {}):
        raise HTTPException(404, "Unknown research cell")
    path = DATA / (cell_id + ".json")
    if not path.is_file():
        raise HTTPException(503, "Prepare the CALCE archives using research/prepare.py")
    data = json.loads(path.read_text())
    if data["dataset_digest"] != model["dataset_digest"] or data["cell_id"] != cell_id:
        raise HTTPException(503, "Research snapshot mismatch; rerun preparation")
    return data
