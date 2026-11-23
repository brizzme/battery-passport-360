from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_report_has_models_and_labels():
    body = client.get("/api/research/hust/report").json()
    assert body["source_type"] == "derived" and body["n_cells"] == 77
    assert list(body["models"]) == ["baseline", "voltage_variance", "capacity", "full"]
    assert "cells" not in body and "fleet" not in str(body).lower()


def test_cell_list():
    cells = client.get("/api/research/hust/cells").json()
    assert len(cells) == 77 and {"id", "batch", "life", "capacity", "full"} <= cells[0].keys()


def test_cell_detail_with_curves():
    body = client.get("/api/research/hust/cells/3-5").json()
    assert body["source_type"] == "measured_public" and body["prediction_source_type"] == "derived"
    assert len(body["capacity_ah"]) == len(body["cycles"]) <= 60 and len(body["delta_q_ah"]) == len(body["delta_q_grid_v"])


def test_unknown_cell_404():
    assert client.get("/api/research/hust/cells/99-9").status_code == 404
